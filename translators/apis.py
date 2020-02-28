# coding=utf-8
# author=UlionTse

'''MIT License

Copyright (c) 2020 UlionTse

Warning: Prohibition of Commercial Use!
This module is designed to help students and individuals with translation services.
For commercial use, please purchase API services from translation suppliers.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software. You may obtain a copy of the
License at

    https://github.com/uliontse/translators/blob/master/LICENSE

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import re
import time
import random
import execjs
import requests
from lxml import etree
from hashlib import md5
from urllib.parse import quote, urlencode, urlparse


class Tse:
    def __init__(self):
        self.author = 'Ulion.Tse'
    
    @classmethod
    def timeStat(self, func):
        def wrapper(*args, **kwargs):
            import time
            t1 = time.time()
            r = func(*args, **kwargs)
            t2 = time.time()
            print('UseTimeSeconds(fn: {}): {}'.format(func.__name__, round((t2 - t1), 2)))
            return r
        return wrapper

    def get_headers(self, host_url, if_use_api=False):
        url_path = urlparse(host_url).path
        host_headers = {
            'Referer': host_url,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/55.0.2883.87 Safari/537.36"
        }
        api_headers = {
            'Origin': host_url.split(url_path)[0] if url_path else host_url,
            'Referer': host_url,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/55.0.2883.87 Safari/537.36"
        }
        return host_headers if not if_use_api else api_headers

    def check_language(self, from_language, to_language, language_map, output_zh=None, output_auto='auto'):
        from_language = output_auto if from_language in ('auto', 'auto-detect') else from_language
        from_language = output_zh if output_zh and from_language in ('zh','zh-CN','zh-CHS','zh-Hans') else from_language
        to_language = output_zh if output_zh and to_language in ('zh','zh-CN','zh-CHS','zh-Hans') else to_language
        
        if from_language != output_auto and from_language not in language_map:
            raise KeyError('Unsupported from_language[{}] in {}.'.format(from_language,list(language_map.keys())))
        elif to_language not in language_map:
            raise KeyError('Unsupported to_language[{}] in {}.'.format(to_language,list(language_map.keys())))
        elif from_language != output_auto and to_language not in language_map[from_language]:
            print('language_map:', language_map)
            raise Exception('Unsupported translation: from [{0}] to [{1}]!'.format(from_language,to_language))
        return from_language,to_language


class Google(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = None
        self.cn_host_url = 'https://translate.google.cn'
        self.en_host_url = 'https://translate.google.com'
        self.host_headers = None
        self.language_map = None
        self.api_url = None
        self.query_count = 0
        self.output_zh = 'zh-CN'
 
    # def rshift(self,val, n):
    #     """python port for '>>>'(right shift with padding)
    #     """
    #     return (val % 0x100000000) >> n
    
    def _xr(self, a, b):
        size_b = len(b)
        c = 0
        while c < size_b - 2:
            d = b[c + 2]
            d = ord(d[0]) - 87 if 'a' <= d else int(d)
            # d = google.rshift(self,a, d) if '+' == b[c + 1] else a << d
            d = (a % 0x100000000) >> d if '+' == b[c + 1] else a << d
            a = a + d & 4294967295 if '+' == b[c] else a ^ d
            c += 3
        return a
    
    def acquire(self, text, tkk):
        # tkk = google.get_tkk(self)
        b = tkk if tkk != '0' else ''
        d = b.split('.')
        b = int(d[0]) if len(d) > 1 else 0
        
        # assume e means char code array
        e = []
        g = 0
        size = len(text)
        for i, char in enumerate(text):
            l = ord(char)
            # just append if l is less than 128(ascii: DEL)
            if l < 128:
                e.append(l)
            # append calculated value if l is less than 2048
            else:
                if l < 2048:
                    e.append(l >> 6 | 192)
                else:
                    # append calculated value if l matches special condition
                    if (l & 64512) == 55296 and g + 1 < size and \
                        ord(text[g + 1]) & 64512 == 56320:
                        g += 1
                        l = 65536 + ((l & 1023) << 10) + ord(text[g]) & 1023
                        e.append(l >> 18 | 240)
                        e.append(l >> 12 & 63 | 128)
                    else:
                        e.append(l >> 12 | 224)
                        e.append(l >> 6 & 63 | 128)
                e.append(l & 63 | 128)
        a = b
        for i, value in enumerate(e):
            a += value
            a = self._xr(a, '+-a^+6')
        a = self._xr(a, '+-3^+b+-f')
        a ^= int(d[1]) if len(d) > 1 else 0
        if a < 0:  # pragma: nocover
            a = (a & 2147483647) + 2147483648
        a %= 1000000  # int(1E6)
        return '{}.{}'.format(a, a ^ b)

    def get_language_map(self,host_html):
        lang_list_str = re.findall("source_code_name:\[(.*?)\],", host_html)[0]
        lang_list_str = ('['+ lang_list_str + ']').replace('code','"code"').replace('name','"name"')
        lang_list = [x['code'] for x in eval(lang_list_str) if x['code'] != 'auto']
        return {}.fromkeys(lang_list,lang_list)

    @Tse.timeStat
    def google_api(self, query_text, from_language='auto', to_language='zh', **kwargs):
        '''
        https://translate.google.com, https://translate.google.cn.
        :param query_text: string, must.
        :param from_language: string, default 'auto'.
        :param to_language: string, default 'zh'.
        :param **kwargs:
                :param if_use_cn_host: boolean, default True.
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default 0.05.
        :return: string or list
        '''
        self.host_url = self.cn_host_url if kwargs.get('if_use_cn_host', True) else self.en_host_url
        self.host_headers = self.get_headers(self.cn_host_url, if_use_api=False)
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep', 0.05)
    
        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, proxies=proxies).text
            self.language_map = self.get_language_map(host_html)
            from_language,to_language = self.check_language(from_language,to_language,self.language_map,output_zh=self.output_zh)
            
            tkk = re.findall("tkk:'(.*?)'", host_html)[0]
            tk = self.acquire(query_text, tkk)
            self.api_url = (self.host_url + '/translate_a/single?client={0}&sl={1}&tl={2}&hl=zh-CN&dt=at&dt=bd&dt=ex&dt=ld&dt=md'
                            + '&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&ie=UTF-8&oe=UTF-8&source=bh&ssel=0&tsel=0&kc=1&tk='
                            + str(tk) + '&q=' + quote(query_text)).format('webapp', from_language,to_language)  # [t,webapp]

            r = ss.get(self.api_url, headers=self.host_headers, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else ''.join([item[0] for item in data[0] if isinstance(item[0],str)])


class Baidu(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://fanyi.baidu.com'
        self.api_url = 'https://fanyi.baidu.com/v2transapi'
        self.langdetect_url = 'https://fanyi.baidu.com/langdetect'
        self.get_sign_url = 'https://fanyi-cdn.cdn.bcebos.com/static/translation/pkg/index_bd36cef.js'
        self.get_sign_pattern = 'https://fanyi-cdn.cdn.bcebos.com/static/translation/pkg/index_(.*?).js'
        self.host_headers = self.get_headers(self.host_url, if_use_api=False)
        self.api_headers = self.get_headers(self.host_url, if_use_api=True)
        self.bdtk_pool = [
            {"baidu_id": "F215FBBB82CAF048A24B86785E193475:FG=1", "token": "4e6d918b00ada40933d3e63fd2f2c009"},
            {"baidu_id": "CC1996183B06AC5DD987C80465B33C2D:FG=1", "token": "b670bbc1562d679045dbea34270af2bc"},
            {"baidu_id": "97AD065BAC1491494A8D48510DABE382:FG=1", "token": "9d893922f8ea987de2f2adc81a81fbe7"},
            {"baidu_id": "A6D0C58DDED7B75B744EDE8A26054BF3:FG=1", "token": "4a1edb47b0528aad49d622db98c7c750"},
        ]
        self.bdtk = random.choice(self.bdtk_pool)
        self.new_bdtk = None
        self.host_info = None
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'zh'

    def get_sign_html(self, ss, host_html, proxies):
        try:
            r = ss.get(self.get_sign_url, headers=self.host_headers, proxies=proxies)
            r.raise_for_status()
        except:
            self.get_sign_url = re.search(self.get_sign_pattern,host_html).group(0)
            r = ss.get(self.get_sign_url, headers=self.host_headers, proxies=proxies)
        return r.text

    def get_sign(self, sign_html, ts_text, gtk):
        begin_label = 'define("translation:widget/translate/input/pGrab",function(r,o,t){'
        end_label = 'var i=null;t.exports=e});'
        sign_js = sign_html[sign_html.find(begin_label) + len(begin_label):sign_html.find(end_label)]
        sign_js = sign_js.replace('function e(r)', 'function e(r,i)')
        return execjs.compile(sign_js).call('e', ts_text, gtk)

    def get_host_info(self, host_html, sign_html, ts_text):
        gtk = re.findall("window.gtk = '(.*?)';", host_html)[0]
        sign = self.get_sign(sign_html, ts_text, gtk)
    
        et = etree.HTML(host_html)
        js_txt = et.xpath("/html/body/script[2]/text()")[0][20:-3]
        run_js = execjs.get()
        js_data = run_js.eval(js_txt)
        js_data.update({'gtk': gtk, 'sign': sign})
        return js_data

    @Tse.timeStat
    def baidu_api(self, query_text, from_language='auto', to_language='zh', **kwargs):
        '''
        https://fanyi.baidu.com
        :param query_text: string, must.
        :param from_language: string, default 'auto'.
        :param to_language: string, default 'zh'.
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default 0.05.
        :return: string or dict
        '''
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep', 0.05)
    
        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, proxies=proxies).text
            sign_html = self.get_sign_html(ss, host_html, proxies)
        
            self.host_info = self.get_host_info(host_html, sign_html, query_text)
            self.new_bdtk = {"baidu_id": ss.cookies.get("BAIDUID"), "token": self.host_info.get("token")}
            self.language_map = self.host_info['langMap']
            from_language,to_language = self.check_language(from_language,to_language,self.language_map,output_zh=self.output_zh)
            self.api_headers.update({"cookie": "BAIDUID={};".format(self.bdtk['baidu_id'])})
            res = ss.post(self.langdetect_url, headers=self.api_headers, data={"query": query_text}, proxies=proxies)
            from_language = res.json()['lan'] if from_language == 'auto' else from_language
            
            # param_data = {"from": from_language, "to": to_language}
            form_data = {
                "from": from_language,
                "to": to_language,
                "query": str(query_text),  # from urllib.parse import quote_plus
                "transtype": "translang",  # ["translang","realtime"]
                "simple_means_flag": "3",
                "sign": self.host_info.get('sign'),
                "token": self.bdtk['token'],  # self.host_info.get('token'),
                # "domain": "common",
            }
            r = ss.post(self.api_url, headers=self.api_headers, data=urlencode(form_data).encode('utf-8'),proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        simple_data = data['trans_result']['data'][0]['dst'] if data.get('trans_result') else {'errno': data.get('errno')}
        return data if is_detail_result else simple_data


class Youdao(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'http://fanyi.youdao.com'
        self.api_url = 'http://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'
        self.get_sign_url = 'http://shared.ydstatic.com/fanyi/newweb/v1.0.24/scripts/newweb/fanyi.min.js'
        self.get_sign_pattern = 'http://shared.ydstatic.com/fanyi/newweb/(.*?))/scripts/newweb/fanyi.min.js'
        self.host_headers = self.get_headers(self.host_url, if_use_api=False)
        self.api_headers = self.get_headers(self.host_url, if_use_api=True)
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'zh-CHS'
    
    def get_language_map(self, host_html):
        et = etree.HTML(host_html)
        lang_list = et.xpath('//*[@id="languageSelect"]/li/@data-value')
        lang_list = [(x.split('2')[0], [x.split('2')[1]]) for x in lang_list if '2' in x]
        lang_map = dict(map(lambda x: x, lang_list))
        lang_map.pop('zh-CHS')
        lang_map.update({'zh-CHS': list(lang_map.keys())})
        return lang_map

    def get_sign_key(self, ss, host_html, proxies):
        try:
            r = ss.get(self.get_sign_url, headers=self.host_headers, proxies=proxies)
            r.raise_for_status()
        except:
            self.get_sign_url = re.search(self.get_sign_pattern, host_html).group(0)
            r = ss.get(self.get_sign_url, headers=self.host_headers, proxies=proxies)
        sign = re.findall('n.md5\("fanyideskweb"\+e\+i\+"(.*?)"\)', r.text)
        return sign[0] if sign and sign != [''] else 'Nw(nmmbP%A-r6U3EUn]Aj'

    def get_form(self, query_text, from_language, to_language, sign_key):
        ts = str(int(time.time()))
        salt = str(ts) + str(random.randrange(0, 10))
        sign_text = ''.join(['fanyideskweb', query_text, salt, sign_key])
        sign = md5(sign_text.encode()).hexdigest()
        bv = md5(self.api_headers['User-Agent'][8:].encode()).hexdigest()
        form = {
            'i': str(query_text),
            'from': from_language,
            'to': to_language,
            'ts': ts,                   # r = "" + (new Date).getTime()
            'salt': salt,               # i = r + parseInt(10 * Math.random(), 10)
            'sign': sign,               # n.md5("fanyideskweb" + e + i + "n%A-rKaT5fb[Gy?;N5@Tj"),e=text
            'bv': bv,                   # n.md5(navigator.appVersion)
            'smartresult': 'dict',
            'client': 'fanyideskweb',
            'doctype': 'json',
            'version': '2.1',
            'keyfrom': 'fanyi.web',
            'action': 'FY_BY_REALTlME',  # not time.["FY_BY_REALTlME","FY_BY_DEFAULT"]
            # 'typoResult': 'false'
        }
        return form

    @Tse.timeStat
    def youdao_api(self, query_text, from_language='auto', to_language='zh', **kwargs):
        '''
        http://fanyi.youdao.com
        :param query_text: string, must.
        :param from_language: string, default 'auto'.
        :param to_language: string, default 'zh'.
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default 0.05.
        :return: string or dict
        '''
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep', 0.05)
    
        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, proxies=proxies).text
            self.language_map = self.get_language_map(host_html)
            sign_key = self.get_sign_key(ss, host_html, proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map,output_zh=self.output_zh)
            form = self.get_form(str(query_text), from_language, to_language, sign_key)
            r = ss.post(self.api_url, data=form, headers=self.api_headers, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else ''.join(item['tgt'] for item in data['translateResult'][0])


class Tencent(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://fanyi.qq.com'
        self.api_url = 'https://fanyi.qq.com/api/translate'
        self.get_language_url = 'https://fanyi.qq.com/js/index.js'
        self.host_headers = self.get_headers(self.host_url, if_use_api=False)
        self.api_headers = self.get_headers(self.host_url, if_use_api=True)
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'zh'
 
    def get_language_map(self, ss, language_url, proxies):
        r = ss.get(language_url,headers=self.host_headers,proxies=proxies)
        r.raise_for_status()
        lang_map_str = re.search('C={(.*?)}', r.text).group(0)
        return execjs.get().eval(lang_map_str)

    @Tse.timeStat
    def tencent_api(self, query_text, from_language='auto', to_language='zh', **kwargs):
        '''
        http://fanyi.qq.com
        :param query_text: string, must.
        :param from_language: string, default 'auto'.
        :param to_language: string, default 'zh'.
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default 0.05.
        :return: string or dict
        '''
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep', 0.05)

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers,proxies=proxies).text
            self.language_map = self.get_language_map(ss, self.get_language_url, proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map,output_zh=self.output_zh)
            qtv = re.findall('var qtv = "(.*?)"', host_html)[0]
            qtk = re.findall('var qtk = "(.*?)"', host_html)[0]
            form_data = {
                'source': from_language,
                'target': to_language,
                'sourceText': str(query_text),
                'qtv': qtv,
                'qtk': qtk,
                'sessionUuid': 'translate_uuid' + str(int(time.time()*1000))
            }
            r = ss.post(self.api_url, headers=self.api_headers, data=form_data,proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else ''.join(item['targetText'] for item in data['translate']['records'])


class Alibaba(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://translate.alibaba.com'
        self.api_url = 'https://translate.alibaba.com/translationopenseviceapp/trans/TranslateTextAddAlignment.do'
        self.get_language_url = 'https://translate.alibaba.com/trans/acquireSupportLanguage.do'
        self.host_headers = self.get_headers(self.host_url, if_use_api=False)
        self.api_headers = self.get_headers(self.host_url, if_use_api=True)
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'zh'
    
    def get_dmtrack_pageid(self, host_response):
        try:
            e = re.findall("dmtrack_pageid='(\w+)';", host_response.text)[0]
        except:
            e = ''
        if not e:
            e = host_response.cookies.get_dict().get("cna", "001")
            e = re.sub(pattern='[^a-z\d]', repl='', string=e.lower())[:16]
        else:
            n, r = e[0:16], e[16:26]
            i = hex(int(r, 10))[2:] if re.match('^[\-+]?[0-9]+$', r) else r
            e = n + i
    
        s = int(time.time() * 1000)
        o = ''.join([e, hex(s)[2:]])
        for u in range(1, 10):
            a = hex(int(random.random() * 1e10))[2:]  # int->string: 16, '0x'
            o += a
        return o[:42]

    def get_language_map(self, ss, language_url, biz_type, dmtrack_pageid, proxies):
        params = {'dmtrack_pageid': dmtrack_pageid, 'biz_type': biz_type}
        language_dict = ss.get(language_url, params=params, headers=self.host_headers, proxies=proxies).json()
        language_map = dict(map(lambda x: x, [(x['sourceLuange'], x['targetLanguages']) for x in language_dict['languageMap']]))
        return language_map

    @Tse.timeStat
    def alibaba_api(self, query_text, from_language='auto', to_language='zh', **kwargs):
        '''
        https://translate.alibaba.com
        :param query_text: string, must.
        :param from_language: string, default 'auto'.
        :param to_language: string, default 'zh'.
        :param **kwargs:
                :param biz_type: string, default 'message', choose from ("general","message","offer")
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default 0.05.
        :return: string or dict
        '''
        biz_type = kwargs.get('biz_type', 'message')
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep', 0.05)
        
        with requests.Session() as ss:
            host_response = ss.get(self.host_url, headers=self.host_headers, proxies=proxies)
            dmtrack_pageid = self.get_dmtrack_pageid(host_response)
            self.language_map = self.get_language_map(ss, self.get_language_url, biz_type, dmtrack_pageid, proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            form_data = {
                "srcLanguage": from_language,
                "tgtLanguage": to_language,
                "srcText": str(query_text),
                "viewType": "",
                "source": "",
                "bizType": biz_type,
            }
            i, data, ts_result, params = 0, {}, [], {"dmtrack_pageid":dmtrack_pageid}
            while not ts_result and i < 3:
                res = ss.post(self.api_url,headers=self.api_headers,data=form_data,params=params,proxies=proxies)
                data = res.json()
                ts_result = data.get('listTargetText')
                i += 1
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else ts_result[0]


class Bing(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = None
        self.cn_host_url = 'https://cn.bing.com/Translator'
        self.en_host_url = 'https://bing.com/Translator'
        self.api_url = None
        self.host_headers = None
        self.api_headers = None
        self.host_info = None
        self.language_map = None
        self.query_count = 0
        self.output_auto = 'auto-detect'
        self.output_zh = 'zh-Hans'
    
    def get_host_info(self, host_html):
        et = etree.HTML(host_html)
        lang_list = et.xpath('//*[@id="tta_srcsl"]/option/@value')
        lang_list.remove(self.output_auto)
        language_map = {}.fromkeys(lang_list,lang_list)
        iid = et.xpath('//*[@id="rich_tta"]/@data-iid')[0] + '.' + str(self.query_count + 1)
        ig = re.findall('IG:"(.*?)"', host_html)[0]
        return {'iid': iid, 'ig': ig, 'language_map': language_map}

    @Tse.timeStat
    def bing_api(self, query_text, from_language='auto', to_language='zh', **kwargs):
        '''
        http://bing.com/Translator, http://cn.bing.com/Translator.
        :param query_text: string, must.
        :param from_language: string, default 'auto'.
        :param to_language: string, default 'zh'.
        :param **kwargs:
                :param if_use_cn_host: boolean, default True.
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default 0.05.
        :return: string or list
        '''
        self.host_url = self.cn_host_url if kwargs.get('if_use_cn_host', True) else self.en_host_url
        self.api_url = self.host_url.replace('Translator', 'ttranslatev3')
        self.host_headers = self.get_headers(self.host_url, if_use_api=False)
        self.api_headers = self.get_headers(self.host_url, if_use_api=True)
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep', 0.05)
    
        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, proxies=proxies).text
            self.host_info = self.get_host_info(host_html)

            self.language_map = self.host_info.pop('language_map')
            from_language, to_language = self.check_language(from_language, to_language, self.language_map,
                                                             output_zh=self.output_zh,output_auto=self.output_auto)
            # params = {'isVertical': '1', '': '', 'IG': self.host_info['ig'], 'IID': self.host_info['iid']}
            self.api_url = self.api_url + '?isVertical=1&&IG={}&IID={}'.format(self.host_info['ig'],self.host_info['iid'])
            form_data = {'text': str(query_text), 'fromLang': from_language, 'to': to_language}
            r = ss.post(self.api_url, headers=self.host_headers, data=form_data, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data[0]['translations'][0]['text']


class Sogou(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://fanyi.sogou.com'
        self.api_url = 'https://fanyi.sogou.com/reventondc/translateV2'
        self.get_language_url = 'https://dlweb.sogoucdn.com/translate/pc/static/js/app.7016e0df.js'
        self.host_headers = self.get_headers(self.host_url, if_use_api=False)
        self.api_headers = self.get_headers(self.host_url, if_use_api=True)
        self.language_map = None
        self.form_data = None
        self.query_count = 0
        self.output_zh = 'zh-CHS'
    
    def get_language_map(self, ss, get_language_url, proxies):
        lang_html = ss.get(get_language_url,headers=self.host_headers,proxies=proxies).text
        lang_list_str = re.findall('"ALL":\[(.*?)\]', lang_html)[0]
        lang_list = execjs.get().eval('[' + lang_list_str + ']')
        lang_list = [x['lang'] for x in lang_list]
        return {}.fromkeys(lang_list,lang_list)
    
    def get_form(self, query_text, from_language, to_language):
        uuid = ''
        for i in range(8):
            uuid += hex(int(65536 * (1 + random.random())))[2:][1:]
            if i in range(1,5):
                uuid += '-'
        sign_text = "" + from_language + to_language + query_text + "8511813095152" #window.seccode
        sign = md5(sign_text.encode()).hexdigest()
        form = {
            "from": from_language,
            "to": to_language,
            "text": str(query_text),
            "uuid": uuid, #"ec3ad428-09a8-42a5-97af-608b88697d4f",
            "s": sign, #"c04897e2f7e7e9863ced444357b30356",
            "client": "pc",
            "fr": "browser_pc",
            "pid": "sogou-dict-vr",
            "dict": "true",
            "word_group": "true",
            "second_query": "true",
            "needQc": "1",
        }
        return form
    
    @Tse.timeStat
    def sogou_api(self, query_text, from_language='auto', to_language='zh', **kwargs):
        '''
        https://fanyi.sogou.com
        :param query_text: string, must.
        :param from_language: string, default 'auto'.
        :param to_language: string, default 'zh'.
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default 0.05.
        :return: string or dict
        '''
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep', 0.05)
        
        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, proxies=proxies)
            self.language_map = self.get_language_map(ss, self.get_language_url, proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

            self.form_data = self.get_form(query_text, from_language, to_language)
            r = ss.post(self.api_url, headers=self.api_headers, data=self.form_data, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['data']['translate']['dit']


_alibaba = Alibaba()
alibaba = _alibaba.alibaba_api
_baidu = Baidu()
baidu = _baidu.baidu_api
_bing = Bing()
bing = _bing.bing_api
_google = Google()
google = _google.google_api
_tencent = Tencent()
tencent = _tencent.tencent_api
_youdao = Youdao()
youdao = _youdao.youdao_api
_sogou = Sogou()
sogou = _sogou.sogou_api