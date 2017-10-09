#coding:utf-8


import re
import requests
from urllib.parse import quote
import execjs
from fake_useragent import UserAgent
from config import *


class google(object):

    def __init__(self):
        self.ua = UserAgent()

    def get_tkk(self,host):
        self.headers = {'User-Agent': self.ua.random}
        res = requests.get(host, headers=self.headers)

        RE_TKK = re.compile(r'''TKK=eval\(\'\(\(function\(\)\{(.+?)\}\)\(\)\)\'\);''')
        code = RE_TKK.search(res.text).group(0).encode().decode('unicode-escape')
        runjs = execjs.get()
        tkk = runjs.eval(code[10:-3])
        return tkk

    # def rshift(self,val, n):
    #     """python port for '>>>'(right shift with padding)
    #     """
    #     return (val % 0x100000000) >> n


    def _xr(self, a, b):  # 引用, thanks "ssut".
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


    def acquire(self, text, tkk):  # 引用, thanks "ssut".
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


    def translate(self, eng_txt, TK, from_language,to_language,host):
        QQ = quote(eng_txt)
        # if from_language and to_language in LANGUAGES.keys():
        try:
            if (from_language not in LANGUAGES.keys()) or (to_language not in LANGUAGES.keys()):
                raise LanguageInputError(from_language, to_language)
            global url
            url = (host + '/translate_a/single?client=t&sl={0}&tl={1}&hl=zh-CN&dt=at&dt=bd&dt=ex&dt=ld&dt=md'
                    + '&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&ie=UTF-8&oe=UTF-8&source=bh&ssel=0&tsel=0&kc=1&tk='
                    + str(TK) + '&q=' + QQ).format(from_language,to_language)
        except LanguageInputError as e:
            print(e)

        headers = {'User-Agent': self.ua.random}
        session = requests.Session()
        try:
            res = session.get(url, headers=headers)
            data = res.json()
            result = ''
            for dt in data[0]:
                if dt[0]:
                    result += dt[0]
        finally:
            session.close()
        return result


class LanguageInputError(Exception):
    def __init__(self,from_language,to_language):
        Exception.__init__(self)
        self.from_language = from_language
        self.to_language = to_language
        print('LanguageInputError:  from_language[`{0}`] or to_language[`{1}`] is error, Please check dictionary of `LANGUAGES`!\nLANGUAGES={2}'.format(
                self.from_language, self.to_language, LANGUAGES))


def api(text=r'', from_language='en',to_language='zh-CN',host='https://translate.google.cn'):
    api = google()
    tkk = api.get_tkk(host)
    TK = api.acquire(text, tkk)
    result = api.translate(text, TK, from_language,to_language,host)
    return result
