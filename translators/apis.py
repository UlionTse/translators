# coding=utf-8
# author=UlionTse

"""MIT License

Copyright (c) 2017-2022 UlionTse

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
import uuid
import hmac
import base64
import random
import hashlib
# import functools
import warnings
import urllib.parse
from typing import Union, Callable

# import loguru
import execjs
import requests
import lxml.etree
import pathos.multiprocessing
# import cryptography.hazmat.primitives.asymmetric.rsa as cry_rsa
import cryptography.hazmat.primitives.hashes as cry_hashes
import cryptography.hazmat.primitives.asymmetric.padding as cry_padding
import cryptography.hazmat.primitives.serialization as cry_serialization


# loguru.logger.remove()
# loguru.logger.add(sys.stdout, format='[{time:HH:mm:ss}] <lvl>{message}</lvl>', level='INFO')
# loguru.logger.opt(colors=True)


class Tse:
    def __init__(self):
        self.author = 'Ulion.Tse'

    # @staticmethod
    # def time_stat(func):
    #     @functools.wraps(func)
    #     def _wrapper(*args, **kwargs):
    #         t1 = time.time()
    #         r = func(*args, **kwargs)
    #         t2 = time.time()
    #         loguru.logger.success('CostTime(fn: {}): {}s'.format(func.__name__, round((t2 - t1), 1)), style='braces')
    #         return r
    #     return _wrapper

    @staticmethod
    def get_headers(host_url, if_api=False, if_referer_for_host=True, if_ajax_for_api=True, if_json_for_api=False):
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
        url_path = urllib.parse.urlparse(host_url).path
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
        auto_pool = ('auto', 'auto-detect')
        zh_pool = ('zh', 'zh-CN', 'zh-CHS', 'zh-Hans', 'zh-Hans_CN', 'cn', 'chi')
        from_language = output_auto if from_language in auto_pool else from_language
        from_language = output_zh if output_zh and from_language in zh_pool else from_language
        to_language = output_zh if output_zh and to_language in zh_pool else to_language

        if from_language != output_auto and from_language not in language_map:
            raise TranslatorError('Unsupported from_language[{}] in {}.'.format(from_language, sorted(language_map.keys())))
        elif to_language not in language_map:
            raise TranslatorError('Unsupported to_language[{}] in {}.'.format(to_language, sorted(language_map.keys())))
        elif from_language != output_auto and to_language not in language_map[from_language]:
            raise TranslatorError('Unsupported translation: from [{0}] to [{1}]!'.format(from_language, to_language))
        elif from_language == to_language:
            raise TranslatorError(f'from_language[{from_language}] and to_language[{to_language}] should not be same.')
        return from_language, to_language

    @staticmethod
    def en_tran(from_lang, to_lang, default_lang='en-US', default_translator='Itranslate'):
        if default_translator in ('Itranslate', 'Lingvanex'):
            from_lang = default_lang if from_lang == 'en' else from_lang
            to_lang = default_lang if to_lang == 'en' else to_lang
            from_lang = default_lang.replace('-', '_') if default_translator == 'Lingvanex' and from_lang[:3] == 'en-' else from_lang
            to_lang = default_lang.replace('-', '_') if default_translator == 'Lingvanex' and to_lang[:3] == 'en-' else to_lang
            # warnings.warn(f'Unsupported [language=en] with [{default_translator}]! Please specify it.')
            # warnings.warn(f'default languages: [{from_lang}, {to_lang}]')
        return from_lang, to_lang

    @staticmethod
    def make_temp_language_map(from_language, to_language):
        warnings.warn('Did not get a complete language map. And do not use `from_language="auto"`.')
        if not (to_language != 'auto' and from_language != to_language):
            raise TranslatorError("to_language != 'auto' and from_language != to_language")
        lang_list = [from_language, to_language]
        return {}.fromkeys(lang_list, lang_list) if from_language != 'auto' else {from_language: to_language, to_language: to_language}

    @staticmethod
    def check_query_text(query_text, if_ignore_limit_of_length=False, limit_of_length=5000):
        if not isinstance(query_text, str):
            raise TranslatorError('query_text is not string type.')
        query_text = query_text.strip()
        length = len(query_text)
        if length >= limit_of_length and not if_ignore_limit_of_length:
            raise TranslatorError('The length of the text to be translated exceeds the limit.')
        else:
            if length >= limit_of_length:
                warnings.warn(f'The translation ignored the excess[above {limit_of_length}]. Length of `query_text` is {length}.')
                warnings.warn('The translation result will be incomplete.')
                return query_text[:limit_of_length - 1]
        return query_text


class TranslatorSeverRegion(Tse):
    def __init__(self):
        super().__init__()
        self.get_addr_url = 'https://geolocation.onetrust.com/cookieconsentpub/v1/geo/location'
        self.get_ip_url = 'https://httpbin.org/ip'
        self.ip_api_addr_url = 'http://ip-api.com/json'  # must http.
        self.ip_tb_add_url = 'https://ip.taobao.com/outGetIpInfo'
        self.default_country = os.environ.get('TRANSLATORS_DEFAULT_COUNTRY', None)

    @property
    def request_server_region_info(self):
        _headers_fn = lambda url: self.get_headers(url, if_api=False, if_referer_for_host=True)
        try:
            try:
                data = eval(requests.get(self.get_addr_url, headers=_headers_fn(self.get_addr_url)).text[9:-2])
                sys.stderr.write(f'Using state {data.get("stateName")} server backend.\n')
                return {'countryCode': data.get('country')}
            except requests.exceptions.Timeout:
                ip_address = requests.get(self.get_ip_url, headers=_headers_fn(self.get_ip_url)).json()['origin']
                form_data = {'ip': ip_address, 'accessKey': 'alibaba-inc'}
                data = requests.post(url=self.ip_tb_add_url, data=form_data, headers=_headers_fn(self.ip_tb_add_url)).json().get('data')
                return {'countryCode': data.get('country_id')}

        except requests.exceptions.ConnectionError:
            raise TranslatorError('Unable to connect the Internet.\n')
        except:
            warnings.warn('Unable to find server backend.\n')
            country = self.default_country or input('Please input your server region need to visit:\neg: [England, China, ...]\n')
            sys.stderr.write(f'Using country {country} server backend.\n')
            return {'countryCode': 'CN' if country == 'China' else 'EN'}


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
            d = (a % 2 ** 32) >> d if '+' == b[c + 1] else a << d
            a = a + d & (2 ** 32 - 1) if '+' == b[c] else a ^ d
            c += 3
        return a

    def _ints(self, text):
        ints = []
        for v in text:
            int_v = ord(v)
            if int_v < 2 ** 16:
                ints.append(int_v)
            else:
                # unicode, emoji
                ints.append(int((int_v - 2 ** 16) / 2 ** 10 + 55296))
                ints.append(int((int_v - 2 ** 16) % 2 ** 10 + 56320))
        return ints

    def acquire(self, text, tkk):
        ints = self._ints(text)
        size = len(ints)
        e = []
        g = 0

        while g < size:
            l = ints[g]
            if l < 2 ** 7:  # 128(ascii)
                e.append(l)
            else:
                if l < 2 ** 11:  # 2048
                    e.append(l >> 6 | 192)
                else:
                    if (l & 64512) == 55296 and g + 1 < size and ints[g + 1] & 64512 == 56320:
                        g += 1
                        l = 65536 + ((l & 1023) << 10) + (ints[g] & 1023)
                        e.append(l >> 18 | 240)
                        e.append(l >> 12 & 63 | 128)
                    else:
                        e.append(l >> 12 | 224)
                    e.append(l >> 6 & 63 | 128)  ##
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
            a = (a & (2 ** 31 - 1)) + 2 ** 31
        a %= int(1E6)
        return '{}.{}'.format(a, a ^ b)

    def get_language_map(self, host_html, ss, timeout, proxies):
        while 'source_code_name:' not in host_html:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            time.sleep(0.01)

        lang_list_str = re.compile("source_code_name:\[(.*?)\],").findall(host_html)[0]
        lang_list_str = ('[' + lang_list_str + ']').replace('code', '"code"').replace('name', '"name"')
        lang_list = [x['code'] for x in eval(lang_list_str) if x['code'] != 'auto']
        return {}.fromkeys(lang_list, lang_list)

    def get_tkk(self, host_html, ss, timeout, proxies):
        while 'tkk:' not in host_html:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            time.sleep(0.01)
        return re.compile("tkk:'(.*?)'").findall(host_html)[0]

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

        use_cn_condition = kwargs.get('if_use_cn_host', None) or self.request_server_region_info.get('countryCode') == 'CN'
        self.host_url = self.cn_host_url if use_cn_condition else self.en_host_url
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length)
        if not query_text:
            return ''

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            if not self.language_map:
                self.language_map = self.get_language_map(host_html, ss, timeout, proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

            if not self.tkk:
                self.tkk = self.get_tkk(host_html, ss, timeout, proxies)

            tk = self.acquire(query_text, self.tkk)
            self.api_url = (self.host_url + '/translate_a/single?client={0}&sl={1}&tl={2}&hl=zh-CN&dt=at&dt=bd&dt=ex'
                            + '&dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&ie=UTF-8&oe=UTF-8&source=bh&ssel=0&tsel=0&kc=1&tk='
                            + str(tk) + '&q=' + urllib.parse.quote(query_text)).format('webapp', from_language, to_language)  # [t,webapp]
            r = ss.get(self.api_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else ''.join([item[0] for item in data[0] if isinstance(item[0], str)])


class GoogleV2(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = None
        self.cn_host_url = 'https://translate.google.cn'
        self.en_host_url = 'https://translate.google.com'
        self.api_url = None
        self.request_server_region_info = REQUEST_SERVER_REGION_INFO
        self.host_headers = None
        self.api_headers = None
        self.language_map = None
        self.rpcid = 'MkEWBc'
        self.query_count = 0
        self.output_zh = 'zh-CN'
        self.input_limit = 5000

    def get_rpc(self, query_text, from_language, to_language):
        param = json.dumps([[query_text, from_language, to_language, True], [1]])
        rpc = json.dumps([[[self.rpcid, param, None, "generic"]]])
        return {'f.req': rpc}

    def get_language_map(self, host_html):
        et = lxml.etree.HTML(host_html)
        lang_list = sorted(list(set(et.xpath('//*/@data-language-code'))))
        if lang_list:
            lang_list.remove('auto')
        return {}.fromkeys(lang_list, lang_list)

    def get_info(self, host_html):
        data_str = re.compile(r'window.WIZ_global_data = (.*?);</script>').findall(host_html)[0]
        data = execjs.eval(data_str)
        return {'bl': data['cfb2h'], 'f.sid': data['FdrFJe']}

    def get_consent_cookie(self, consent_html):  # by mercuree. merged but not verify.
        et = lxml.etree.HTML(consent_html)
        input_element = et.xpath('.//input[@type="hidden"][@name="v"]')
        cookie_value = input_element[0].attrib.get('value') if input_element else 'cb'
        return f'CONSENT=YES+{cookie_value}'  # cookie CONSENT=YES+cb works for now

    # @Tse.time_stat
    def google_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, list]:
        """
        https://translate.google.com, https://translate.google.cn.
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param reset_host_url: str, default None. eg: 'https://translate.google.fr'
                :param if_use_cn_host: boolean, default None. affected by `reset_host_url`.
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or list
        """
        reset_host_url = kwargs.get('reset_host_url', None)
        if reset_host_url and reset_host_url != self.host_url:
            if not reset_host_url[:25] == 'https://translate.google.':
                raise TranslatorError('Your [reset_host_url] is wrong.')
            self.host_url = reset_host_url
        else:
            use_cn_condition = kwargs.get('if_use_cn_host', None) or self.request_server_region_info.get('countryCode') == 'CN'
            self.host_url = self.cn_host_url if use_cn_condition else self.en_host_url
        self.api_url = f'{self.host_url}/_/TranslateWebserverUi/data/batchexecute'

        self.host_headers = self.host_headers or self.get_headers(self.host_url, if_api=False)  # reuse cookie header
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_referer_for_host=True, if_ajax_for_api=True)
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        delete_temp_language_map_label = 0
        if not query_text:
            return ''

        with requests.Session() as ss:
            r = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            if 'consent.google.com' == urllib.parse.urlparse(r.url).hostname:
                self.host_headers.update({'cookie': self.get_consent_cookie(r.text)})
                host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            else:
                host_html = r.text

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
        return data if is_detail_result else ' '.join([x[0] for x in (data[1][0][0][5] or data[1][0])])


class Baidu(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://fanyi.baidu.com'
        self.api1_url = 'https://fanyi.baidu.com/transapi'
        self.api2_url = 'https://fanyi.baidu.com/v2transapi'
        self.langdetect_url = 'https://fanyi.baidu.com/langdetect'
        self.get_sign_old_url = 'https://fanyi-cdn.cdn.bcebos.com/static/translation/pkg/index_bd36cef.js'
        self.get_sign_url = None
        self.get_sign_pattern = 'https://fanyi-cdn.cdn.bcebos.com/static/translation/pkg/index_(.*?).js'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True)
        self.language_map = None
        self.token = None
        self.sign = None
        # self.acs_token = None
        self.query_count = 0
        self.output_zh = 'zh'
        self.input_limit = 5000

    def get_language_map(self, host_html):
        lang_str = re.compile('langMap: {(.*?)}').search(host_html.replace('\n', '').replace('  ', '')).group()[8:]
        return execjs.eval(lang_str)

    def get_sign(self, query_text, host_html, ss, timeout, proxies):
        gtk_list = re.compile("""window.gtk = '(.*?)';|window.gtk = "(.*?)";""").findall(host_html)[0]
        gtk = gtk_list[0] or gtk_list[1]

        try:
            if not self.get_sign_url:
                self.get_sign_url = re.compile(self.get_sign_pattern).search(host_html).group(0)
            r = ss.get(self.get_sign_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            r.raise_for_status()
        except:
            r = ss.get(self.get_sign_old_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            r.raise_for_status()
        sign_html = r.text

        begin_label = 'define("translation:widget/translate/input/pGrab",function(r,o,t){'
        end_label = 'var i=null;t.exports=e});'

        sign_js = sign_html[sign_html.find(begin_label) + len(begin_label):sign_html.find(end_label)]
        sign_js = sign_js.replace('function e(r)', 'function e(r,i)')
        return execjs.compile(sign_js).call('e', query_text, gtk)

    def get_tk(self, host_html):
        tk_list = re.compile("""token: '(.*?)',|token: "(.*?)",""").findall(host_html)[0]
        return tk_list[0] or tk_list[1]

    # def get_acs_token(self):
    #     pass

    def baidu_api_v1(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
        """
        https://fanyi.baidu.com
        :param query_text: str, must.  # attention emoji
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
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        if not query_text:
            return ''

        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies)  # must twice, send cookies.
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            if not self.language_map:
                self.language_map = self.get_language_map(host_html)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

            form_data = {
                'from': from_language,
                'to': to_language,
                'query': query_text,
                'source': 'txt',
            }
            r = ss.post(self.api1_url, data=form_data, headers=self.api_headers, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else '\n'.join([item['dst'] for item in data['data']])

    # @Tse.time_stat
    def baidu_api_v2(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
        """
        https://fanyi.baidu.com
        :param query_text: str, must.  # attention emoji
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param professional_field: str, default 'common'. Choose from ('common', 'medicine', 'electronics', 'mechanics', 'novel')
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """

        use_domain = kwargs.get('professional_field', 'common')
        if use_domain not in ('common', 'medicine', 'electronics', 'mechanics', 'novel'):  # only support zh-en, en-zh.
            raise TranslatorError('Your [professional_field] is wrong.')
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        if not query_text:
            return ''

        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies)  # must twice, send cookies.
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text

            if not self.language_map:
                self.language_map = self.get_language_map(host_html)

            self.token = self.get_tk(host_html)
            self.sign = self.get_sign(query_text, host_html, ss, timeout, proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

            if from_language == 'auto':
                res = ss.post(self.langdetect_url, headers=self.api_headers, data={"query": query_text}, timeout=timeout, proxies=proxies)
                from_language = res.json()['lan']

            params = {"from": from_language, "to": to_language}
            form_data = {
                "from": from_language,
                "to": to_language,
                "query": query_text,  # from urllib.parse import quote_plus
                "transtype": "realtime",  # ["translang","realtime"]
                "simple_means_flag": "3",
                "sign": self.sign,
                "token": self.token,
                "domain": use_domain,
            }
            form_data = urllib.parse.urlencode(form_data).encode('utf-8')
            # self.api_headers.update({'Acs-Token': self.acs_token})
            r = ss.post(self.api2_url, params=params, data=form_data, headers=self.api_headers, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else '\n'.join([x['dst'] for x in data['trans_result']['data']])

    # @Tse.time_stat
    def baidu_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
        """
        https://fanyi.baidu.com
        :param query_text: str, must.  # attention emoji
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param version: str, default 'v1'. Choose from ('v1', 'v2').
                :param professional_field: str, default 'common'. Choose from ('common', 'medicine', 'electronics', 'mechanics')
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        use_version = kwargs.get('version', 'v1')
        if use_version not in ('v1', 'v2'):
            raise TranslatorError('Your parameter [version] is wrong.')
        if use_version == 'v1':
            return self.baidu_api_v1(query_text, from_language, to_language, **kwargs)
        return self.baidu_api_v2(query_text, from_language, to_language, **kwargs)


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
        self.input_limit = 5000

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
            r.raise_for_status()
        sign = re.compile('md5\("fanyideskweb" \+ e \+ i \+ "(.*?)"\)').findall(r.text)
        return sign[0] if sign and sign != [''] else "Ygy_4c=r#e#4EX^NUGUc5"  # v1.1.10

    def get_form(self, query_text, from_language, to_language, sign_key):
        ts = str(int(time.time() * 1000))
        salt = str(ts) + str(random.randrange(0, 10))
        sign_text = ''.join(['fanyideskweb', query_text, salt, sign_key])
        sign = hashlib.md5(sign_text.encode()).hexdigest()
        bv = hashlib.md5(self.api_headers['User-Agent'][8:].encode()).hexdigest()
        form = {
            'i': query_text,
            'from': from_language,
            'to': to_language,
            'lts': ts,  # r = "" + (new Date).getTime()
            'salt': salt,  # i = r + parseInt(10 * Math.random(), 10)
            'sign': sign,  # n.md5("fanyideskweb" + e + i + "n%A-rKaT5fb[Gy?;N5@Tj"),e=text
            'bv': bv,  # n.md5(navigator.appVersion)
            'smartresult': 'dict',
            'client': 'fanyideskweb',
            'doctype': 'json',
            'version': '2.1',
            'keyfrom': 'fanyi.web',
            'action': 'FY_BY_REALTlME',
            # not time.["FY_BY_REALTlME", "FY_BY_DEFAULT", "FY_BY_CLICKBUTTION", "lan-select"]
            # 'typoResult': 'false'
        }
        return form

    # @Tse.time_stat
    def youdao_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
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
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        if not query_text:
            return ''

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            if not self.language_map:
                self.language_map = self.get_language_map(host_html)
            sign_key = self.get_sign_key(ss, host_html, timeout, proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

            form = self.get_form(query_text, from_language, to_language, sign_key)
            r = ss.post(self.api_url, data=form, headers=self.api_headers, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()

        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else '\n'.join([' '.join([it['tgt'] for it in item]) for item in data['translateResult']])


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
        self.input_limit = 2000

    def get_language_map(self, ss, language_url, timeout, proxies):
        r = ss.get(language_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
        r.raise_for_status()
        lang_map_str = re.compile(pattern='C={(.*?)}|languagePair = {(.*?)}', flags=re.S).search(r.text).group(0)  # C=
        return execjs.eval(lang_map_str)

    def get_qt(self, ss, timeout, proxies, if_session=False):
        if if_session:
            return ss.post(self.get_qt_url, headers=self.qt_headers, json=self.qtv_qtk, timeout=timeout, proxies=proxies).json()
        return requests.post(self.get_qt_url, headers=self.qt_headers, json=self.qtv_qtk, timeout=timeout, proxies=proxies).json()

    # @Tse.time_stat
    def tencent_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
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
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        if not query_text:
            return ''

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
                'sessionUuid': 'translate_uuid' + str(int(time.time() * 1000)),
            }
            r = ss.post(self.api_url, headers=self.api_headers, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else ''.join(item['targetText'] for item in data['translate']['records'])  # auto whitespace


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
        self.input_limit = 5000

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
    def alibaba_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
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
        if use_domain not in ("general", "message", "offer"):
            raise TranslatorError('Your [professional_field] is wrong.')
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        if not query_text:
            return ''

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
            params = {"dmtrack_pageid": dmtrack_pageid}
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
        self.input_limit = 1000

    def get_host_info(self, host_html):
        et = lxml.etree.HTML(host_html)
        lang_list = et.xpath('//*[@id="tta_srcsl"]/option/@value') or et.xpath('//*[@id="t_srcAllLang"]/option/@value')
        lang_list = list(set(lang_list))
        language_map = {}.fromkeys(lang_list, lang_list)
        iid = et.xpath('//*[@id="rich_tta"]/@data-iid')[0] + '.' + str(self.query_count + 1)
        ig = re.compile('IG:"(.*?)"').findall(host_html)[0]
        return {'iid': iid, 'ig': ig, 'language_map': language_map}

    def get_tk(self, host_html):
        result_str = re.compile('var params_RichTranslateHelper = (.*?);').findall(host_html)[0]
        result = execjs.eval(result_str)
        return {'key': result[0], 'token': result[1]}

    # @Tse.time_stat
    def bing_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, list]:
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
        use_cn_condition = kwargs.get('if_use_cn_host', None) or self.request_server_region_info.get('countryCode') == 'CN'
        self.host_url = self.cn_host_url if use_cn_condition else self.en_host_url
        self.api_url = self.host_url.replace('Translator', 'ttranslatev3')
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True)
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        if not query_text:
            return ''

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            self.host_info = self.get_host_info(host_html)

            if not self.language_map:
                self.language_map = self.host_info.get('language_map')
            from_language, to_language = self.check_language(from_language, to_language, self.language_map,
                                                             output_zh=self.output_zh, output_auto=self.output_auto)
            # params = {'isVertical': '1', '': '', 'IG': self.host_info['ig'], 'IID': self.host_info['iid']}
            self.api_url = self.api_url + '?isVertical=1&&IG={}&IID={}'.format(self.host_info['ig'], self.host_info['iid'])

            if not self.tk or time.time() - self.first_time > 3500:  # 3600
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
        self.input_limit = 5000

    def get_language_map(self, ss, get_language_url, timeout, proxies):
        lang_html = ss.get(get_language_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
        lang_list_str = re.compile('"ALL":\[(.*?)\]').findall(lang_html)[0]
        lang_list = execjs.eval(''.join(['[', lang_list_str, ']']))
        lang_list = [x['lang'] for x in lang_list]
        return {}.fromkeys(lang_list, lang_list)

    def get_form(self, query_text, from_language, to_language):
        uuid = ''
        for i in range(8):
            uuid += hex(int(65536 * (1 + random.random())))[2:][1:]
            if i in range(1, 5):
                uuid += '-'
        sign_text = "" + from_language + to_language + query_text + '109984457'  # window.__INITIAL_STATE__.common.CONFIG.secretCode
        sign = hashlib.md5(sign_text.encode()).hexdigest()
        form = {
            "from": from_language,
            "to": to_language,
            "text": query_text,
            "uuid": uuid,
            "s": sign,
            "client": "pc",  # wap
            "fr": "browser_pc",  # browser_wap
            "needQc": "1",
        }
        return form

    # @Tse.time_stat
    def sogou_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
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
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        if not query_text:
            return ''

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
        self.get_tk_pattern = '/assets/index.(.*?).js'
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
        self.input_limit = 5000

    def get_language_map(self, ss, timeout, proxies):
        js_html = ss.get(self.get_tk_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
        # lang_str = re.compile('Ai={(.*?)},').search(js_html).group()[3:-1]
        lang_str = re.compile('lang:{(.*?)},').search(js_html).group()[5:-1]
        lang_list = list(execjs.eval(lang_str).keys())
        return {}.fromkeys(lang_list, lang_list)

    def get_tk(self, ss, timeout, proxies):
        js_html = ss.get(self.get_tk_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
        return re.compile('headers\["X-Authorization"\]="(.*?)",').findall(js_html)[0]

    def get_jwt(self, browser_id, api_headers, ss, timeout, proxies):
        data = {"browser_id": browser_id}
        # _ = ss.options(self.get_jwt_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
        return ss.post(self.get_jwt_url, json=data, headers=api_headers, timeout=timeout, proxies=proxies).json()['jwt']

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
    def caiyun_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
        """
        https://fanyi.caiyunapp.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param professional_field: str, default None, choose from (None, "medicine","law","machinery")
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        use_domain = kwargs.get('professional_field', None)
        if use_domain not in (None, "medicine", "law", "machinery"):
            raise TranslatorError('Your [professional_field] is wrong.')
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        if not query_text:
            return ''

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            if not self.tk:
                tk_path = re.compile(self.get_tk_pattern).search(host_html).group()
                self.get_tk_url = ''.join([self.host_url, tk_path])
                self.tk = self.get_tk(ss, timeout, proxies)

            if not self.language_map:
                self.language_map = self.get_language_map(ss, timeout, proxies)

            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

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
                "source": query_text.split('\n'),
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
        return data if is_detail_result else '\n'.join([self.decrypt(item) for item in data['target']])


class Deepl(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://www.deepl.com/translator'
        self.api_url = 'https://www2.deepl.com/jsonrpc'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_ajax_for_api=False, if_json_for_api=True)
        self.params = {'split': {'method': 'LMT_split_text'}, 'handle': {'method': 'LMT_handle_jobs'}}
        self.request_id = random.randrange(100, 10000) * 10000 + 4
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'zh'
        self.input_limit = 5000

    def get_language_map(self, host_html):
        lang_list = list(set(re.compile('translateIntoLang\.(\w+)":').findall(host_html)))
        return {}.fromkeys(lang_list, lang_list)

    def split_sentences_param(self, query_text, from_language):
        data = {
            'id': self.request_id,
            'jsonrpc': '2.0',
            'params': {
                'texts': query_text.split('\n'),
                'commonJobParams': {'mode': 'translate'},
                'lang': {
                    'lang_user_selected': from_language,
                    'preference': {
                        'weight': {},
                        'default': 'default',
                    },
                },
            },
        }
        return {**self.params['split'], **data}

    def context_sentences_param(self, sentences, from_language, to_language):
        sentences = [''] + sentences + ['']
        data = {
            'id': self.request_id + 1,
            'jsonrpc': ' 2.0',
            'params': {
                'priority': 1,  # -1 if 'quality': 'fast'
                'timestamp': int(time.time() * 1000),
                'commonJobParams': {
                    # 'regionalVariant': 'en-US',
                    'browserType': 1,
                    'mode': 'translate',
                },
                'jobs': [
                    {
                        'kind': 'default',
                        # 'quality': 'fast', # -1
                        'sentences': [{'id': i-1, 'prefix': '', 'text': sentences[i]}],
                        'raw_en_context_before': sentences[1:i] if sentences[i-1] else [],
                        'raw_en_context_after': [sentences[i+1]] if sentences[i+1] else [],
                        'preferred_num_beams': 1 if len(sentences) >= 4 else 4,  # 1 if two sentences else 4, len>=2+2
                    } for i in range(1, len(sentences) - 1)
                ],
                'lang': {
                    'preference': {
                        'weight': {},
                        'default': 'default',
                    },
                    'source_lang_user_selected': from_language,  # "source_lang_computed"
                    'target_lang': to_language,
                },
            },
        }
        return {**self.params['handle'], **data}

    # @Tse.time_stat
    def deepl_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
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
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        delete_temp_language_map_label = 0
        if not query_text:
            return ''

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            if not self.language_map:
                self.language_map = self.get_language_map(host_html)
            if not self.language_map:
                delete_temp_language_map_label += 1
                self.language_map = self.make_temp_language_map(from_language, to_language)
            from_language, to_language = self.check_language(from_language, to_language, language_map=self.language_map, output_zh=self.output_zh, output_auto='auto')
            from_language = from_language.upper() if from_language != 'auto' else from_language
            to_language = to_language.upper() if to_language != 'auto' else to_language

            ssp_data = self.split_sentences_param(query_text, from_language)
            r_s = ss.post(self.api_url, params=self.params['split'], json=ssp_data, headers=self.api_headers, timeout=timeout, proxies=proxies)
            r_s.raise_for_status()
            s_data = r_s.json()

            s_sentences = [it['sentences'][0]['text'] for item in s_data['result']['texts'] for it in item['chunks']]
            h_data = self.context_sentences_param(s_sentences, from_language, to_language)

            r_cs = ss.post(self.api_url, params=self.params['handle'], json=h_data, headers=self.api_headers, timeout=timeout, proxies=proxies)
            r_cs.raise_for_status()
            data = r_cs.json()

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.request_id += 3
        self.query_count += 1
        return data if is_detail_result else ' '.join(item['beams'][0]['sentences'][0]["text"] for item in data['result']['translations'])  # not split paragraph


class Yandex(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://translate.yandex.com'
        self.api_url = 'https://translate.yandex.net/api/v1/tr.json/translate'
        self.api_host = 'https://translate.yandex.net'
        self.detect_language_url = 'https://translate.yandex.net/api/v1/tr.json/detect'
        self.host_headers = None
        self.api_headers = None
        self.language_map = None
        self.sid = None
        self.key = None
        self.csrf_token = None
        self.yu = None
        self.begin_timestamp = time.time()
        self.query_count = 0
        self.output_zh = 'zh'
        self.input_limit = 10000  # ten thousand.

    def get_language_map(self, host_html):
        lang_str = re.compile(pattern='TRANSLATOR_LANGS: {(.*?)},').findall(host_html)[0]
        lang_dict = eval('{' + lang_str + '}')
        lang_list = sorted(list(lang_dict.keys()))
        return {}.fromkeys(lang_list, lang_list)

    def get_csrf_token(self, host_html):
        return re.compile(pattern="CSRF_TOKEN: '(.*?)',").findall(host_html)[0]

    def get_key(self, host_html):
        return re.compile(pattern="SPEECHKIT_KEY: '(.*?)',").findall(host_html)[0]

    def get_sid(self, host_html):
        sid_find = re.compile("SID: '(.*?)',").findall(host_html)[0]
        return '.'.join([w[::-1] for w in sid_find.split('.')])

    def detect_language(self, ss, query_text, sid, timeout, proxies):
        params = {'sid': sid, 'srv': 'tr-text', 'text': query_text, 'hint': 'en,ru', 'options': 1}
        self.host_headers.update({'Host': self.api_host})
        r = ss.get(self.detect_language_url, params=params, headers=self.host_headers, timeout=timeout, proxies=proxies)
        r.raise_for_status()
        self.host_headers.pop('Host')
        return r.json().get('lang')

    # @Tse.time_stat
    def yandex_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
        """
        https://translate.yandex.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param reset_host_url: str, default None.eg: 'https://translate.yandex.fr'
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        reset_host_url = kwargs.get('reset_host_url', None)
        if reset_host_url and reset_host_url != self.host_url:
            if reset_host_url[:25] != 'https://translate.yandex.':
                raise TranslatorError('Your [reset_host_url] is wrong.')
            self.host_url = reset_host_url
        self.host_headers = self.get_headers(self.host_url, if_api=False, if_referer_for_host=True)  # host_html
        self.host_headers.update({'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'})
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_ajax_for_api=True)
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        if not query_text:
            return ''

        with requests.Session() as ss:
            if not (self.language_map and self.sid and self.yu and time.time() - self.begin_timestamp < 1700):  # 1800
                self.begin_timestamp = time.time()
                self.query_count = 0

                r = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
                r.raise_for_status()
                self.yu = r.cookies.get_dict().get('yuidss') or f'{random.randint(int(1e8), int(9e8))}{int(time.time())}'

                host_html = r.text
                self.sid = self.get_sid(host_html)
                self.key = self.get_key(host_html)
                self.csrf_token = self.get_csrf_token(host_html)
                self.language_map = self.get_language_map(host_html)

            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            from_language = self.detect_language(ss, query_text, self.sid, timeout, proxies) if from_language == 'auto' else from_language
            params = {
                'id': f'{self.sid}-{self.query_count}-0',
                'lang': f'{from_language}-{to_language}',
                'srv': 'tr-text',
                'reason': 'paste',  # 'auto'
                'format': 'text',
                'yu': self.yu,
            }
            form_data = {'text': query_text, 'options': 4}
            self.api_headers.update({'Host': self.api_host, 'X-CSRF-Token': self.csrf_token})
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
        self.input_limit = 5000  # unknown

    def get_language_map(self, lang_url, ss, headers, timeout, proxies):
        # et = lxml.etree.HTML(host_html)
        # lang_list = sorted(list(set(et.xpath('//*/select/option/@value'))))
        lang_list = ss.get(lang_url, headers=headers, timeout=timeout, proxies=proxies).json()
        lang_list = sorted([lang['code'] for lang in lang_list])
        return {}.fromkeys(lang_list, lang_list)

    # @Tse.time_stat
    def argos_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
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
            if reset_host_url not in self.host_pool:
                raise TranslatorError('Your [reset_host_url] is wrong.')
            self.host_url = reset_host_url
            self.api_url = f'{self.host_url}/translate'
            self.language_url = f'{self.host_url}/languages'

        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        delete_temp_language_map_label = 0
        if not query_text:
            return ''

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
        self.s_y2 = 'ifanyiweb8hc9s98e'
        self.query_count = 0
        self.output_zh = 'zh'
        self.input_limit = 3000

    def get_language_map(self, api_url, ss, headers, timeout, proxies):
        params = {'c': 'trans', 'm': 'getLanguage', 'q': 0, 'type': 'en', 'str': ''}
        dd = ss.get(api_url, params=params, headers=headers, timeout=timeout, proxies=proxies).json()
        lang_list = sorted(list(set([lang for d in dd for lang in dd[d]])))
        return {}.fromkeys(lang_list, lang_list)

    # @Tse.time_stat
    def iciba_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
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
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        delete_temp_language_map_label = 0
        if not query_text:
            return ''

        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            if not self.language_map:
                self.language_map = self.get_language_map(self.api_url, ss, self.language_headers, timeout, proxies)
            if not self.language_map:
                delete_temp_language_map_label += 1
                self.language_map = self.make_temp_language_map(from_language, to_language)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

            sign = hashlib.md5(f"6key_web_fanyi{self.s_y2}{query_text}".encode()).hexdigest()[:16]  # strip()
            params = {'c': 'trans', 'm': 'fy', 'client': 6, 'auth_user': 'key_web_fanyi', 'sign': sign}
            form_data = {'from': from_language, 'to': to_language, 'q': query_text}
            r = ss.post(self.api_url, headers=self.api_headers, params=params, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['content'] if data.get('isSensitive') == 1 else data['content']['out']


class IflytekV1(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://saas.xfyun.cn/translate?tabKey=text'
        self.api_url = 'https://saas.xfyun.cn/ai-application/trans/its'
        self.old_language_url = 'https://saas.xfyun.cn/_next/static/4bzLSGCWUNl67Xal-AfIl/pages/translate.js'
        self.language_url_pattern = '/_next/static/(\w+([-]?\w+))/pages/translate.js'
        self.language_url = None
        self.cookies_url = 'https://sso.xfyun.cn//SSOService/login/getcookies'
        self.info_url = 'https://saas.xfyun.cn/ai-application/user/info'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True)
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'cn'
        self.input_limit = 2000

    def get_language_map(self, host_html, ss, headers, timeout, proxies):
        try:
            if not self.language_url:
                url_path = re.compile(self.language_url_pattern).search(host_html).group(0)
                self.language_url = f'{self.host_url[:21]}{url_path}'
            r = ss.get(self.language_url, headers=headers, timeout=timeout, proxies=proxies)
            r.raise_for_status()
        except:
            r = ss.get(self.old_language_url, headers=headers, timeout=timeout, proxies=proxies)
            r.raise_for_status()

        if not self.language_url:
            self.language_url = self.old_language_url

        js_html = r.text
        lang_str = re.compile('languageList:\(e={(.*?)}').search(js_html).group()[16:]
        lang_list = sorted(list(execjs.eval(lang_str).keys()))
        return {}.fromkeys(lang_list, lang_list)

    # @Tse.time_stat
    def iflytek_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
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
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        delete_temp_language_map_label = 0
        if not query_text:
            return ''

        if from_language == 'auto':
            warnings.warn('Unsupported [from_language=auto] with [iflytek]! Please specify it.')
            from_language = self.output_zh

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

            # cipher_query_text = base64.b64encode(query_text.encode()).decode()
            cipher_query_text = query_text
            form_data = {'from': from_language, 'to': to_language, 'text': cipher_query_text}

            r = ss.post(self.api_url, headers=self.api_headers, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else eval(data['data'])['trans_result']['dst']


class IflytekV2(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://fanyi.xfyun.cn/console/trans/text'  # https://www.iflyrec.com/html/translate.html
        self.api_url = 'https://fanyi.xfyun.cn/api-tran/trans/its'
        self.detect_language_url = 'https://fanyi.xfyun.cn/api-tran/trans/detection'
        self.language_url_pattern = '/js/trans-text/index.(.*?).js'
        self.language_url = None
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True)
        self.language_map = None
        self.query_count = 0
        self.output_zh = 'cn'
        self.input_limit = 2000

    def get_language_map(self, host_html, ss, headers, timeout, proxies):
        host_true_url = f'https://{urllib.parse.urlparse(self.host_url).hostname}'

        et = lxml.etree.HTML(host_html)
        host_js_url = f"""{host_true_url}{et.xpath('//script[@type="module"]/@src')[0]}"""
        host_js_html = ss.get(host_js_url, headers=headers, timeout=timeout, proxies=proxies).text
        self.language_url = f"""{host_true_url}{re.compile(self.language_url_pattern).search(host_js_html).group()}"""

        lang_js_html = ss.get(self.language_url, headers=headers, timeout=timeout, proxies=proxies).text
        lang_list = re.compile('languageCode:"(.*?)",').findall(lang_js_html)
        lang_list = sorted(list(set(lang_list)))
        return {}.fromkeys(lang_list, lang_list)

    # @Tse.time_stat
    def iflytek_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
        """
        https://fanyi.xfyun.cn/console/trans/text
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
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        delete_temp_language_map_label = 0
        if not query_text:
            return ''

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text

            if from_language == 'auto':
                detect_r = ss.get(self.detect_language_url, params={'text': query_text}, headers=self.host_headers, timeout=timeout, proxies=proxies)
                from_language = detect_r.json()['data'] if detect_r.status_code == 200 and detect_r.text.strip() != '' else self.output_zh

            if not self.language_map:
                self.language_map = self.get_language_map(host_html, ss, self.host_headers, timeout, proxies)
            if not self.language_map:
                delete_temp_language_map_label += 1
                self.language_map = self.make_temp_language_map(from_language, to_language)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

            form_data = {'from': from_language, 'to': to_language, 'text': query_text}
            r = ss.post(self.api_url, headers=self.api_headers, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else eval(data['data'])['trans_result']['dst']


class Reverso(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://www.reverso.net/text-translation'
        self.api_url = 'https://api.reverso.net/translate/v1/translation'
        self.language_url = 'https://cdn.reverso.net/trans/v2.3.6/main.js'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_json_for_api=True)
        self.language_map = None
        self.language_tran = None
        self.query_count = 0
        self.output_zh = 'zh'  # 'chi', because there are self.language_tran
        self.input_limit = 2000

    def get_language_map(self, lang_url, ss, headers, timeout, proxies):
        lang_html = ss.get(lang_url, headers=headers, timeout=timeout, proxies=proxies).text
        lang_str = re.compile('const e={(.*?)}').search(lang_html).group()[8:]
        lang_dict = execjs.eval(lang_str)
        lang_dict['ptb'] = 'pt'
        lang_dict = {k: v for v, k in lang_dict.items()}
        lang_list = list(lang_dict.keys())
        return {'lang_map': {}.fromkeys(lang_list, lang_list), 'lang_tran': lang_dict}

    # @Tse.time_stat
    def reverso_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
        """
        https://www.reverso.net/text-translation
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
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        delete_temp_language_map_label = 0
        if not query_text:
            return ''

        if from_language == 'auto':
            warnings.warn('Unsupported [from_language=auto] with [reverso]! Please specify it.')
            from_language = self.output_zh

        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text

            if not self.language_map:
                lang_box = self.get_language_map(self.language_url, ss, self.host_headers, timeout, proxies)
                self.language_map, self.language_tran = lang_box['lang_map'], lang_box['lang_tran']
            if not self.language_map:
                delete_temp_language_map_label += 1
                self.language_map = self.make_temp_language_map(from_language, to_language)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            if self.language_tran:
                from_language, to_language = self.language_tran[from_language], self.language_tran[to_language]

            form_data = {
                'format': 'text',
                'from': from_language,
                'to': to_language,
                'input': query_text,
                'options': {
                    'contextResults': 'true',
                    'languageDetection': 'true',
                    'sentenceSplitter': 'true',
                    'origin': 'translation.web',
                }
            }
            r = ss.post(self.api_url, headers=self.api_headers, json=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else ' '.join(data['translation'])


class Itranslate(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://itranslate.com/webapp'
        self.api_url = 'https://web-api.itranslateapp.com/v3/texts/translate'
        self.language_url = 'https://itranslate-webapp-production.web.app/main.js'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_json_for_api=True)
        self.language_map = None
        self.language_description = None
        self.api_key = None
        self.query_count = 0
        self.output_zh = 'zh-CN'
        self.input_limit = 1000

    def get_language_map(self, lang_url, ss, headers, timeout, proxies):
        lang_html = ss.get(lang_url, headers=headers, timeout=timeout, proxies=proxies).text
        api_key = re.compile('"API-KEY":"(.*?)"').findall(lang_html)[0]

        lang_str = re.compile('d=\[{(.*?)}\]').search(lang_html).group()[2:]
        lang_origin_list = execjs.eval(lang_str)
        lang_list = [dd['dialect'] for dd in lang_origin_list]
        return {'lang_map': {}.fromkeys(lang_list, lang_list), 'lang_desc': lang_origin_list, 'api_key': api_key}

    # @Tse.time_stat
    def itranslate_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
        """
        https://itranslate.com/webapp
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en-US'.
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
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        delete_temp_language_map_label = 0
        if not query_text:
            return ''

        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text

            if not self.language_map:
                lang_box = self.get_language_map(self.language_url, ss, self.host_headers, timeout, proxies)
                self.api_key = lang_box['api_key']
                self.api_headers.update({'API-KEY': self.api_key})
                self.language_map, self.language_description = lang_box['lang_map'], lang_box['lang_desc']
            if not self.language_map:
                delete_temp_language_map_label += 1
                self.language_map = self.make_temp_language_map(from_language, to_language)

            from_language, to_language = self.en_tran(from_language, to_language, default_translator='Itranslate')
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

            form_data = {
                'source': {'dialect': from_language, 'text': query_text, 'with': ['synonyms']},
                'target': {'dialect': to_language},
            }
            r = ss.post(self.api_url, headers=self.api_headers, json=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['target']['text']


class TranslateCom(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://www.translate.com/machine-translation'
        self.api_url = 'https://www.translate.com/translator/translate_mt'
        self.lang_detect_url = 'https://www.translate.com/translator/ajax_lang_auto_detect'
        self.language_url = 'https://www.translate.com/ajax/language/ht/all'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_json_for_api=False)
        self.language_map = None
        self.language_description = None
        self.tk = None
        self.query_count = 0
        self.output_zh = 'zh'
        self.input_limit = 15000  # fifteen thousand letters left today.

    def get_language_map(self, lang_url, ss, headers, timeout, proxies):
        lang_origin_list = ss.get(lang_url, headers=headers, timeout=timeout, proxies=proxies).json()
        lang_map = {item['code']: [it['code'] for it in item['availableTranslationLanguages']] for item in lang_origin_list}
        return {'lang_map': lang_map, 'lang_desc': lang_origin_list}

    # @Tse.time_stat
    def translateCom_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
        """
        https://www.translate.com/machine-translation
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
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        delete_temp_language_map_label = 0
        if not query_text:
            return ''

        with requests.Session() as ss:
            r = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            # if not self.tk:
            #     self.tk = r.cookies.get_dict()
            #     self.api_headers.update({'Cookie': f'XSRF-TOKEN={self.tk["XSRF-TOKEN"]}; ci_session={self.tk["ci_session"]}'})

            if not self.language_map:
                lang_box = self.get_language_map(self.language_url, ss, self.host_headers, timeout, proxies)
                self.language_map, self.language_description = lang_box['lang_map'], lang_box['lang_desc']
            if not self.language_map:
                delete_temp_language_map_label += 1
                self.language_map = self.make_temp_language_map(from_language, to_language)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

            if from_language == 'auto':
                detect_form = {'text_to_translate': query_text}
                r_detect = ss.post(self.lang_detect_url, headers=self.api_headers, data=detect_form, timeout=timeout, proxies=proxies)
                from_language = r_detect.json()['language']

            form_data = {
                'text_to_translate': query_text,
                'source_lang': from_language,
                'translated_lang': to_language,
                'use_cache_only': 'false',
            }
            r = ss.post(self.api_url, headers=self.api_headers, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['translated_text']  # translation_source is microsoft, wtf!


class Utibet(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'http://mt.utibet.edu.cn/mt'  # must http
        self.api_url = self.host_url
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_json_for_api=False)
        self.language_map = {'ti': ['zh'], 'zh': ['ti']}
        self.query_count = 0
        self.output_zh = 'zh'
        self.input_limit = 5000  # unknown

    def parse_result(self, host_html):
        et = lxml.etree.HTML(host_html)
        return et.xpath('//*[@name="tgt"]/text()')[0]

    # @Tse.time_stat
    def utibet_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'zh', **kwargs) -> Union[str, dict]:
        """
        http://mt.utibet.edu.cn/mt
        :param query_text: str, must.
        :param from_language: str, default 'auto', equals to 'tibet'.
        :param to_language: str, default 'zh'.
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
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        if not query_text:
            return ''

        if from_language == 'auto':
            warnings.warn('Unsupported [from_language=auto] with [utibet]! Please specify it.')
            from_language = 'ti'

        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            form_data = {
                'src': query_text,
                'tgt': query_text if from_language == 'ti' else '',
                'lang': 'tc' if from_language == 'ti' else 'ct',
            }
            form_data = urllib.parse.urlencode(form_data)
            r = ss.post(self.api_url, headers=self.api_headers, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data_html = r.text

        time.sleep(sleep_seconds)
        self.query_count += 1
        return {'data_html': data_html} if is_detail_result else self.parse_result(data_html)


class Papago(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://papago.naver.com'
        self.api_url = 'https://papago.naver.com/apis/n2mt/translate'  # nsmt
        self.web_api_url = 'https://papago.naver.net/website'
        self.lang_detect_url = 'https://papago.naver.com/apis/langs/dect'
        self.language_url = None
        self.language_url_pattern = '/home.(.*?).chunk.js'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_json_for_api=False)
        self.language_map = None
        self.device_id = uuid.uuid4().__str__()
        self.auth_key = None  # 'v1.7.1_12f919c9b5'  #'v1.6.7_cc60b67557'
        self.query_count = 0
        self.output_zh = 'zh-CN'
        self.input_limit = 5000

    def get_language_map(self, host_html, ss, headers, timeout, proxies):
        try:
            if not self.language_url:
                url_path = re.compile(self.language_url_pattern).search(host_html).group()
                self.language_url = ''.join([self.host_url, url_path])
            lang_js_html = ss.get(self.language_url, headers=headers, timeout=timeout, proxies=proxies).text

            self.auth_key = self.get_auth_key(lang_js_html)

            lang_str = re.compile('={ALL:(.*?)}').search(lang_js_html).group()[1:]
            lang_str = lang_str.lower().replace('zh-cn', 'zh-CN').replace('zh-tw', 'zh-TW')
            lang_list = re.compile(',"(.*?)":|,(.*?):').findall(lang_str)
            lang_list = [j if j else k for j, k in lang_list]
            lang_list = sorted(list(filter(lambda x: x not in ('all', 'auto'), lang_list)))
            return {}.fromkeys(lang_list, lang_list)
        except:
            lang_list = ['de', 'en', 'es', 'fr', 'hi', 'id', 'it', 'ja', 'ko', 'pt', 'ru', 'th', 'vi', 'zh-CN', 'zh-TW']
            return {}.fromkeys(lang_list, lang_list)

    def get_auth_key(self, lang_js_html):
        return re.compile('AUTH_KEY:"(.*?)"').findall(lang_js_html)[0]

    def get_authorization(self, url, auth_key, device_id, time_stamp):
        '''Authorization: "PPG " + t + ":" + p.a.HmacMD5(t + "\n" + e.split("?")[0] + "\n" + n, "v1.6.7_cc60b67557").toString(p.a.enc.Base64)'''
        auth = hmac.new(key=auth_key.encode(), msg=f'{device_id}\n{url}\n{time_stamp}'.encode(), digestmod='md5').digest()
        return f'PPG {device_id}:{base64.b64encode(auth).decode()}'

    def trans_web(self, from_language, to_language, web_link, ss, headers, proxies, timeout):
        params = {'url': web_link, 'target': to_language, 'source': from_language, 'locale': 'en'}
        return ss.get(self.web_api_url, params=params, headers=headers, proxies=proxies, timeout=timeout).text

    # @Tse.time_stat
    def papago_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
        """
        https://papago.naver.com
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param if_translate_web_link: boolean, default False. eg, meanwhile query_text='https://www.naver.com'.
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        if_translate_web_link = kwargs.get('if_translate_web_link', False)
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        delete_temp_language_map_label = 0
        if not query_text:
            return ''

        with requests.Session() as ss:
            host_html = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies).text
            if not self.language_map:
                self.language_map = self.get_language_map(host_html, ss, self.host_headers, timeout, proxies)
            if not self.language_map:
                delete_temp_language_map_label += 1
                self.language_map = self.make_temp_language_map(from_language, to_language)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

            if if_translate_web_link:
                return self.trans_web(from_language, to_language, query_text, ss, self.host_headers, proxies, timeout)

            detect_time = str(int(time.time() * 1000))
            detect_auth = self.get_authorization(self.lang_detect_url, self.auth_key, self.device_id, detect_time)
            detect_add_headers = {'device-type': 'pc', 'timestamp': detect_time, 'authorization': detect_auth}
            detect_headers = {**self.api_headers, **detect_add_headers}

            if from_language == 'auto':
                detect_form = urllib.parse.urlencode({'query': query_text})
                r_detect = ss.post(self.lang_detect_url, headers=detect_headers, data=detect_form, timeout=timeout, proxies=proxies)
                from_language = r_detect.json()['langCode']

            trans_time = str(int(time.time() * 1000))
            trans_auth = self.get_authorization(self.api_url, self.auth_key, self.device_id, trans_time)
            trans_update_headers = {'x-apigw-partnerid': 'papago', 'timestamp': trans_time, 'authorization': trans_auth}
            detect_headers.update(trans_update_headers)
            trans_headers = detect_headers

            form_data = {
                'deviceId': self.device_id,
                'text': query_text, 'source': from_language, 'target': to_language, 'locale': 'en',
                'dict': 'true', 'dictDisplay': 30, 'honorific': 'false', 'instant': 'false', 'paging': 'false',
            }
            form_data = urllib.parse.urlencode(form_data)
            r = ss.post(self.api_url, headers=trans_headers, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['translatedText']


class Lingvanex(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://lingvanex.com/demo/'
        self.api_url = None
        self.language_url = None
        self.auth_url = 'https://lingvanex.com/lingvanex_demo_page/js/api-base.js'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_json_for_api=False)
        self.language_map = None
        self.detail_language_map = None
        self.auth_info = None
        self.mode = None
        self.query_count = 0
        self.output_zh = 'zh-Hans_CN'
        self.input_limit = 10000

    def get_auth(self, auth_url, ss, headers, timeout, proxies):
        js_html = ss.get(auth_url, headers=headers, timeout=timeout, proxies=proxies).text
        return {k: v for k, v in re.compile(',(.*?)="(.*?)"').findall(js_html)}

    def get_language_map(self, lang_url, ss, headers, timeout, proxies):
        params = {'all': 'true', 'code': 'en_GB', 'platform': 'dp', '_': int(time.time() * 1000)}
        detail_lang_map = ss.get(lang_url, params=params, headers=headers, timeout=timeout, proxies=proxies).json()
        for _ in range(3):
            _ = ss.get(lang_url, params={'platform': 'dp'}, headers=headers, timeout=timeout, proxies=proxies)
        lang_list = sorted(set([item['full_code'] for item in detail_lang_map['result']]))
        return {'d_lang_map': detail_lang_map, 'lang_map': {}.fromkeys(lang_list, lang_list)}

    # @Tse.time_stat
    def lingvanex_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
        """
        https://lingvanex.com/demo/
        :param query_text: str, must.
        :param from_language: str, default 'auto'.
        :param to_language: str, default 'en'.
        :param **kwargs:
                :param mode: str, default "B2C", choose from ("B2B", "B2C").
                :param if_ignore_limit_of_length: boolean, default False.
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or dict
        """
        mode = kwargs.get('mode', 'B2C')
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        if_ignore_limit_of_length = kwargs.get('if_ignore_limit_of_length', False)
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        delete_temp_language_map_label = 0
        if not query_text:
            return ''

        if from_language == 'auto':
            warnings.warn('Unsupported [from_language=auto] with [lingvanex]! Please specify it.')
            from_language = self.output_zh

        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies)

            if not self.auth_info:
                self.auth_info = self.get_auth(self.auth_url, ss, self.host_headers, timeout, proxies)

            if mode != self.mode:
                self.mode = mode
                self.api_url = ''.join([self.auth_info[f'{mode}_BASE_URL'], self.auth_info['TRANSLATE_URL']])
                self.language_url = ''.join([self.auth_info[f'{mode}_BASE_URL'], self.auth_info['GET_LANGUAGES_URL']])
                self.host_headers.update({'authorization': self.auth_info[f'{mode}_AUTH_TOKEN']})
                self.api_headers.update({'authorization': self.auth_info[f'{mode}_AUTH_TOKEN']})
                self.api_headers.update({'referer': urllib.parse.urlparse(self.auth_info[f'{mode}_BASE_URL']).netloc})

            if not self.language_map:
                lang_data = self.get_language_map(self.language_url, ss, self.host_headers, timeout, proxies)
                self.detail_language_map, self.language_map = lang_data['d_lang_map'], lang_data['lang_map']
            if not self.language_map:
                delete_temp_language_map_label += 1
                self.language_map = self.make_temp_language_map(from_language, to_language)

            from_language, to_language = self.en_tran(from_language, to_language, default_translator='Lingvanex')
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

            form_data = {
                'from': from_language,
                'to': to_language,
                'text': query_text,
                'platform': 'dp',
                'is_return_text_split_ranges': 'true'
            }
            form_data = urllib.parse.urlencode(form_data)
            r = ss.post(self.api_url, headers=self.api_headers, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['result'] if self.mode == 'B2C' else data['result']['text']


class Niutrans(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'http://display.niutrans.com'  # must http
        self.api_url = 'http://display.niutrans.com/niutrans/textTranslation'
        self.cookie_url = 'http://display.niutrans.com/niutrans/user/getAccountAdmin?locale=zh-CN'
        self.user_url = 'http://display.niutrans.com/niutrans/user/getGuestUser'
        self.key_url = 'http://display.niutrans.com/niutrans/user/getOnePublicKey'
        self.token_url = 'http://display.niutrans.com/niutrans/login'
        self.info_url = 'http://display.niutrans.com/niutrans/user/getUserInfoByToken'
        self.get_language_url = 'http://display.niutrans.com/niutrans/translServiceInfo/getAllLanguage'
        self.detect_language_url = 'http://display.niutrans.com/niutrans/textLanguageDetect'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = None
        self.language_map = None
        self.detail_language_map = None
        self.account_info = None
        self.query_count = 0
        self.output_zh = 'zh'
        self.input_limit = 5000

    def get_language_map(self, lang_url, ss, headers, timeout, proxies):
        detail_lang_map = ss.get(lang_url, headers=headers, timeout=timeout, proxies=proxies).json()
        lang_list = sorted(set([item['languageAbbreviation'] for item in detail_lang_map['data']]))  # 42
        return {'d_lang_map': detail_lang_map, 'lang_map': {}.fromkeys(lang_list, lang_list)}

    def encrypt_rsa(self, message_text, public_key_text):
        """https://github.com/kjur/jsrsasign/blob/c665ebcebc62cc7e55ffadbf2efec7ef89279b00/sample_node/dataencrypt#L24"""
        public_key_pem = ''.join(['-----BEGIN PUBLIC KEY-----\n', public_key_text, '\n-----END PUBLIC KEY-----'])
        public_key_object = cry_serialization.load_pem_public_key(public_key_pem.encode())
        cipher_text = base64.b64encode(public_key_object.encrypt(
            plaintext=message_text.encode(),
            padding=cry_padding.PKCS1v15()
            # padding=cry_padding.OAEP(
            #     mgf=cry_padding.MGF1(algorithm=cry_hashes.SHA256()),
            #     algorithm=cry_hashes.SHA256(),
            #     label=None
            # )
        )).decode()
        return cipher_text

    # @Tse.time_stat
    def niutrans_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs) -> Union[str, dict]:
        """
        http://display.niutrans.com
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
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        delete_temp_language_map_label = 0
        if not query_text:
            return ''

        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            _ = ss.options(self.cookie_url, headers=self.host_headers, timeout=timeout, proxies=proxies)

            if not self.account_info:
                user_data = ss.get(self.user_url, headers=self.host_headers, timeout=timeout, proxies=proxies).json()
                key_data = ss.get(self.key_url, headers=self.host_headers, timeout=timeout, proxies=proxies).json()
                guest_info = {
                    'username': user_data['data']['username'].strip(),
                    'password': self.encrypt_rsa(message_text=user_data['data']['password'], public_key_text=key_data['data']),
                    'publicKey': key_data['data'],
                    'symbol': '',
                }
                r_tk = ss.post(self.token_url, json=guest_info, headers=self.host_headers, timeout=timeout, proxies=proxies)
                token_data = r_tk.json()
                self.account_info = {**guest_info, **token_data['data']}

            if not self.api_headers:
                self.api_headers = {**self.host_headers, **{'Jwt': self.account_info['token']}}

            ss.cookies.update({'Admin-Token': self.account_info['token']})
            # info_data = ss.get(self.info_url, headers=self.host_headers, timeout=timeout, proxies=proxies).json()

            if not self.language_map:
                lang_data = self.get_language_map(self.get_language_url, ss, self.api_headers, timeout, proxies)
                self.detail_language_map, self.language_map = lang_data['d_lang_map'], lang_data['lang_map']
            if not self.language_map:
                delete_temp_language_map_label += 1
                self.language_map = self.make_temp_language_map(from_language, to_language)

            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            if from_language == 'auto':
                res = ss.post(self.detect_language_url, json={'src_text': query_text}, headers=self.api_headers, timeout=timeout, proxies=proxies)
                from_language = res.json()['data']['language']

            form_data = {
                'src_text': query_text, 'from': from_language, 'to': to_language,
                'contrastFlag': 'true', 'termDictionaryLibraryId': '', 'translationMemoryLibraryId': '',
            }
            r = ss.post(self.api_url, json=form_data, headers=self.api_headers, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()

        if delete_temp_language_map_label != 0:
            self.language_map = None
        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else '\n'.join([' '.join([it['data'] for it in item['sentences']]) for item in data['data']])


class Mglip(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'http://fy.mglip.com/pc'  # must http
        self.api_url = 'http://fy.mglip.com/t2t'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True, if_json_for_api=False)
        self.language_map = {}.fromkeys(['zh', 'mon', 'xle'], ['zh', 'mon', 'xle'])
        self.query_count = 0
        self.output_zh = 'zh'
        self.input_limit = 500

    # @Tse.time_stat
    def mglip_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'zh', **kwargs) -> Union[str, dict]:
        """
        http://fy.mglip.com/pc
        :param query_text: str, must.
        :param from_language: str, default 'auto', equals to 'mon'.
        :param to_language: str, default 'zh'.
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
        query_text = self.check_query_text(query_text, if_ignore_limit_of_length, limit_of_length=self.input_limit)
        if not query_text:
            return ''

        if from_language == 'auto':
            warnings.warn('Unsupported [from_language=auto] with [mglip]! Please specify it.')
            from_language = 'mon'

        with requests.Session() as ss:
            _ = ss.get(self.host_url, headers=self.host_headers, timeout=timeout, proxies=proxies)
            from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)
            form_data = {
                'userInput': query_text,
                'from': from_language,
                'to': to_language,
            }
            form_data = urllib.parse.urlencode(form_data)
            r = ss.post(self.api_url, headers=self.api_headers, data=form_data, timeout=timeout, proxies=proxies)
            r.raise_for_status()
            data = r.json()

        time.sleep(sleep_seconds)
        self.query_count += 1
        return data if is_detail_result else data['datas'][0]['paragraph'] if data['datas'][0]['type'] == 'trans' else data['datas'][0]['data']



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
# _iflytek = IflytekV1()
_iflytek = IflytekV2()
iflytek = _iflytek.iflytek_api
_itranslate = Itranslate()
itranslate = _itranslate.itranslate_api
_lingvanex = Lingvanex()
lingvanex = _lingvanex.lingvanex_api
_niutrans = Niutrans()
niutrans = _niutrans.niutrans_api
_mglip = Mglip()
mglip = _mglip.mglip_api
_papago = Papago()
papago = _papago.papago_api
_reverso = Reverso()
reverso = _reverso.reverso_api
_sogou = Sogou()
sogou = _sogou.sogou_api
_tencent = Tencent()
tencent = _tencent.tencent_api
_translateCom = TranslateCom()
translateCom = _translateCom.translateCom_api
_utibet = Utibet()
utibet = _utibet.utibet_api
_yandex = Yandex()
yandex = _yandex.yandex_api
_youdao = Youdao()
youdao = _youdao.youdao_api


# @Tse.time_stat
def translate_html(html_text: str, to_language: str = 'en', translator: Callable = 'auto', n_jobs: int = -1, **kwargs) -> str:
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
            if param in kwargs:
                raise TranslatorError(f'{param} should not be in `**kwargs`.')
    kwargs.update({'sleep_seconds': 0})

    n_jobs = os.cpu_count() if n_jobs <= 0 else n_jobs
    translator = bing if translator == 'auto' else translator

    pattern = re.compile(r"(?:^|(?<=>))([\s\S]*?)(?:(?=<)|$)")  # TODO: <code></code> <div class="codetext notranslate">
    sentence_list = list(set(pattern.findall(html_text)))
    _map_translate_func = lambda sentence: (sentence, translator(query_text=sentence, to_language=to_language, **kwargs))

    with pathos.multiprocessing.ProcessPool(n_jobs) as pool:
        result_list = pool.map(_map_translate_func, sentence_list)

    result_dict = {text: ts_text for text, ts_text in result_list}
    _get_result_func = lambda k: result_dict.get(k.group(1), '')
    return pattern.sub(repl=_get_result_func, string=html_text)
