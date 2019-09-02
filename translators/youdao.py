# coding=utf-8
# author=UlionTse

'''MIT License

Copyright (c) 2019 UlionTse

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software. You may obtain a copy of the
License at

    https://github.com/shinalone/translators/blob/master/LICENSE

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import time
import warnings
import requests
from hashlib import md5
from random import randrange


class Youdao:
    def __init__(self):
        self.Languages = {
            'zh-CHS': 'chinese',
            'en': 'english',
            'ja': 'japanese',
            'ko': 'korean',
            'fr': 'french',
            'de': 'german',
            'ru': 'russian',
            'es': 'spanish',
            'pt': 'portuguese',
            'vi': 'vietnamese',
            'id': 'indonesian',
            'ar': 'arabic'
        }
        self.host = 'http://fanyi.youdao.com'
        self.api_url = 'http://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule?'
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko' \
                  ') Chrome/69.0.3497.100 Safari/537.36'
        self.cookies = {
            'OUTFOX_SEARCH_USER_ID': '{0}@10.168.8.{1}'.format(randrange(int(1e9),int(1e10)),randrange(1,100)),
            # 'OUTFOX_SEARCH_USER_ID_NCOO': '1234.1234',
            # 'JSESSIONID': 'aaaxxxxxx',
            # '___rl__test__cookies': str(int(time.time()*1000))
        }
        self.headers = {
            'User-Agent': self.ua,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'fanyi.youdao.com',
            'Origin': 'http://fanyi.youdao.com',
            'Referer': 'http://fanyi.youdao.com/?keyfrom=fanyi.logo',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7,en-GB;q=0.6,zh-TW;q=0.5,zh-HK;q=0.4',
            'Connection': 'keep-alive'
        }

    def get_form(self,text,from_language,to_language):
        from_language = 'zh-CHS' if from_language in ('zh-cn','zh-CN','zh-TW','zh-HK') else from_language
        to_language = 'zh-CHS' if to_language in ('zh-cn','zh-CN','zh-TW','zh-HK') else to_language
        if from_language not in self.Languages or to_language not in self.Languages:
            raise LanguageInputError(from_language,to_language)
        ts = str(int(time.time()))
        salt = str(ts) + str(randrange(0,10))
        sign_text = ''.join(['fanyideskweb',text,salt,'n%A-rKaT5fb[Gy?;N5@Tj']) # before 20190902: p09@Bn{h02_BIEe]$P^nG
        sign = md5(sign_text.encode()).hexdigest()
        bv = md5(self.headers['User-Agent'][8:].encode()).hexdigest()
        form = {
            'i':text,
            'from': from_language,
            'to': to_language,
            'smartresult': 'dict',
            'client': 'fanyideskweb',
            'ts': ts,                     # r = "" + (new Date).getTime()
            'salt': salt,                 # i = r + parseInt(10 * Math.random(), 10)
            'sign': sign,                 # n.md5("fanyideskweb" + e + i + "n%A-rKaT5fb[Gy?;N5@Tj"),e=text
            'bv': bv,                     # n.md5(navigator.appVersion)
            'doctype': 'json',
            'version': '2.1',
            'keyfrom': 'fanyi.web',
            'action': 'FY_BY_REALTlME', #not time.
            #'typoResult': 'false'
        }
        return form



    def youdao_api(self,text=r'',from_language='en', to_language='zh-CHS', proxy=None):
        form = self.get_form(text, from_language, to_language)
        ss = requests.Session()
        r0 = ss.get(self.host, headers=self.headers,proxies=proxy)
        if r0.status_code == 200 and len(r0.cookies)>0:
            r = ss.post(self.api_url, data=form, headers=self.headers,proxies=proxy)
        else:
            r = ss.post(self.api_url, data=form, headers=self.headers, cookies=self.cookies,proxies=proxy)
        if r.status_code == 200:
            result = r.json()
        else:
            raise Exception('NetworkRequestError: response <{}>'.format(r.status_code))
        ss.close()

        if result['errorCode'] == 0:
            return result['translateResult'][0][0]['tgt']
        else:
            raise YoudaoApiError(result['errorCode'])


class LanguageInputError(Exception):
    def __init__(self,from_language,to_language):
        Exception.__init__(self)
        self.from_language = from_language
        self.to_language = to_language
        warnings.warn('YoudaoTranslateApi supports between [english,russian,arabic,japanese,korean,vietnamese,'
                      'indonesian,french,german,spanish,portuguese] and [chinese] only.\n')
        print('LanguageInputError:  from_language[`{0}`] or to_language[`{1}`] is error, '
              'Please check dictionary of `LANGUAGES`!\n'.format(self.from_language, self.to_language))


class YoudaoApiError(Exception):
    def __init__(self,errorNum):
        Exception.__init__(self)
        self.errorMsg = {
            "10": "Sorry, individual sentences are too long for me to read!",
            "20": "Sorry, more than 20,000 words is too long. Let me catch my breath!",
            "30": "Sorry, I've racked my brain. No effective translation is possible!",
            "40": "Sorry, I'm still learning the language. Unsupported language type!",
            "50": "Sorry, please do not request service frequently!",
            "transRequestError": "Translation error, please check the network and try again!",
            "serviceError": "ServiceError!"
        }
        self.errorNum = str(errorNum)
        print('YoudaoApiError: {}\n'.format(self.errorMsg[self.errorNum]))


yd = Youdao()
youdao_api = yd.youdao_api
