#coding:utf-8


import re
import requests
from urllib.parse import quote
import execjs
from .config import *


class google(object):

    def __init__(self):
        self.default_ua = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'

    def get_tkk(self,host):
        self.headers = {'User-Agent': self.default_ua}
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


    def acquire(self, text, tkk):  # thanks "ssut".
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
        try:
            if (from_language not in LANGUAGES.keys()) or (to_language not in LANGUAGES.keys()):
                raise LanguageInputError(from_language, to_language)
            global url
            url = (host + '/translate_a/single?client=t&sl={0}&tl={1}&hl=zh-CN&dt=at&dt=bd&dt=ex&dt=ld&dt=md'
                    + '&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&ie=UTF-8&oe=UTF-8&source=bh&ssel=0&tsel=0&kc=1&tk='
                    + str(TK) + '&q=' + QQ).format(from_language,to_language)
        except LanguageInputError as e:
            print(e)

        headers = {'User-Agent': self.default_ua}
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
    if len(text) <= 4900:
        api = google()
        tkk = api.get_tkk(host)
        TK = api.acquire(text, tkk)
        result = api.translate(text, TK, from_language,to_language,host)
        return result
    return 'Warning: THe length of text bigger than 4900. Please fix it.'




#####################################################################################################
######################### _xr(),acquire() module js:##########################
# var b = function (a, b) {
# 	for (var d = 0; d < b.length - 2; d += 3) {
# 		var c = b.charAt(d + 2),
# 			c = "a" <= c ? c.charCodeAt(0) - 87 : Number(c),
# 			c = "+" == b.charAt(d + 1) ? a >>> c : a << c;
# 		a = "+" == b.charAt(d) ? a + c & 4294967295 : a ^ c
# 	}
# 	return a
# }
#
# var tk =  function (a,TKK) {
# 	//console.log(a,TKK);
# 	for (var e = TKK.split("."), h = Number(e[0]) || 0, g = [], d = 0, f = 0; f < a.length; f++) {
# 		var c = a.charCodeAt(f);
# 		128 > c ? g[d++] = c : (2048 > c ? g[d++] = c >> 6 | 192 : (55296 == (c & 64512) && f + 1 < a.length && 56320 == (a.charCodeAt(f + 1) & 64512) ? (c = 65536 + ((c & 1023) << 10) + (a.charCodeAt(++f) & 1023), g[d++] = c >> 18 | 240, g[d++] = c >> 12 & 63 | 128) : g[d++] = c >> 12 | 224, g[d++] = c >> 6 & 63 | 128), g[d++] = c & 63 | 128)
# 	}
# 	a = h;
# 	for (d = 0; d < g.length; d++) a += g[d], a = b(a, "+-a^+6");
# 	a = b(a, "+-3^+b+-f");
# 	a ^= Number(e[1]) || 0;
# 	0 > a && (a = (a & 2147483647) + 2147483648);
# 	a %= 1E6;
# 	return a.toString() + "." + (a ^ h)
