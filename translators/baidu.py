# coding=utf-8
# author=UlionTse

'''MIT License

Copyright (c) 2019 UlionTse

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
import random
import requests
import execjs
from lxml import etree
from urllib.parse import urlencode


class Baidu:
    def __init__(self):
        self.origin_url = 'https://fanyi.baidu.com'
        self.langdetect_url = 'https://fanyi.baidu.com/langdetect'
        self.api_url = 'https://fanyi.baidu.com/v2transapi'
        self.get_sign_url ='https://fanyi-cdn.cdn.bcebos.com/static/translation/pkg/index_bd36cef.js'
        self.origin_headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, sdch, br",
            "accept-language": "zh-CN,zh;q=0.8,en;q=0.6",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/55.0.2883.87 Safari/537.36"
        }
        self.api_headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.8,en;q=0.6",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://fanyi.baidu.com",
            "referer": "https://fanyi.baidu.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/55.0.2883.87 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        }
        self.bdtk_pool = [
            {"baidu_id": "F215FBBB82CAF048A24B86785E193475:FG=1", "token": "4e6d918b00ada40933d3e63fd2f2c009"},
            {"baidu_id": "CC1996183B06AC5DD987C80465B33C2D:FG=1", "token": "b670bbc1562d679045dbea34270af2bc"},
            {"baidu_id": "97AD065BAC1491494A8D48510DABE382:FG=1", "token": "9d893922f8ea987de2f2adc81a81fbe7"},
        ]
        self.bdtk = random.choice(self.bdtk_pool)
        self.new_bdtk = None
        self.host_info = None


    def getSignHtml(self,ss,host_html,proxies):
        try:
            r = ss.get(self.get_sign_url, headers=self.origin_headers, proxies=proxies)
            r.raise_for_status()
        except:
            self.get_sign_url = re.search("https://fanyi-cdn.cdn.bcebos.com/static/translation/pkg/index_(.*?).js",host_html).group(0)
            r = ss.get(self.get_sign_url, headers=self.origin_headers, proxies=proxies)
        return r.text
            

    def getSign(self,sign_html,ts_text,gtk):
        begin_label = 'define("translation:widget/translate/input/pGrab",function(r,o,t){'
        end_label = 'var i=null;t.exports=e});'
        sign_js = sign_html[sign_html.find(begin_label)+len(begin_label):sign_html.find(end_label)]
        sign_js = sign_js.replace('function e(r)','function e(r,i)')
        return execjs.compile(sign_js).call('e',ts_text,gtk)


    def getHostInfo(self,host_html,sign_html,ts_text):
        # yjs_js_challenge_token = re.findall("window\['yjs_js_challenge_token'\]='(.*?)'", host_html)[0]
        # print(yjs_js_challenge_token)
        gtk = re.findall("window.gtk = '(.*?)';", host_html)[0]
        sign = self.getSign(sign_html,ts_text,gtk)

        et = etree.HTML(host_html)
        js_txt = et.xpath("/html/body/script[2]/text()")[0][20:-3]
        run_js = execjs.get()
        js_data = run_js.eval(js_txt)
        js_data.update({'gtk': gtk, 'sign': sign})
        return js_data
    
      
    def check_language(self,from_language, to_language):
        if from_language != 'auto' and from_language not in self.host_info['langList']:
            raise KeyError('[from_language] is not in {}'.format(self.host_info['langList']))
        elif to_language not in self.host_info['langList']:
            raise KeyError('[to_language] is not in {}'.format(self.host_info['langList']))
        elif from_language != 'auto' and to_language not in self.host_info['langMap'][from_language]:
            raise Exception('No Service about [{0} --> {1}] !'.format(from_language,to_language))
        else:
            return True


    def baidu_api(self, text='', from_language='auto', to_language='zh', **kwargs):
        '''
        https://fanyi.baidu.com
        :param text: string
        :param from_language: string, default 'auto'.
        :param to_language: string, default 'zh'
        :param **kwargs:
            :param if_check_language: boolean, default True.
            :param is_detail: boolean, default False.
            :param proxies: dict, default None.
        :return:
        '''
        if_check_language = kwargs.get('if_check_language', True)
        is_detail = kwargs.get('is_detail', False)
        proxies = kwargs.get('proxies', None)

        with requests.Session() as ss:
            host_html = ss.get(self.origin_url, headers=self.origin_headers, proxies=proxies).text
            sign_html = self.getSignHtml(ss,host_html,proxies)

            self.host_info = self.getHostInfo(host_html,sign_html, text)
            self.new_bdtk = {"baidu_id": ss.cookies.get("BAIDUID"), "token": self.host_info.get("token")}
    
            from_language = 'zh' if from_language in ('zh', 'zh-cn', 'zh-CN', 'zh-TW', 'zh-HK', 'zh-CHS') else from_language
            to_language = 'zh' if to_language in ('zh', 'zh-cn', 'zh-CN', 'zh-TW', 'zh-HK', 'zh-CHS') else to_language
            if if_check_language:
                self.check_language(from_language, to_language)
            
            self.api_headers.update({"cookie": "BAIDUID={};".format(self.bdtk['baidu_id'])})
            r2 = ss.post(self.langdetect_url,headers=self.api_headers,data={"query": text},proxies=proxies)
            from_language = r2.json()['lan'] if from_language=='auto' else from_language
                
            # param_data = {"from": from_language, "to": to_language}
            form_data = {
                "from": from_language,
                "to": to_language,
                "query": text, #from urllib.parse import quote_plus
                "transtype": "translang", #["translang","realtime"]
                "simple_means_flag": "3",
                "sign": self.host_info.get('sign'),
                "token": self.bdtk['token'], #self.host_info.get('token'),
                # "domain": "common",
            }

            r3 = ss.post(self.api_url,headers=self.api_headers,data=urlencode(form_data).encode('utf-8'),proxies=proxies)
            data = r3.json()
        return data['trans_result']['data'][0]['dst'] if not is_detail and data.get('trans_result') else data

      
baidu = Baidu()
baidu_api = baidu.baidu_api
