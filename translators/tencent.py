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

import re
import time
import requests


class Tencent:
    def __init__(self):
        self.language = {
            "auto": "自动识别",
            "zh": "中文",
            "en": "英语",
            "jp": "日语",
            "kr": "韩语",
            "fr": "法语",
            "es": "西班牙语",
            "it": "意大利语",
            "de": "德语",
            "tr": "土耳其语",
            "ru": "俄语",
            "pt": "葡萄牙语",
            "vi": "越南语",
            "id": "印尼语",
            "th": "泰语",
            "ms": "马来西亚语",
            "ar": "阿拉伯语",
            "hi": "印地语"
        }
        self.translate_service = {
            "auto": ["zh", "en", "jp", "kr", "fr", "es", "it", "de", "tr", "ru", "pt", "vi", "id", "th", "ms"],
            "en": ["zh", "fr", "es", "it", "de", "tr", "ru", "pt", "vi", "id", "th", "ms", "ar", "hi"],
            "zh": ["en", "jp", "kr", "fr", "es", "it", "de", "tr", "ru", "pt", "vi", "id", "th", "ms"],
            "fr": ["zh", "en", "es", "it", "de", "tr", "ru", "pt"],
            "es": ["zh", "en", "fr", "it", "de", "tr", "ru", "pt"],
            "it": ["zh", "en", "fr", "es", "de", "tr", "ru", "pt"],
            "de": ["zh", "en", "fr", "es", "it", "tr", "ru", "pt"],
            "tr": ["zh", "en", "fr", "es", "it", "de", "ru", "pt"],
            "ru": ["zh", "en", "fr", "es", "it", "de", "tr", "pt"],
            "pt": ["zh", "en", "fr", "es", "it", "de", "tr", "ru"],
            "vi": ["zh", "en"],
            "id": ["zh", "en"],
            "ms": ["zh", "en"],
            "th": ["zh", "en"],
            "jp": ["zh"],
            "kr": ["zh"],
            "ar": ["en"],
            "hi": ["en"]
        }
        self.api_url = 'https://fanyi.qq.com/api/translate'
        self.headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'fanyi.qq.com',
            'Origin': 'https://fanyi.qq.com',
            'Referer': 'https://fanyi.qq.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }


    def judgeLangError(self,from_language, to_language):
        if from_language not in self.translate_service.keys():
            raise KeyError('[from_language] is not in {}'.format(self.language))
        elif to_language not in self.translate_service.keys():
            raise KeyError('[to_language] is not in {}'.format(self.language))
        elif to_language not in self.translate_service[from_language]:
            raise Exception('No Service about [{0} --> {1}] !'.format(from_language,to_language))
        else:
            pass


    def tencent_api(self,text='',from_language='en', to_language='zh', is_detail=False, proxy=None):
        from_language = 'zh' if from_language in ('zh-cn','zh-CN','zh-TW','zh-HK','zh-CHS') else from_language
        to_language = 'zh' if to_language in ('zh-cn','zh-CN','zh-TW','zh-HK','zh-CHS') else to_language
        self.judgeLangError(from_language,to_language)

        ss = requests.Session()
        r0 = ss.get(self.headers['Origin'], headers=self.headers,proxies=proxy)
        qtv = re.findall('var qtv = "(.*?)"', r0.text)[0]
        qtk = re.findall('var qtk = "(.*?)"', r0.text)[0]
        form_data = {
            'source': from_language,
            'target': to_language,
            'sourceText': text,
            'qtv': qtv,
            'qtk': qtk,
            'sessionUuid': 'translate_uuid' + str(int(time.time()*1000))
        }
        r1 = ss.post(self.api_url, headers=self.headers, data=form_data,proxies=proxy)
        reseult = r1.json()
        r = reseult['translate']['records'][0]['targetText']
        ss.close()
        return reseult if is_detail else r


tct = Tencent()
tencent_api = tct.tencent_api
