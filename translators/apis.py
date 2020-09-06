# coding=utf-8
# author=UlionTse

"""MIT License

Copyright (c) 2017-2020 UlionTse

Warning: Prohibition of commercial use!
This module is designed to help students and individuals with translation services.
For commercial use, please purchase API services from translation suppliers.

Don't make high frequency requests!
Enterprises provide free services, we should remain grateful, not cause trouble.

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
"""

import re
import sys
import time
import random
from functools import wraps
from typing import Union
from hashlib import md5
from urllib.parse import quote, urlencode, urlparse

import requests
import execjs
from lxml import etree
from loguru import logger


logger.remove()
logger.add(sys.stdout, format='[{time:HH:mm:ss}] <lvl>{message}</lvl>', level='INFO')
logger.opt(colors=True)


class Tse:
    def __init__(self):
        self.author = 'Ulion.Tse'
    
    @staticmethod
    def time_stat(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            t1 = time.time()
            r = func(*args, **kwargs)
            t2 = time.time()
            logger.success('UseTimeSeconds(fn: {}): {}'.format(func.__name__, round((t2 - t1), 1)), style='braces')
            return r
        return wrapper

    @staticmethod
    def if_none(v1,v2):
        return v1 if v1 else v2

    @staticmethod
    def get_headers(host_url, if_use_api=False, if_use_referer=True, if_ajax=True):
        url_path = urlparse(host_url).path
        host_headers = {
            'Referer' if if_use_referer else 'Host': host_url,
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
        if not if_ajax:
            api_headers.pop('X-Requested-With')
            api_headers.update({'Content-Type': 'text/plain'})
        return host_headers if not if_use_api else api_headers

    @staticmethod
    def check_language(from_language, to_language, language_map, output_zh=None, output_auto='auto'):
        from_language = output_auto if from_language in ('auto', 'auto-detect') else from_language
        from_language = output_zh if output_zh and from_language in ('zh','zh-CN','zh-CHS','zh-Hans') else from_language
        to_language = output_zh if output_zh and to_language in ('zh','zh-CN','zh-CHS','zh-Hans') else to_language
        
        if from_language != output_auto and from_language not in language_map:
            raise TranslatorError('Unsupported from_language[{}] in {}.'.format(from_language,list(language_map.keys())))
        elif to_language not in language_map:
            raise TranslatorError('Unsupported to_language[{}] in {}.'.format(to_language,list(language_map.keys())))
        elif from_language != output_auto and to_language not in language_map[from_language]:
            logger.exception('language_map:', language_map)
            raise TranslatorError('Unsupported translation: from [{0}] to [{1}]!'.format(from_language,to_language))
        return from_language,to_language


class TranslatorSeverRegion:
    @property
    def request_server_region_info(self):
        try:
            ip_address = requests.get('http://httpbin.org/ip').json()['origin']
            try:
                data = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=10).json()
                sys.stderr.write(f'Using {data.get("country")} server backend.\n')
                return data
            except requests.exceptions.Timeout:
                data = requests.post(
                    url='http://ip.taobao.com/outGetIpInfo',
                    data={'ip': ip_address, 'accessKey': 'alibaba-inc'}
                ).json().get('data')
                data.update({'countryCode': data.get('country_id')})
                return data

        except requests.exceptions.ConnectionError:
            raise TranslatorError('Unable to connect the Internet.\n')
        except:
            raise TranslatorError('Unable to find server backend.\n')


class TranslatorError(Exception):
    pass


class Google(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = None
        self.cn_host_url = 'https://translate.google.cn'
        self.en_host_url = 'https://translate.google.com'
        self.request_server_region_info = REQUEST_SERVER_REGION_INFO
        self.host_headers = None
        self.language_map = None
        self.api_url = None
        self.query_count = 0
        self.output_zh = 'zh-CN'

    
    def _xr(self, a, b):
        size_b = len(b)
        c = 0
        while c < size_b - 2:
            d = b[c + 2]
            d = ord(d[0]) - 87 if 'a' <= d else int(d)
            d = (a % 2**32) >> d if '+' == b[c + 1] else a << d
            a = a + d & (2**32-1) if '+' == b[c] else a ^ d
            c += 3
        return a


    def _ints(self, text):
        ints = []
        for v in text:
            int_v = ord(v)
            if int_v < 2**16:
                ints.append(int_v)
            else:
                # unicode, emoji
                ints.append(int((int_v - 2**16) / 2**10 + 55296))
                ints.append(int((int_v - 2**16) % 2**10 + 56320))
        return ints


    def acquire(self, text, tkk):
        ints = self._ints(text)
        size = len(ints)
        e = []
        g = 0

        while g < size:
            l = ints[g]
            if l < 2**7: # 128(ascii)
                e.append(l)
            else:
                if l < 2**11: # 2048
                    e.append(l >> 6 | 192)
                else:
                    if (l & 64512) == 55296 and g + 1 < size and ints[g + 1] & 64512 == 56320:
                        g += 1
                        l = 65536 + ((l & 1023) << 10) + (ints[g] & 1023)
                        e.append(l >> 18 | 240)
                        e.append(l >> 12 & 63 | 128)
                    else:
                        e.append(l >> 12 | 224)
                    e.append(l >> 6 & 63 | 128) ##
                e.append(l & 63 | 128)
            g += 1

        b = tkk if tkk != '0' else ''
        d = b.split('.')
        b = int(d[0]) if len(d) > 1 else 0

        a = b
        for value in e:
            a += value
            a = self._xr(a, '+-a^+6')
        a = self._xr(a, '+-3^+b+-f')
        a ^= int(d[1]) if len(d) > 1 else 0
        if a < 0:
            a = (a & (2**31-1)) + 2**31
        a %= int(1E6)
        return '{}.{}'.format(a, a ^ b)

    def get_language_map(self,host_html):
        lang_list_str = re.findall("source_code_name:\[(.*?)\],", host_html)[0]
        lang_list_str = ('['+ lang_list_str + ']').replace('code','"code"').replace('name','"name"')
        lang_list = [x['code'] for x in eval(lang_list_str) if x['code'] != 'auto']
        return {}.fromkeys(lang_list,lang_list)

    @Tse.time_stat
    def google_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,list]:
        """
        https://translate.google.com, https://translate.google.cn.
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param if_use_cn_host: boolean, default None.
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param use_cache: bool, default False.
                :param sleep_seconds: float, >0.05. Best to set it yourself, otherwise there will be surprises.
        :return: str or list
        """

        self.host_url = self.cn_host_url if kwargs.get('if_use_cn_host', None) \
            or self.request_server_region_info.get('countryCode')=='CN' else self.en_host_url
        self.host_headers = self.get_headers(self.cn_host_url, if_use_api=False)
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        use_cache = kwargs.get('use_cache', False)
        sleep_seconds = kwargs.get('sleep_seconds', 0.05 + random.random()/2 + 1e-100*2**self.query_count)
    
        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, proxies=proxies).text
            if self.query_count==0 or not use_cache:
                 self.language_map = self.get_language_map(host_html)
            from_language,to_language = self.check_language(from_language,to_language,self.language_map,output_zh=self.output_zh)
            
            tkk = re.findall("tkk:'(.*?)'", host_html)[0]
            tk = self.acquire(query_text, tkk)
            self.api_url = (self.host_url + '/translate_a/single?client={0}&sl={1}&tl={2}&hl=zh-CN&dt=at&dt=bd&dt=ex'
                + '&dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&ie=UTF-8&oe=UTF-8&source=bh&ssel=0&tsel=0&kc=1&tk='
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
            # {"baidu_id": "A6D0C58DDED7B75B744EDE8A26054BF3:FG=1", "token": "4a1edb47b0528aad49d622db98c7c750"},
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
        js_data = execjs.get().eval(js_txt)
        js_data.update({'gtk': gtk, 'sign': sign})
        return js_data

    @Tse.time_stat
    def baidu_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://fanyi.baidu.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param professional_field: str, default 'common'. Choose from ('common', 'medicine', 'electronics', 'mechanics')
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param sleep_seconds: float, >0.05. Best to set it yourself, otherwise there will be surprises.
        :return: str or dict
        """

        use_domain = kwargs.get('professional_field', 'common')
        assert use_domain in ('common', 'medicine', 'electronics', 'mechanics')
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        # use_cache = kwargs.get('use_cache', False)
        sleep_seconds = kwargs.get('sleep_seconds', 0.05 + random.random()/2 + 1e-100*2**self.query_count)
    
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
                "domain": use_domain,
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
        self.get_old_sign_url = 'http://shared.ydstatic.com/fanyi/newweb/v1.0.29/scripts/newweb/fanyi.min.js'
        self.get_new_sign_url = None
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
            self.get_new_sign_url = re.search(self.get_sign_pattern, host_html).group(0)
            r = ss.get(self.get_new_sign_url, headers=self.host_headers, proxies=proxies)
            r.raise_for_status()
        except:
            r = ss.get(self.get_old_sign_url, headers=self.host_headers, proxies=proxies)
        sign = re.findall('n.md5\("fanyideskweb"\+e\+i\+"(.*?)"\)', r.text)
        return sign[0] if sign and sign != [''] else 'mmbP%A-r6U3Nw(n]BjuEU' #v.1.0.27

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
            'lts': ts,                   # r = "" + (new Date).getTime()
            'salt': salt,               # i = r + parseInt(10 * Math.random(), 10)
            'sign': sign,               # n.md5("fanyideskweb" + e + i + "n%A-rKaT5fb[Gy?;N5@Tj"),e=text
            'bv': bv,                   # n.md5(navigator.appVersion)
            'smartresult': 'dict',
            'client': 'fanyideskweb',
            'doctype': 'json',
            'version': '2.1',
            'keyfrom': 'fanyi.web',
            'action': "FY_BY_DEFAULT", #'FY_BY_REALTlME',  # not time.["FY_BY_REALTlME","FY_BY_DEFAULT"]
            # 'typoResult': 'false'
        }
        return form

    @Tse.time_stat
    def youdao_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        http://fanyi.youdao.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param use_cache: bool, default False.
                :param sleep_seconds: float, >0.05. Best to set it yourself, otherwise there will be surprises.
        :return: str or dict
        """
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        use_cache = kwargs.get('use_cache', False)
        sleep_seconds = kwargs.get('sleep_seconds', 0.05 + random.random()/2 + 1e-100*2**self.query_count)

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, proxies=proxies).text
            if self.query_count==0 or not use_cache:
                 self.language_map = self.get_language_map(host_html)
            sign_key = self.get_sign_key(ss, host_html, proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map,output_zh=self.output_zh)
            from_language, to_language = ('auto','auto') if from_language=='auto' else (from_language,to_language)

            form = self.get_form(str(query_text), from_language, to_language, sign_key)
            r = ss.post(self.api_url, data=form, headers=self.api_headers, proxies=proxies)
            r.raise_for_status()
            data = r.json()
            if data['errorCode'] == 40:
                raise Exception('Invalid translation of `from_language[auto]`, '
                                'please specify parameters of `from_language` or `to_language`.')
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else ''.join(item['tgt'] for result in data['translateResult'] for item in result)


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
        lang_map_str = re.search(pattern='languagePair = {(.*?)}', string=r.text, flags=re.S).group(0) #C=
        return execjs.get().eval(lang_map_str)

    @Tse.time_stat
    def tencent_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        http://fanyi.qq.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param use_cache: bool, default False.
                :param sleep_seconds: float, >0.05. Best to set it yourself, otherwise there will be surprises.
        :return: str or dict
        """
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        use_cache = kwargs.get('use_cache', False)
        sleep_seconds = kwargs.get('sleep_seconds', 0.05 + random.random()/2 + 1e-100*2**self.query_count)

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers,proxies=proxies).text
            if self.query_count==0 or not use_cache:
                 self.language_map = self.get_language_map(ss,self.get_language_url, proxies)
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
        self.get_language_old_url = 'https://translate.alibaba.com/trans/acquireSupportLanguage.do'
        self.get_language_new_url = 'https://translate.alibaba.com/translationopenseviceapp/trans/acquire_supportLanguage.do'
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
        for _ in range(1, 10):
            a = hex(int(random.random() * 1e10))[2:]  # int->str: 16, '0x'
            o += a
        return o[:42]

    def get_language_map(self, ss, biz_type, dmtrack_pageid, proxies):
        def _get_lang(language_url, params=None):
            language_dict = ss.get(language_url, params=params, headers=self.host_headers, proxies=proxies).json()
            language_map = dict(map(lambda x: x, [(x['sourceLuange'], x['targetLanguages']) for x in language_dict['languageMap']]))
            return language_map

        params = {'dmtrack_pageid': dmtrack_pageid, 'biz_type': biz_type}
        try:
            return _get_lang(self.get_language_new_url, params=None)
        except:
            return _get_lang(self.get_language_old_url, params=params)

    @Tse.time_stat
    def alibaba_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://translate.alibaba.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param professional_field: str, default 'message', choose from ("general","message","offer")
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param use_cache: bool, default False.
                :param sleep_seconds: float, >0.05. Best to set it yourself, otherwise there will be surprises.
        :return: str or dict
        """
        use_domain = kwargs.get('professional_field', 'message')
        assert use_domain in ("general","message","offer")
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        use_cache = kwargs.get('use_cache', False)
        sleep_seconds = kwargs.get('sleep_seconds', 0.05 + random.random()/2 + 1e-100*2**self.query_count)
        
        with requests.Session() as ss:
            host_response = ss.get(self.host_url, headers=self.host_headers, proxies=proxies)
            dmtrack_pageid = self.get_dmtrack_pageid(host_response)
            if self.query_count==0 or not use_cache:
                 self.language_map = self.get_language_map(ss, use_domain, dmtrack_pageid, proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            form_data = {
                "srcLanguage": from_language,
                "tgtLanguage": to_language,
                "srcText": str(query_text),
                "viewType": "",
                "source": "",
                "bizType": use_domain,
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
        self.en_host_url = 'https://www.bing.com/Translator'
        self.request_server_region_info = REQUEST_SERVER_REGION_INFO
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
        lang_list = et.xpath('//*[@id="tta_srcsl"]/option/@value') or et.xpath('//*[@id="t_srcAllLang"]/option/@value')
        lang_list.remove(self.output_auto)
        language_map = {}.fromkeys(lang_list,lang_list)
        iid = et.xpath('//*[@id="rich_tta"]/@data-iid')[0] + '.' + str(self.query_count + 1)
        ig = re.findall('IG:"(.*?)"', host_html)[0]
        return {'iid': iid, 'ig': ig, 'language_map': language_map}

    @Tse.time_stat
    def bing_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,list]:
        """
        http://bing.com/Translator, http://cn.bing.com/Translator.
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param if_use_cn_host: boolean, default None.
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param sleep_seconds: float, >0.05. Best to set it yourself, otherwise there will be surprises.
        :return: str or list
        """
        self.host_url = self.cn_host_url if kwargs.get('if_use_cn_host', None) \
            or self.request_server_region_info.get('countryCode')=='CN' else self.en_host_url
        self.api_url = self.host_url.replace('Translator', 'ttranslatev3')
        self.host_headers = self.get_headers(self.host_url, if_use_api=False)
        self.api_headers = self.get_headers(self.host_url, if_use_api=True)
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        # use_cache = kwargs.get('use_cache', False)
        sleep_seconds = kwargs.get('sleep_seconds', 0.05 + random.random()/2 + 1e-100*2**self.query_count)
    
        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, proxies=proxies).text
            self.host_info = self.get_host_info(host_html)

            self.language_map = self.host_info.get('language_map')
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
    
    @Tse.time_stat
    def sogou_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://fanyi.sogou.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param use_cache: bool, default False.
                :param sleep_seconds: float, >0.05. Best to set it yourself, otherwise there will be surprises.
        :return: str or dict
        """
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        use_cache = kwargs.get('use_cache', False)
        sleep_seconds = kwargs.get('sleep_seconds', 0.05 + random.random()/2 + 1e-100*2**self.query_count)
        
        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, proxies=proxies)
            if self.query_count==0 or not use_cache:
                 self.language_map = self.get_language_map(ss,self.get_language_url,proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            self.form_data = self.get_form(query_text, from_language, to_language)
            r = ss.post(self.api_url, headers=self.api_headers, data=self.form_data, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['data']['translate']['dit']


class Deepl(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://www.deepl.com/translator'
        self.api_url = 'https://www2.deepl.com/jsonrpc'
        self.host_headers = self.get_headers(self.host_url, if_use_api=False)
        self.api_headers = self.get_headers(self.host_url, if_use_api=True, if_ajax=False)
        self.api_headers.update({'Content-Type': 'application/json'})
        self.request_id = random.randrange(100,10000) * 10000 + 5
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'zh'

    def get_language_map(self, host_html):
        lang_list = etree.HTML(host_html).xpath('//*[@dl-test="language-selector"]//@value')
        lang_list = set(map(lambda x: x.strip('/').split('/')[0][:2], lang_list)) #[pt-PT, pt-BR] --> pt
        return {}.fromkeys(lang_list, lang_list)

    def split_sentences(self, ss, query_text, from_language, to_language, proxies):
        params = {
            'method': 'LMT_split_into_sentences',
            'id': self.request_id + 2 * self.query_count,
            'jsonrpc': '2.0',
            'params': {
                'texts': [str(query_text)],
                'lang': {
                    'lang_user_selected': from_language,
                    'user_preferred_langs': [to_language, from_language],
                },
            },
        }
        r = ss.post(self.api_url, json=params, headers=self.api_headers, proxies=proxies)
        r.raise_for_status()
        data = r.json()
        return ss, data['result']['splitted_texts'][0]

    def context_sentences_param(self, sentences, from_language, to_language):
        sentences = [''] + sentences + ['']
        param = {
            'method': 'LMT_handle_jobs',
            'id': self.request_id + 2 * self.query_count + 1,
            'jsonrpc':' 2.0',
            'params': {
                'priority': 1,
                'commonJobParams': {},
                'timestamp': int(time.time()*1000),
                'jobs': [
                    {
                        'kind': 'default',
                        'raw_en_sentence': sentences[i],
                        'raw_en_context_before': [sentences[i-1]] if sentences[i-1] else [],
                        'raw_en_context_after': [sentences[i+1]] if sentences[i+1] else [],
                        'preferred_num_beams': 1 if len(sentences)>3 else 4,
                    } for i in range(1,len(sentences)-1)
                ],
                'lang': {
                    'user_preferred_langs': [to_language, from_language],
                    'source_lang_computed': from_language,
                    'target_lang': to_language,
                },
            },
        }
        return param

    @Tse.time_stat
    def deepl_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://www.deepl.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param use_cache: bool, default False.
                :param sleep_seconds: float, >0.05. Best to set it yourself, otherwise there will be surprises.
        :return: str or dict
        """
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        use_cache = kwargs.get('use_cache', False)
        sleep_seconds = kwargs.get('sleep_seconds', 0.05 + random.random()/2 + 1e-100*2**self.query_count)

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, proxies=proxies).text
            if self.query_count==0 or not use_cache:
                 self.language_map = self.get_language_map(host_html)
            from_language, to_language = self.check_language(from_language, to_language, language_map=self.language_map,
                                                             output_zh=self.output_zh, output_auto='auto')
            from_language, to_language = from_language.upper() if from_language != 'auto' else from_language, to_language.upper()
            ss, sentences = self.split_sentences(ss, query_text, from_language, to_language, proxies)
            params = self.context_sentences_param(sentences, from_language, to_language)
            r = ss.post(self.api_url, json=params, headers=self.api_headers, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else ''.join(item['beams'][0]['postprocessed_sentence'] for item in data['result']['translations'])


class Yandex(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://translate.yandex.com'
        self.api_url = 'https://translate.yandex.net/api/v1/tr.json/translate'
        self.detect_language_url = 'https://translate.yandex.net/api/v1/tr.json/detect'
        self.host_headers = self.get_headers(self.host_url, if_use_api=False, if_ajax=False)
        self.api_headers = self.get_headers(self.host_url, if_use_api=True, if_ajax=True)
        self.language_map = None
        self.sid = None
        self.query_count = 0
        self.output_zh = 'zh'

    def get_language_map(self, host_html):
        lang_str = re.findall('TRANSLATOR_LANGS: {(.*?)},', host_html, re.S)
        if not lang_str:
            return {}
        lang_dict = eval('{' + lang_str[0] + '}')
        return {}.fromkeys(lang_dict.keys(), lang_dict.keys())

    def detect_language(self, ss, query_text, sid, proxies):
        params = {'sid': sid, 'srv': 'tr-text', 'text': query_text, 'hint': 'zh,en', 'options': 1,}
        r = ss.get(self.detect_language_url, params=params, headers=self.host_headers, proxies=proxies)
        r.raise_for_status()
        return r.json().get('lang')

    @Tse.time_stat
    def yandex_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://www.deepl.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param proxies: dict, default None.
                :param use_cache: bool, default False.
                :param sleep_seconds: float, >0.05. Best to set it yourself, otherwise there will be surprises.
        :return: str or dict
        """
        is_detail_result = kwargs.get('is_detail_result', False)
        proxies = kwargs.get('proxies', None)
        use_cache = kwargs.get('use_cache', False)
        sleep_seconds = kwargs.get('sleep_seconds', 0.05 + random.random()/2 + 1e-100*2**self.query_count)

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, proxies=proxies).text
            if self.query_count==0 or not use_cache:
                sid_find = re.findall("SID: '(.*?)',", host_html)
                self.sid = sid_find[0] if sid_find else '3d58bd71.5f49c293.93b157d0.74722d74657874'
                self.language_map = self.get_language_map(host_html)

            if self.language_map:
                from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            from_language = self.detect_language(ss, query_text, self.sid, proxies) if from_language=='auto' else from_language
            params = {
                'id': f'{self.sid}-{self.query_count}-0',
                'lang': f'{from_language}-{to_language}',
                'srv': 'tr-text',
                'reason': 'auto',
                'format': 'text'
            }
            form_data = {'text': str(query_text), 'options': 4}
            r = ss.post(self.host_url,params=params,data=form_data,headers=self.api_headers,proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['text'][0]




REQUEST_SERVER_REGION_INFO = TranslatorSeverRegion().request_server_region_info

_alibaba = Alibaba()
alibaba = _alibaba.alibaba_api
_baidu = Baidu()
baidu = _baidu.baidu_api
_bing = Bing()
bing = _bing.bing_api
_deepl = Deepl()
deepl = _deepl.deepl_api
_google = Google()
google = _google.google_api
_sogou = Sogou()
sogou = _sogou.sogou_api
_tencent = Tencent()
tencent = _tencent.tencent_api
_yandex = Yandex()
yandex = _yandex.yandex_api
_youdao = Youdao()
youdao = _youdao.youdao_api


@logger.catch
def test():
    query_text1 = '季姬寂，集鸡，鸡即棘鸡。棘鸡饥叽，季姬及箕稷济鸡。👍👍👍'
    query_text2 = """北国风光，千里冰封，万里雪飘。望长城内外，惟余莽莽；大河上下，顿失滔滔。山舞银蛇，原驰蜡象，欲与天公试比高。
    须晴日，看红装素裹，分外妖娆。江山如此多娇，引无数英雄竞折腰。惜秦皇汉武，略输文采；唐宗宋祖，稍逊风骚。一代天骄，成吉思汗，只识弯弓射大雕。
    俱往矣，数风流人物，还看今朝。
    """
    query_text3 = 'All the past, a number of heroes, but also look at the present.'

    for query_text in [query_text1,query_text2,query_text3]:
        print(alibaba(query_text))
        print(baidu(query_text))
        print(bing(query_text))
        print(deepl(query_text))
        print(google(query_text))
        print(sogou(query_text))
        print(tencent(query_text))
        print(yandex(query_text))
        print(youdao(query_text))

# test()
