# coding=utf-8
# author=UlionTse

"""MIT License

Copyright (c) 2017-2021 UlionTse

Warning: Prohibition of commercial use!
This module is designed to help students and individuals with translation services.
For commercial use, please purchase API services from translation suppliers.

Don't make high frequency requests!
Enterprises provide free services, we should be grateful instead of making trouble.

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

import os
import re
import sys
import time
import json
import base64
import random
import urllib.parse
import hashlib
import functools
import warnings
from typing import Union, Callable

import pathos.multiprocessing
import lxml.etree
import execjs
import requests
import loguru


loguru.logger.remove()
loguru.logger.add(sys.stdout, format='[{time:HH:mm:ss}] <lvl>{message}</lvl>', level='INFO')
loguru.logger.opt(colors=True)


class Tse:
    def __init__(self):
        self.author = 'Ulion.Tse'
    
    @staticmethod
    def time_stat(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            t1 = time.time()
            r = func(*args, **kwargs)
            t2 = time.time()
            loguru.logger.success('CostTime(fn: {}): {}s'.format(func.__name__, round((t2 - t1), 1)), style='braces')
            return r
        return _wrapper

    @staticmethod
    def get_headers(host_url, if_api=False, if_referer_for_host=True, if_ajax_for_api=True, if_json_for_api=False):
        url_path = urllib.parse.urlparse(host_url).path
        user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                     "Chrome/55.0.2883.87 Safari/537.36"
        host_headers = {
            'Referer' if if_referer_for_host else 'Host': host_url,
            "User-Agent": user_agent,
        }
        api_headers = {
            'Origin': host_url.split(url_path)[0] if url_path else host_url,
            'Referer': host_url,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            "User-Agent": user_agent,
        }
        if if_api and not if_ajax_for_api:
            api_headers.pop('X-Requested-With')
            api_headers.update({'Content-Type': 'text/plain'})
        if if_api and if_json_for_api:
            api_headers.update({'Content-Type': 'application/json'})
        return host_headers if not if_api else api_headers

    @staticmethod
    def check_language(from_language, to_language, language_map, output_zh=None, output_auto='auto'):
        from_language = output_auto if from_language in ('auto', 'auto-detect') else from_language
        from_language = output_zh if output_zh and from_language in ('zh','zh-CN','zh-CHS','zh-Hans') else from_language
        to_language = output_zh if output_zh and to_language in ('zh','zh-CN','zh-CHS','zh-Hans') else to_language
        
        if from_language != output_auto and from_language not in language_map:
            raise TranslatorError('Unsupported from_language[{}] in {}.'.format(from_language,sorted(language_map.keys())))
        elif to_language not in language_map:
            raise TranslatorError('Unsupported to_language[{}] in {}.'.format(to_language,sorted(language_map.keys())))
        elif from_language != output_auto and to_language not in language_map[from_language]:
            loguru.logger.exception('language_map:', language_map)
            raise TranslatorError('Unsupported translation: from [{0}] to [{1}]!'.format(from_language,to_language))
        return from_language,to_language

    @staticmethod
    def make_temp_language_map(from_language, to_language):
        warnings.warn('Did not get a complete language map. And do not use `from_language="auto"`.')
        assert from_language != 'auto' and to_language != 'auto' and from_language != to_language
        lang_list = [from_language, to_language]
        return {}.fromkeys(lang_list, lang_list)

    @staticmethod
    def check_query_text(query_text, if_ignore_limit_of_length=False, limit_of_length=5000):
        if not isinstance(query_text, str):
            raise TranslatorError('query_text is not string.')
        query_text = query_text.strip()
        if not query_text:
            return ''
        length = len(query_text)
        if length > limit_of_length and not if_ignore_limit_of_length:
            raise TranslatorError('The length of the text to be translated exceeds the limit.')
        else:
            if length > limit_of_length:
                warnings.warn(f'The translation ignored the excess[above 5000]. Length of `query_text` is {length}.')
                return query_text[:limit_of_length]
        return query_text


class TranslatorSeverRegion:
    @property
    def request_server_region_info(self):
        try:
            ip_address = requests.get('https://httpbin.org/ip').json()['origin']
            try:
                data = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=10).json() # http # limit 45/min.
                country = data.get("country")
                assert country
                sys.stderr.write(f'Using {country} server backend.\n')
                return data
            except requests.exceptions.Timeout:
                data = requests.post(
                    url='https://ip.taobao.com/outGetIpInfo',
                    data={'ip': ip_address, 'accessKey': 'alibaba-inc'}
                ).json().get('data')
                data.update({'countryCode': data.get('country_id')})
                return data

        except requests.exceptions.ConnectionError:
            raise TranslatorError('Unable to connect the Internet.\n')
        except:
            warnings.warn('Unable to find server backend.\n')
            country = input('Please input your server region need to visit:\neg: [England, China, ...]\n')
            sys.stderr.write(f'Using {country} server backend.\n')
            return {'country': country, 'countryCode': 'CN' if country == 'China' else 'EN'}


class TranslatorError(Exception):
    pass


class GoogleV1(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = None
        self.cn_host_url = 'https://translate.google.cn'
        self.en_host_url = 'https://translate.google.com'
        self.request_server_region_info = REQUEST_SERVER_REGION_INFO
        self.host_headers = None
        self.language_map = None
        self.api_url = None
        self.tkk = None
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

    def get_language_map(self, host_html, ss, timeout, proxies):
        while 'source_code_name:' not in host_html:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            time.sleep(0.01)

        lang_list_str = re.compile("source_code_name:\[(.*?)\],").findall(host_html)[0]
        lang_list_str = ('['+ lang_list_str + ']').replace('code','"code"').replace('name','"name"')
        lang_list = [x['code'] for x in eval(lang_list_str) if x['code'] != 'auto']
        return {}.fromkeys(lang_list,lang_list)

    def get_tkk(self, host_html, ss, timeout, proxies):
        while 'tkk:' not in host_html:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            time.sleep(0.01)
        return re.compile("tkk:'(.*?)'").findall(host_html)[0]

    # @Tse.time_stat
    def google_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,list]:
        """
        https://translate.google.com, https://translate.google.cn.
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param if_use_cn_host: boolean, default None.
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or list
        """

        use_cn_condition = kwargs.get('if_use_cn_host', None) or self.request_server_region_info.get('countryCode')=='CN'
        self.host_url = self.cn_host_url if use_cn_condition else self.en_host_url
        self.host_headers = self.get_headers(self.cn_host_url, if_api=False)
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            if not self.language_map:
                 self.language_map = self.get_language_map(host_html, ss, timeout, proxies)
            from_language,to_language = self.check_language(from_language,to_language,self.language_map,output_zh=self.output_zh)

            if not self.tkk:
                self.tkk = self.get_tkk(host_html, ss, timeout, proxies)

            tk = self.acquire(query_text, self.tkk)
            self.api_url = (self.host_url + '/translate_a/single?client={0}&sl={1}&tl={2}&hl=zh-CN&dt=at&dt=bd&dt=ex'
                + '&dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&ie=UTF-8&oe=UTF-8&source=bh&ssel=0&tsel=0&kc=1&tk='
                + str(tk) + '&q=' + urllib.parse.quote(query_text)).format('webapp', from_language,to_language)  # [t,webapp]
            r = ss.get(self.api_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else ''.join([item[0] for item in data[0] if isinstance(item[0],str)])


class GoogleV2(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = None
        self.cn_host_url = 'https://translate.google.cn'
        self.en_host_url = 'https://translate.google.com'
        self.api_url = 'https://translate.google.cn/_/TranslateWebserverUi/data/batchexecute'
        self.request_server_region_info = REQUEST_SERVER_REGION_INFO
        self.host_headers = None
        self.api_headers = None
        self.language_map = None
        self.rpcid = 'MkEWBc'
        self.query_count = 0
        self.output_zh = 'zh-CN'

    def get_rpc(self, query_text, from_language, to_language):
        param = json.dumps([[query_text, from_language, to_language, True], [1]])
        rpc = json.dumps([[[self.rpcid, param, None, "generic"]]])
        return {'f.req': rpc}

    def get_language_map(self, host_html):
        et = lxml.etree.HTML(host_html)
        lang_list = sorted(list(set(et.xpath('//*/@data-language-code'))))
        return {}.fromkeys(lang_list, lang_list)

    def get_info(self, host_html):
        data_str = re.compile(r'window.WIZ_global_data = (.*?);</script>').findall(host_html)[0]
        data = execjs.get().eval(data_str)
        return {'bl': data['cfb2h'], 'f.sid': data['FdrFJe']}

    # @Tse.time_stat
    def google_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, list]:
        """
        https://translate.google.com, https://translate.google.cn.
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param if_use_cn_host: boolean, default None.
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or list
        """

        use_cn_condition = kwargs.get('if_use_cn_host', None) or self.request_server_region_info.get('countryCode')=='CN'
        self.host_url = self.cn_host_url if use_cn_condition else self.en_host_url
        self.host_headers = self.get_headers(self.cn_host_url, if_api=False)
        self.api_headers = self.get_headers(self.cn_host_url, if_api=True, if_referer_for_host=True, if_ajax_for_api=True)
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)
        delete_temp_language_map_label = 0

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, proxies=proxies).text
            if not self.language_map:
                self.language_map = self.get_language_map(host_html)
            if not self.language_map:
                delete_temp_language_map_label += 1
                self.language_map = self.make_temp_language_map(from_language, to_language)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

            rpc_data = self.get_rpc(query_text, from_language, to_language)
            rpc_data = urllib.parse.urlencode(rpc_data)
            r = ss.post(self.api_url, headers=self.api_headers, data=rpc_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            json_data = json.loads(r.text[6:])
            data = json.loads(json_data[0][2])

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else ' '.join([x[0] for x in data[1][0][0][5]])


class Baidu(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://fanyi.baidu.com'
        self.api_url = 'https://fanyi.baidu.com/v2transapi'
        self.langdetect_url = 'https://fanyi.baidu.com/langdetect'
        self.get_sign_url = 'https://fanyi-cdn.cdn.bcebos.com/static/translation/pkg/index_bd36cef.js'
        self.get_sign_pattern = 'https://fanyi-cdn.cdn.bcebos.com/static/translation/pkg/index_(.*?).js'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True)
        self.bdtk_pool = [
            {"baidu_id": "F215FBBB82CAF048A24B86785E193475:FG=1", "token": "4e6d918b00ada40933d3e63fd2f2c009"},
            {"baidu_id": "97AD065BAC1491494A8D48510DABE382:FG=1", "token": "9d893922f8ea987de2f2adc81a81fbe7"},
            {"baidu_id": "A6D0C58DDED7B75B744EDE8A26054BF3:FG=1", "token": "4a1edb47b0528aad49d622db98c7c750"},
        ]
        self.bdtk = random.choice(self.bdtk_pool)
        self.new_bdtk = None
        self.host_info = None
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'zh'

    def get_sign_html(self, ss, host_html, timeout, proxies):
        try:
            if not self.get_sign_url:
                self.get_sign_url = re.compile(self.get_sign_pattern).search(host_html).group(0)
            r = ss.get(self.get_sign_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            r.raise_for_status()
        except:
            r = ss.get(self.get_sign_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
        return r.text

    def get_sign(self, sign_html, ts_text, gtk):
        begin_label = 'define("translation:widget/translate/input/pGrab",function(r,o,t){'
        end_label = 'var i=null;t.exports=e});'
        sign_js = sign_html[sign_html.find(begin_label) + len(begin_label):sign_html.find(end_label)]
        sign_js = sign_js.replace('function e(r)', 'function e(r,i)')
        return execjs.compile(sign_js).call('e', ts_text, gtk)

    def get_host_info(self, host_html, sign_html, ts_text):
        gtk = re.compile("window.gtk = '(.*?)';").findall(host_html)[0]
        sign = self.get_sign(sign_html, ts_text, gtk)
    
        et = lxml.etree.HTML(host_html)
        js_txt = ''
        for i in range(6):
            js_re_list = et.xpath(f"/html/body/script[{i}]/text()")
            if js_re_list:
                if 'langMap' in js_re_list[0]:
                    js_txt = js_re_list[0][20:-111]
                    break

        js_data = execjs.get().eval(js_txt)
        js_data.update({'gtk': gtk, 'sign': sign})
        return js_data

    # @Tse.time_stat
    def baidu_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://fanyi.baidu.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param professional_field: str, default 'common'. Choose from ('common', 'medicine', 'electronics', 'mechanics')
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """

        use_domain = kwargs.get('professional_field', 'common')
        assert use_domain in ('common', 'medicine', 'electronics', 'mechanics')
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)
    
        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, proxies=proxies).text
            sign_html = self.get_sign_html(ss, host_html, timeout, proxies)

            self.host_info = self.get_host_info(host_html, sign_html, query_text)
            self.new_bdtk = {"baidu_id": ss.cookies.get("BAIDUID"), "token": self.host_info.get("token")}
            self.language_map = self.host_info['langMap']
            from_language,to_language = self.check_language(from_language,to_language,self.language_map,output_zh=self.output_zh)
            self.api_headers.update({"cookie": "BAIDUID={};".format(self.bdtk['baidu_id'])})

            if from_language == 'auto':
                res = ss.post(self.langdetect_url, headers=self.api_headers, data={"query": query_text}, timeout=timeout, proxies=proxies)
                from_language = res.json()['lan']
            
            # param_data = {"from": from_language, "to": to_language}
            form_data = {
                "from": from_language,
                "to": to_language,
                "query": query_text,  # from urllib.parse import quote_plus
                "transtype": "translang",  # ["translang","realtime"]
                "simple_means_flag": "3",
                "sign": self.host_info.get('sign'),
                "token": self.bdtk['token'],  # self.host_info.get('token'),
                "domain": use_domain,
            }
            form_data = urllib.parse.urlencode(form_data).encode('utf-8')
            r = ss.post(self.api_url, headers=self.api_headers, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else '\n'.join([x['dst'] for x in data['trans_result']['data']])


class Youdao(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://fanyi.youdao.com'
        self.api_url = 'https://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'
        self.get_old_sign_url = 'https://shared.ydstatic.com/fanyi/newweb/v1.0.29/scripts/newweb/fanyi.min.js'
        self.get_new_sign_url = None
        self.get_sign_pattern = 'https://shared.ydstatic.com/fanyi/newweb/(.*?)/scripts/newweb/fanyi.min.js'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True)
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'zh-CHS'
    
    def get_language_map(self, host_html):
        et = lxml.etree.HTML(host_html)
        lang_list = et.xpath('//*[@id="languageSelect"]/li/@data-value')
        lang_list = [(x.split('2')[0], [x.split('2')[1]]) for x in lang_list if '2' in x]
        lang_map = dict(map(lambda x: x, lang_list))
        lang_map.pop('zh-CHS')
        lang_map.update({'zh-CHS': list(lang_map.keys())})
        return lang_map

    def get_sign_key(self, ss, host_html, timeout, proxies):
        try:
            if not self.get_new_sign_url:
                self.get_new_sign_url = re.compile(self.get_sign_pattern).search(host_html).group(0)
            r = ss.get(self.get_new_sign_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            r.raise_for_status()
        except:
            r = ss.get(self.get_old_sign_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
        sign = re.compile('n.md5\("fanyideskweb"\+e\+i\+"(.*?)"\)').findall(r.text)
        return sign[0] if sign and sign != [''] else "Tbh5E8=q6U3EXe+&L[4c@" #v1.0.31

    def get_form(self, query_text, from_language, to_language, sign_key):
        ts = str(int(time.time()*1000))
        salt = str(ts) + str(random.randrange(0, 10))
        sign_text = ''.join(['fanyideskweb', query_text, salt, sign_key])
        sign = hashlib.md5(sign_text.encode()).hexdigest()
        bv = hashlib.md5(self.api_headers['User-Agent'][8:].encode()).hexdigest()
        form = {
            'i': query_text,
            'from': from_language,
            'to': to_language,
            'lts': ts,                  # r = "" + (new Date).getTime()
            'salt': salt,               # i = r + parseInt(10 * Math.random(), 10)
            'sign': sign,               # n.md5("fanyideskweb" + e + i + "n%A-rKaT5fb[Gy?;N5@Tj"),e=text
            'bv': bv,                   # n.md5(navigator.appVersion)
            'smartresult': 'dict',
            'client': 'fanyideskweb',
            'doctype': 'json',
            'version': '2.1',
            'keyfrom': 'fanyi.web',
            'action': 'FY_BY_DEFAULT',  # not time.["FY_BY_REALTlME","FY_BY_DEFAULT"]
            # 'typoResult': 'false'
        }
        return form

    # @Tse.time_stat
    def youdao_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://fanyi.youdao.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, proxies=proxies).text
            if not self.language_map:
                 self.language_map = self.get_language_map(host_html)
            sign_key = self.get_sign_key(ss, host_html, timeout, proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map,output_zh=self.output_zh)
            from_language, to_language = ('auto','auto') if from_language=='auto' else (from_language,to_language)

            form = self.get_form(query_text, from_language, to_language, sign_key)
            r = ss.post(self.api_url, data=form, headers=self.api_headers, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()
            if data['errorCode'] == 40:
                raise TranslatorError('Invalid translation of `from_language[auto]`, '
                                'please specify parameters of `from_language` or `to_language`.')
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else ' '.join(item['tgt'] if item['tgt'] else '\n' for result in data['translateResult'] for item in result)


class Tencent(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://fanyi.qq.com'
        self.api_url = 'https://fanyi.qq.com/api/translate'
        self.get_language_url = 'https://fanyi.qq.com/js/index.js'
        self.get_qt_url = 'https://fanyi.qq.com/api/reauth12f'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True)
        self.qt_headers = self.get_headers(self.host_url, if_api=True, if_json_for_api=True)
        self.language_map = None
        self.qtv_qtk = None
        self.query_count = 0
        self.output_zh = 'zh'
 
    def get_language_map(self, ss, language_url, timeout, proxies):
        r = ss.get(language_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
        r.raise_for_status()
        lang_map_str = re.compile(pattern='C={(.*?)}|languagePair = {(.*?)}', flags=re.S).search(r.text).group(0) #C=
        return execjs.get().eval(lang_map_str)

    def get_qt(self, ss, timeout, proxies, if_session=False):
        if if_session:
            return ss.post(self.get_qt_url, headers=self.qt_headers, json=self.qtv_qtk, timeout=timeout, proxies=proxies).json()
        return requests.post(self.get_qt_url, headers=self.qt_headers, json=self.qtv_qtk, timeout=timeout, proxies=proxies).json()

    # @Tse.time_stat
    def tencent_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://fanyi.qq.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)

        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            if not self.language_map:
                self.language_map = self.get_language_map(ss, self.get_language_url, timeout, proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            self.qtv_qtk = self.get_qt(ss, timeout, proxies, if_session=False)
            form_data = {
                'source': from_language,
                'target': to_language,
                'sourceText': query_text,
                'qtv': self.qtv_qtk.get('qtv', ''),
                'qtk': self.qtv_qtk.get('qtk', ''),
                'ticket': '',
                'randstr': '',
                'sessionUuid': 'translate_uuid' + str(int(time.time()*1000)),
            }
            r = ss.post(self.api_url, headers=self.api_headers, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else ''.join(item['targetText'] for item in data['translate']['records']) # auto whitespace


class Alibaba(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://translate.alibaba.com'
        self.api_url = 'https://translate.alibaba.com/translationopenseviceapp/trans/TranslateTextAddAlignment.do'
        self.get_language_old_url = 'https://translate.alibaba.com/trans/acquireSupportLanguage.do'
        self.get_language_new_url = 'https://translate.alibaba.com/translationopenseviceapp/trans/acquire_supportLanguage.do'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True)
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'zh'
    
    def get_dmtrack_pageid(self, host_response):
        try:
            e = re.compile("dmtrack_pageid='(\w+)';").findall(host_response.text)[0]
        except:
            e = ''
        if not e:
            e = host_response.cookies.get_dict().get("cna", "001")
            e = re.compile(pattern='[^a-z\d]').sub(repl='', string=e.lower())[:16]
        else:
            n, r = e[0:16], e[16:26]
            i = hex(int(r, 10))[2:] if re.compile('^[\-+]?[0-9]+$').match(r) else r
            e = n + i
    
        s = int(time.time() * 1000)
        o = ''.join([e, hex(s)[2:]])
        for _ in range(1, 10):
            a = hex(int(random.random() * 1e10))[2:]  # int->str: 16, '0x'
            o += a
        return o[:42]

    def get_language_map(self, ss, biz_type, dmtrack_pageid, timeout, proxies):
        def _get_lang(language_url, params=None):
            language_dict = ss.get(language_url, params=params, headers=self.host_headers, timeout=timeout, proxies=proxies).json()
            language_map = dict(map(lambda x: x, [(x['sourceLuange'], x['targetLanguages']) for x in language_dict['languageMap']]))
            return language_map

        params = {'dmtrack_pageid': dmtrack_pageid, 'biz_type': biz_type}
        try:
            return _get_lang(self.get_language_new_url, params=None)
        except:
            return _get_lang(self.get_language_old_url, params=params)

    # @Tse.time_stat
    def alibaba_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://translate.alibaba.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param professional_field: str, default 'message', choose from ("general","message","offer")
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        use_domain = kwargs.get('professional_field', 'message')
        assert use_domain in ("general","message","offer")
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)
        
        with requests.Session() as ss:
            host_response = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            dmtrack_pageid = self.get_dmtrack_pageid(host_response)
            if not self.language_map:
                 self.language_map = self.get_language_map(ss, use_domain, dmtrack_pageid, timeout, proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            form_data = {
                "srcLanguage": from_language,
                "tgtLanguage": to_language,
                "srcText": query_text,
                "viewType": "",
                "source": "",
                "bizType": use_domain,
            }
            params = {"dmtrack_pageid":dmtrack_pageid}
            r = ss.post(self.api_url, headers=self.api_headers, params=params, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['listTargetText'][0]


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
        self.tk = None
        self.first_time = int(time.time())
        self.language_map = None
        self.query_count = 0
        self.output_auto = 'auto-detect'
        self.output_zh = 'zh-Hans'
    
    def get_host_info(self, host_html):
        et = lxml.etree.HTML(host_html)
        lang_list = et.xpath('//*[@id="tta_srcsl"]/option/@value') or et.xpath('//*[@id="t_srcAllLang"]/option/@value')
        lang_list = list(set(lang_list))
        language_map = {}.fromkeys(lang_list,lang_list)
        iid = et.xpath('//*[@id="rich_tta"]/@data-iid')[0] + '.' + str(self.query_count + 1)
        ig = re.compile('IG:"(.*?)"').findall(host_html)[0]
        return {'iid': iid, 'ig': ig, 'language_map': language_map}

    def get_tk(self, host_html):
        result_str = re.compile('var params_RichTranslateHelper = (.*?);').findall(host_html)[0]
        result = execjs.get().eval(result_str)
        return {'key': result[0], 'token': result[1]}


    # @Tse.time_stat
    def bing_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,list]:
        """
        https://bing.com/Translator, https://cn.bing.com/Translator.
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param if_use_cn_host: boolean, default None.
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or list
        """
        use_cn_condition = kwargs.get('if_use_cn_host', None) or self.request_server_region_info.get('countryCode')=='CN'
        self.host_url = self.cn_host_url if use_cn_condition else self.en_host_url
        self.api_url = self.host_url.replace('Translator', 'ttranslatev3')
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True)
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)
    
        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            self.host_info = self.get_host_info(host_html)

            if not self.language_map:
                self.language_map = self.host_info.get('language_map')
            from_language, to_language = self.check_language(from_language, to_language, self.language_map,
                                                             output_zh=self.output_zh,output_auto=self.output_auto)
            # params = {'isVertical': '1', '': '', 'IG': self.host_info['ig'], 'IID': self.host_info['iid']}
            self.api_url = self.api_url + '?isVertical=1&&IG={}&IID={}'.format(self.host_info['ig'],self.host_info['iid'])

            if not self.tk or time.time() - self.first_time > 3500: #3600
                self.tk = self.get_tk(host_html)
            form_data = {
                'text': query_text,
                'fromLang': from_language,
                'to': to_language,
            }
            form_data.update(self.tk)
            r = ss.post(self.api_url, headers=self.host_headers, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data[0]['translations'][0]['text']


class Sogou(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://fanyi.sogou.com'
        # self.old_api_url = 'https://fanyi.sogou.com/reventondc/translateV3'
        self.api_url = 'https://fanyi.sogou.com/api/transpc/text/result'
        self.get_language_url = 'https://dlweb.sogoucdn.com/translate/pc/static/js/app.7016e0df.js'
        # self.get_language_pattern = '//dlweb.sogoucdn.com/translate/pc/static/js/app.(.*?).js'
        # self.get_language_url = None
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True)
        self.language_map = None
        self.form_data = None
        self.query_count = 0
        self.output_zh = 'zh-CHS'
    
    def get_language_map(self, ss, get_language_url, timeout, proxies):
        lang_html = ss.get(get_language_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
        lang_list_str = re.compile('"ALL":\[(.*?)\]').findall(lang_html)[0]
        lang_list = execjs.get().eval('[' + lang_list_str + ']')
        lang_list = [x['lang'] for x in lang_list]
        return {}.fromkeys(lang_list,lang_list)
    
    def get_form(self, query_text, from_language, to_language):
        uuid = ''
        for i in range(8):
            uuid += hex(int(65536 * (1 + random.random())))[2:][1:]
            if i in range(1,5):
                uuid += '-'
        sign_text = "" + from_language + to_language + query_text + '109984457' # window.__INITIAL_STATE__.common.CONFIG.secretCode
        sign = hashlib.md5(sign_text.encode()).hexdigest()
        form = {
            "from": from_language,
            "to": to_language,
            "text": query_text,
            "uuid": uuid,
            "s": sign,
            "client": "pc", #wap
            "fr": "browser_pc", #browser_wap
            "needQc": "1",
        }
        return form
    
    # @Tse.time_stat
    def sogou_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://fanyi.sogou.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)
        
        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            # if not self.get_language_url:
            #     self.get_language_url = 'https:' + re.compile(self.get_language_pattern).search(host_html).group() # TODO
            if not self.language_map:
                self.language_map = self.get_language_map(ss, self.get_language_url, timeout, proxies)

            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            self.form_data = self.get_form(query_text, from_language, to_language)
            r = ss.post(self.api_url, headers=self.api_headers, data=self.form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['data']['translate']['dit']


class Caiyun(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://fanyi.caiyunapp.com'
        self.api_url = 'https://api.interpreter.caiyunai.com/v1/translator'
        # self.old_get_tk_url = 'https://fanyi.caiyunapp.com/static/js/app.1312348c1a3d00422dd1.js'
        self.get_tk_pattern = '/static/js/app.(.*?).js'
        self.get_tk_url = None
        self.get_jwt_url = 'https://api.interpreter.caiyunai.com/v1/user/jwt/generate'
        self.host_headers = self.get_headers(self.host_url, if_api=False, if_referer_for_host=True)
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_ajax_for_api=False, if_json_for_api=True)
        self.language_map = None
        self.browser_pool = [
            'd8bab270cec5dc600525d424be1da0bb',
            '2c011fd3dbab6f3f763c5e7406317fdf',
            '74231a3a95c91c2fa8eba3082a8cc4d6'
        ]
        self.browser_id = random.choice(self.browser_pool)
        self.tk = None
        self.jwt = None
        self.decrypt_dictionary = self.crypt(if_de=True)
        self.query_count = 0
        self.output_zh = 'zh'

    def get_language_map(self, ss, timeout, proxies):
        js_html = ss.get(self.get_tk_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
        # lang_str = re.compile('Ai={(.*?)},').search(js_html).group()[3:-1]
        lang_str = re.compile('lang:{(.*?)},').search(js_html).group()[5:-1]
        lang_list = list(execjs.eval(lang_str).keys())
        return {}.fromkeys(lang_list, lang_list)

    def get_tk(self, ss, timeout, proxies):
        js_html = ss.get(self.get_tk_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
        return re.compile('t.headers\["X-Authorization"\]="(.*?)",').findall(js_html)[0]

    def get_jwt(self, browser_id, api_headers, ss, timeout, proxies):
        data = {"browser_id": browser_id}
        _ = ss.options(self.get_jwt_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
        return ss.post(self.get_jwt_url, headers=api_headers, json=data, timeout=timeout, proxies=proxies).json()['jwt']

    def crypt(self, if_de=True):
        normal_key = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' + '0123456789' + '=.+-_/'
        cipher_key = 'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm' + '0123456789' + '=.+-_/'
        if if_de:
            return {k: v for k, v in zip(cipher_key, normal_key)}
        return {v: k for k, v in zip(cipher_key, normal_key)}

    def encrypt(self, plain_text):
        encrypt_dictionary = self.crypt(if_de=False)
        _cipher_text = base64.b64encode(plain_text.encode()).decode()
        return ''.join(list(map(lambda k: encrypt_dictionary[k], _cipher_text)))

    def decrypt(self, cipher_text):
        _ciphertext = ''.join(list(map(lambda k: self.decrypt_dictionary[k], cipher_text)))
        return base64.b64decode(_ciphertext).decode()

    # @Tse.time_stat
    def caiyun_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str, dict]:
        """
        https://fanyi.caiyunapp.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param professional_field: str, default None, choose from ("medicine","law","machinery")
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        use_domain = kwargs.get('professional_field', None)
        if use_domain:
            assert use_domain in ("medicine", "law", "machinery")
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            if not self.get_tk_url:
                self.get_tk_url = self.host_url + re.compile(self.get_tk_pattern).search(host_html).group()
            if not self.language_map:
                self.language_map = self.get_language_map(ss, timeout, proxies)

            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            self.tk = self.get_tk(ss, timeout, proxies)
            self.api_headers.update({
                "app-name": "xy",
                "device-id": "",
                "os-type": "web",
                "os-version": "",
                "version": "1.8.0",
                "X-Authorization": self.tk,
            })
            self.jwt = self.get_jwt(self.browser_id, self.api_headers, ss, timeout, proxies)
            self.api_headers.update({"T-Authorization": self.jwt})
            form_data = {
                "browser_id": self.browser_id,
                "cached": "true",
                "dict": "true",
                "media": "text",
                "os_type": "web",
                "replaced": "true",
                "request_id": "web_fanyi",
                "source": query_text,
                "trans_type": f"{from_language}2{to_language}",
            }
            if from_language == 'auto':
                form_data.update({'detect': 'true'})
            if use_domain:
                form_data.update({"dict_name": use_domain, "use_common_dict": "true"})
            _ = ss.options(self.api_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            r = ss.post(self.api_url, headers=self.api_headers, json=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        self.api_headers.pop('T-Authorization')
        data['target'] = self.decrypt(data['target'])
        return data if is_detail_result else data['target']


class Deepl(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://www.deepl.com/translator'
        self.api_url = 'https://www2.deepl.com/jsonrpc'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_ajax_for_api=False, if_json_for_api=True)
        self.api_headers.update({'TE': 'trailers'})
        self.request_id = random.randrange(100,10000) * 10000 + 5
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'zh'

    def get_language_map(self, host_html):
        pattern = '//*[@dl-test="language-selector"]//option[@value]/@value'
        lang_list = lxml.etree.HTML(host_html).xpath(pattern)
        lang_list = list(set([x.split('/')[1] for x in lang_list if 'auto' not in x]))
        return {}.fromkeys(lang_list, lang_list)

    def split_sentences_param(self, query_text, from_language):
        params = {'method': 'LMT_split_into_sentences'}
        data = {
            'id': self.request_id + 0,
            'jsonrpc': '2.0',
            'params': {
                'texts': [query_text],
                'lang': {
                    'lang_user_selected': from_language,
                    'preference':{
                        'weight': {},
                        'default': 'default',
                    },
                },
            },
        }
        data.update(params)
        return params, data

    def context_sentences_param(self, sentences, from_language, to_language):
        sentences = [''] + sentences + ['']
        params = {'method': 'LMT_handle_jobs'}
        data = {
            'id': self.request_id + 1,
            'jsonrpc':' 2.0',
            'params': {
                'priority': 1, #-1 if 'quality': 'fast'
                'commonJobParams': {
                    # 'regionalVariant': 'en-US',
                    'browserType': 1,
                    'formality': None,
                },
                'timestamp': int(time.time()*1000),
                'jobs': [
                    {
                        'kind': 'default',
                        # 'quality': 'fast', # -1
                        'raw_en_sentence': sentences[i],
                        'raw_en_context_before': [sentences[i-1]] if sentences[i-1] else [],
                        'raw_en_context_after': [sentences[i+1]] if sentences[i+1] else [],
                        'preferred_num_beams': 1 if len(sentences)>=4 else 4, # 1 if two sentences else 4, len>=2+2
                    } for i in range(1,len(sentences)-1)
                ],
                'lang': {
                    'preference':{
                        'weight': {},
                        'default': 'default',
                    },
                    'source_lang_computed': from_language,
                    'target_lang': to_language,
                },
            },
        }
        data.update(params)
        return params, data

    # @Tse.time_stat
    def deepl_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://www.deepl.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)
        delete_temp_language_map_label = 0

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            if not self.language_map:
                self.language_map = self.get_language_map(host_html)
            if not self.language_map:
                delete_temp_language_map_label += 1
                self.language_map = self.make_temp_language_map(from_language, to_language)
            from_language, to_language = self.check_language(from_language, to_language, language_map=self.language_map,
                                                             output_zh=self.output_zh, output_auto='auto')
            from_language = from_language.upper() if from_language != 'auto' else from_language
            to_language = to_language.upper() if to_language != 'auto' else to_language

            ss_params, ss_data = self.split_sentences_param(query_text, from_language)
            _ = ss.options(self.api_url, params=ss_params, headers=self.api_headers, timeout=timeout, proxies=proxies)
            r_ss = ss.post(self.api_url, params=ss_params, json=ss_data, headers=self.api_headers, timeout=timeout, proxies=proxies)
            r_ss.raise_for_status()
            ss_data = r_ss.json()
            ss_sentences = ss_data['result']['splitted_texts'][0]

            cs_params, cs_data = self.context_sentences_param(ss_sentences, from_language, to_language)
            _ = ss.options(self.api_url, params=cs_params, headers=self.api_headers, timeout=timeout, proxies=proxies)
            r_cs = ss.post(self.api_url, params=cs_params, json=cs_data, headers=self.api_headers, timeout=timeout, proxies=proxies)
            r_cs.raise_for_status()
            data = r_cs.json()

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else ' '.join(item['beams'][0]['postprocessed_sentence'] for item in data['result']['translations'])


class Yandex(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://translate.yandex.com'
        self.api_url = 'https://translate.yandex.net/api/v1/tr.json/translate'
        self.detect_language_url = 'https://translate.yandex.net/api/v1/tr.json/detect'
        self.host_headers = self.get_headers(self.host_url, if_api=False, if_ajax_for_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_ajax_for_api=True)
        self.language_map = None
        self.sid = None
        self.query_count = 0
        self.output_zh = 'zh'

    def get_language_map(self, host_html):
        lang_str = re.compile(pattern='TRANSLATOR_LANGS: {(.*?)},', flags=re.S).findall(host_html)
        if not lang_str:
            return {}
        lang_dict = eval('{' + lang_str[0] + '}')
        return {}.fromkeys(lang_dict.keys(), lang_dict.keys())

    def detect_language(self, ss, query_text, sid, timeout, proxies):
        params = {'sid': sid, 'srv': 'tr-text', 'text': query_text, 'hint': 'zh,en', 'options': 1,}
        r = ss.get(self.detect_language_url, params=params, headers=self.host_headers, timeout=timeout, proxies=proxies)
        r.raise_for_status()
        return r.json().get('lang')

    # @Tse.time_stat
    def yandex_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://translate.yandex.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            if not self.sid:
                sid_find = re.compile("SID: '(.*?)',").findall(host_html)
                self.sid = sid_find[0] if sid_find else '3d58bd71.5f49c293.93b157d0.74722d74657874'
            if not self.language_map:
                self.language_map = self.get_language_map(host_html)

            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            from_language = self.detect_language(ss, query_text, self.sid, timeout, proxies) if from_language=='auto' else from_language
            params = {
                'id': f'{self.sid}-{self.query_count}-0',
                'lang': f'{from_language}-{to_language}',
                'srv': 'tr-text',
                'reason': 'auto',
                'format': 'text'
            }
            form_data = {'text': query_text, 'options': 4}
            r = ss.post(self.api_url, headers=self.api_headers, params=params, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['text'][0]


class Argos(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://translate.argosopentech.com'
        self.api_url = f'{self.host_url}/translate'
        self.language_url = f'{self.host_url}/languages'
        self.host_headers = self.get_headers(self.host_url, if_api=False, if_ajax_for_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_ajax_for_api=False, if_json_for_api=True)
        self.language_headers = self.get_headers(self.host_url, if_api=False, if_json_for_api=True)
        self.host_pool = ['https://translate.argosopentech.com', 'https://libretranslate.de',
                          'https://translate.astian.org', 'https://translate.mentality.rip',
                          'https://translate.api.skitzen.com', 'https://trans.zillyhuhn.com']
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'zh'

    def get_language_map(self, lang_url, ss, headers, timeout, proxies):
        # et = lxml.etree.HTML(host_html)
        # lang_list = sorted(list(set(et.xpath('//*/select/option/@value'))))
        lang_list = ss.get(lang_url, headers=headers, timeout=timeout, proxies=proxies).json()
        lang_list = sorted([lang['code'] for lang in lang_list])
        return {}.fromkeys(lang_list, lang_list)

    def argos_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://translate.argosopentech.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param reset_host_url: str, default None.
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        reset_host_url = kwargs.get('reset_host_url', None)
        if reset_host_url and reset_host_url != self.host_url:
            assert reset_host_url in self.host_pool, f'`reset_host_url` not in `host_pool`: {self.host_pool}'
            self.host_url = reset_host_url
            self.api_url = f'{self.host_url}/translate'
            self.language_url = f'{self.host_url}/languages'

        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)
        delete_temp_language_map_label = 0

        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            if not self.language_map:
                self.language_map = self.get_language_map(self.language_url, ss, self.language_headers, timeout, proxies)
            if not self.language_map:
                delete_temp_language_map_label += 1
                self.language_map = self.make_temp_language_map(from_language, to_language)

            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            form_data = {'q': query_text, 'source': from_language, 'target': to_language, 'format': 'text'}
            r = ss.post(self.api_url, headers=self.api_headers, json=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['translatedText']


class Iciba(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://www.iciba.com/fy'
        self.api_url = 'https://ifanyi.iciba.com/index.php'
        self.host_headers = self.get_headers(self.host_url, if_api=False, if_ajax_for_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_ajax_for_api=True, if_json_for_api=False)
        self.language_headers = self.get_headers(self.host_url, if_api=False, if_json_for_api=True)
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'zh'

    def get_language_map(self, api_url, ss, headers, timeout, proxies):
        params = {'c': 'trans', 'm': 'getLanguage', 'q': 0, 'type': 'en', 'str': ''}
        dd = ss.get(api_url, params=params, headers=headers, timeout=timeout, proxies=proxies).json()
        lang_list = sorted(list(set([lang for d in dd for lang in dd[d]])))
        return {}.fromkeys(lang_list, lang_list)

    def iciba_api(self, query_text:str, from_language:str='auto', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://www.iciba.com/fy
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)
        delete_temp_language_map_label = 0

        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            if not self.language_map:
                self.language_map = self.get_language_map(self.api_url, ss, self.language_headers, timeout, proxies)
            if not self.language_map:
                delete_temp_language_map_label += 1
                self.language_map = self.make_temp_language_map(from_language, to_language)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

            sign = hashlib.md5(f"6key_cibaifanyicjbysdlove1{query_text}".encode()).hexdigest()[:16]
            params = {'c': 'trans', 'm': 'fy', 'client': 6, 'auth_user': 'key_ciba', 'sign': sign}
            form_data = {'from': from_language, 'to': to_language, 'q': query_text}
            r = ss.post(self.api_url, headers=self.api_headers, params=params, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['content']['out']


class Iflytek(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://saas.xfyun.cn/translate?tabKey=text'
        self.api_url = 'https://saas.xfyun.cn/ai-application/trans/its'
        self.old_language_url = 'https://saas.xfyun.cn/_next/static/nm6eUaYRIwR8O8PcfxpxX/pages/translate.js'
        self.language_url_pattern = 'https://saas.xfyun.cn/_next/static/(.*?)/pages/translate.js'
        self.language_url = None
        self.cookies_url = 'https://sso.xfyun.cn//SSOService/login/getcookies'
        self.info_url = 'https://saas.xfyun.cn/ai-application/user/info'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True)
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'cn'

    def get_language_map(self, host_html, ss, headers, timeout, proxies):
        try:
            r = ss.get(self.old_language_url, headers=headers, timeout=timeout, proxies=proxies)
            r.raise_for_status()
        except:
            if not self.language_url:
                self.language_url = re.compile(self.language_url_pattern).search(host_html).group(0)
            r = ss.get(self.language_url, headers=headers, timeout=timeout, proxies=proxies)

        js_html = r.text
        lang_str = re.compile('languageList:{(.*?)}').search(js_html).group()[13:]
        lang_list = sorted(list(execjs.eval(lang_str).keys()))
        return {}.fromkeys(lang_list, lang_list)

    def iflytek_api(self, query_text:str, from_language:str='zh', to_language:str='en', **kwargs) -> Union[str,dict]:
        """
        https://saas.xfyun.cn/translate?tabKey=text
        :param query_text: str, must.
        :param from_language: str, default 'zh', unsupported 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)
        delete_temp_language_map_label = 0
        assert from_language != 'auto', 'unsupported [from_language=auto] with [iflytek] !'

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            _ = ss.get(self.cookies_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            _ = ss.get(self.info_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            if not self.language_map:
                self.language_map = self.get_language_map(host_html, ss, self.host_headers, timeout, proxies)
            if not self.language_map:
                delete_temp_language_map_label += 1
                self.language_map = self.make_temp_language_map(from_language, to_language)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

            cookie_dict = ss.cookies.get_dict()
            self.api_headers.update({'Cookie': f'_wafuid={cookie_dict["_wafuid"]}; di_c_mti={cookie_dict["SESSION"]}'})

            cipher_query_text = base64.b64encode(query_text.encode()).decode()
            form_data = {'from': from_language, 'to': to_language, 'text': cipher_query_text}
            r = ss.post(self.api_url, headers=self.api_headers, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['data']['result']['trans_result']['dst']


REQUEST_SERVER_REGION_INFO = TranslatorSeverRegion().request_server_region_info

_alibaba = Alibaba()
alibaba = _alibaba.alibaba_api
_argos = Argos()
argos = _argos.argos_api
_baidu = Baidu()
baidu = _baidu.baidu_api
_bing = Bing()
bing = _bing.bing_api
_caiyun = Caiyun()
caiyun = _caiyun.caiyun_api
_deepl = Deepl()
deepl = _deepl.deepl_api
# _google = GoogleV1()
_google = GoogleV2()
google = _google.google_api
_iciba = Iciba()
iciba = _iciba.iciba_api
_iflytek = Iflytek()
iflytek = _iflytek.iflytek_api
_sogou = Sogou()
sogou = _sogou.sogou_api
_tencent = Tencent()
tencent = _tencent.tencent_api
_yandex = Yandex()
yandex = _yandex.yandex_api
_youdao = Youdao()
youdao = _youdao.youdao_api


@Tse.time_stat
def translate_html(html_text:str, to_language:str='en', translator:Callable='auto', n_jobs:int=-1, **kwargs) -> str:
    """
    Translate the displayed content of html without changing the html structure.
    :param html_text: str, html format.
    :param to_language: str, default: 'en'.
    :param translator: translator, default 'auto', means ts.bing
    :param n_jobs: int, default -1, means os.cpu_cnt().
    :param **kwargs:
        :param if_ignore_limit_of_length: boolean, default False.
        :param timeout: float, default None.
        :param proxies: dict, default None.
    :return: str, html format.
    """
    if kwargs:
        for param in ('query_text', 'to_language', 'is_detail_result'):
            assert param not in kwargs, f'{param} should not be in `**kwargs`.'
    kwargs.update({'sleep_seconds': 0})

    n_jobs = os.cpu_count() if n_jobs <= 0 else n_jobs
    translator = bing if translator == 'auto' else translator

    pattern = re.compile(r"(?:^|(?<=>))([\s\S]*?)(?:(?=<)|$)") #TODO: <code></code> <div class="codetext notranslate">
    sentence_list = set(pattern.findall(html_text))
    _map_translate_func = lambda sentence: (sentence,translator(query_text=sentence, to_language=to_language, **kwargs))
    result_list = pathos.multiprocessing.ProcessPool(n_jobs).map(_map_translate_func, sentence_list)
    result_dict = {text: ts_text for text,ts_text in result_list}
    _get_result_func = lambda k: result_dict.get(k.group(1), '')
    return pattern.sub(repl=_get_result_func, string=html_text)
