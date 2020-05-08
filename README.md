[translators](https://github.com/uliontse/translators/blob/master/README.md)
================================================================================

[![PyPI - Version](https://img.shields.io/badge/pypi-v4.5.0-blue.svg)](https://pypi.org/project/translators/)
[![PyPI - License](https://img.shields.io/pypi/l/translators.svg)](https://github.com/shinalone/translators/blob/master/LICENSE)
[![PyPI - Python](https://img.shields.io/badge/python-3.5+-blue.svg)](https://docs.python.org/3/)
[![PyPI - Status](https://img.shields.io/pypi/status/translators.svg)](https://pypi.org/project/translators/)



**Translators** is a library which aims to bring **free, multiple, enjoyable** translation to individuals and students in Python.

 It based on the translation interface of Google, Microsoft(Bing), Baidu, Alibaba, Tencent, NetEase(Youdao), Sogou, Deepl,  etc.

- [More about translators](#more-about-translators)
    - [Features](#features)
    - [Support Language](#support-language)
    - [About Chinese Language](#about-Chinese-language)
- [Installation](#installation)
  - [From PyPI](#from-PyPI)
  - [From Source](#from-source)
- [Getting Started](#getting-started)
- [License](#License)



## More About Translators

### Features

| Translator\Feature | Supported Language Count | Advantage                                                    |
| ------------------ | ------------------------ | ------------------------------------------------------------ |
| Google             | 104                      | support the most languages in the world                      |
| Bing               | 71                       | support the second most languages in the world               |
| Baidu              | 28                       | support the most Europe & Asia language; support professional domain |
| Alibaba            | 21                       | support the most Europe & Asia language;support professional domain |
| Tencent            | 17                       | support the most Europe & Asia language                      |
| Youdao             | 13                       | support the most Europe & Asia language                      |
| Sogou              | 61                       | support more languages in the world                          |
| Deepl              | 11                       | hign quality to Europe language                              |



### Support Language

| Language             | Supported Language \ Translator | Google | Bing               | Baidu  | Alibaba | Tencent | Youdao | Sogou              | Deepl |
| -------------------- | ------------------------------- | ------ | ------------------ | ------ | ------- | ------- | ------ | ------------------ | ----- |
| english              | en                              | Y      | Y                  | Y      | Y       | Y       | Y      | Y                  | Y     |
| chinese              | zh                              | Y      | Y                  | Y      | Y       | Y       | Y      | Y                  | Y     |
| arabic               | ar                              | Y      | Y                  | Y(ara) | Y       | Y       | Y      | Y                  |       |
| russian              | ru                              | Y      | Y                  | Y      | Y       | Y       | Y      | Y                  | Y     |
| french               | fr                              | Y      | Y                  | Y(fra) | Y       | Y       | Y      | Y                  | Y     |
| german               | de                              | Y      | Y                  | Y      | Y       | Y       | Y      | Y                  | Y     |
| spanish              | es                              | Y      | Y                  | Y(spa) | Y       | Y       | Y      | Y                  | Y     |
| portuguese           | pt                              | Y      | Y(pt/pt-pt)        | Y      | Y       | Y       | Y      | Y                  | Y     |
| italian              | it                              | Y      | Y                  | Y      | Y       | Y       | Y      | Y                  | Y     |
| japanese             | ja                              | Y      | Y                  | Y(jp)  | Y       | Y       | Y      | Y                  | Y     |
| korean               | ko                              | Y      | Y                  | Y(kor) | Y       | Y       | Y      | Y                  |       |
| greek                | el                              | Y      | Y                  | Y      |         |         |        | Y                  |       |
| dutch                | nl                              | Y      | Y                  | Y      | Y       |         |        | Y                  | Y     |
| hindi                | hi                              | Y      | Y                  |        | Y       | Y       |        | Y                  |       |
| turkish              | tr                              | Y      | Y                  |        | Y       | Y       |        | Y                  |       |
| malay                | ms                              | Y      | Y                  |        | Y       | Y       |        | Y                  |       |
| thai                 | th                              | Y      | Y                  | Y      | Y       | Y       |        | Y                  |       |
| vietnamese           | vi                              | Y      | Y                  | Y(vie) | Y       | Y       | Y      | Y                  |       |
| indonesian           | id                              | Y      | Y                  |        | Y       | Y       | Y      | Y                  |       |
| hebrew               | he                              | Y(iw)  | Y                  |        | Y       |         |        | Y                  |       |
| polish               | pl                              | Y      | Y                  | Y      | Y       |         |        | Y                  | Y     |
| mongolian            | mn                              | Y      |                    |        |         |         |        |                    |       |
| czech                | cs                              | Y      | Y                  | Y      |         |         |        | Y                  |       |
| hungarian            | hu                              | Y      | Y                  | Y      |         |         |        | Y                  |       |
| estonian             | et                              | Y      | Y                  | Y(est) |         |         |        | Y                  |       |
| bulgarian            | bg                              | Y      | Y                  | Y(bul) |         |         |        | Y                  |       |
| danish               | da                              | Y      | Y                  | Y(dan) |         |         |        | Y                  |       |
| finnish              | fi                              | Y      | Y                  | Y(fin) |         |         |        | Y                  |       |
| romanian             | ro                              | Y      | Y                  | Y(rom) |         |         |        | Y                  |       |
| swedish              | sv                              | Y      | Y                  | Y(swe) |         |         |        | Y                  |       |
| slovenian            | sl                              | Y      | Y                  | Y(slo) |         |         |        | Y                  |       |
| persian/farsi        | fa                              | Y      | Y                  |        |         |         |        | Y                  |       |
| bosnian              | bs                              | Y      | Y(bs-Latn)         |        |         |         |        | Y(bs-Latn)         |       |
| serbian              | sr                              | Y      | Y(sr-Latn/sr-Cyrl) |        |         |         |        | Y(sr-Latn/sr-Cyrl) |       |
| fijian               | fj                              |        | Y                  |        |         |         |        | Y                  |       |
| filipino             | tl                              | Y      | Y(fil)             |        |         |         |        | Y(fil)             |       |
| haitiancreole        | ht                              | Y      | Y                  |        |         |         |        | Y                  |       |
| catalan              | ca                              | Y      | Y                  |        |         |         |        | Y                  |       |
| croatian             | hr                              | Y      | Y                  |        |         |         |        | Y                  |       |
| latvian              | lv                              | Y      | Y                  |        |         |         |        | Y                  |       |
| lithuanian           | lt                              | Y      | Y                  |        |         |         |        | Y                  |       |
| urdu                 | ur                              | Y      | Y                  |        |         |         |        | Y                  |       |
| ukrainian            | uk                              | Y      | Y                  |        |         |         |        | Y                  |       |
| welsh                | cy                              | Y      | Y                  |        |         |         |        | Y                  |       |
| tahiti               | ty                              |        | Y                  |        |         |         |        | Y                  |       |
| tongan               | to                              |        | Y                  |        |         |         |        | Y                  |       |
| swahili              | sw                              | Y      | Y                  |        |         |         |        | Y                  |       |
| samoan               | sm                              | Y      | Y                  |        |         |         |        | Y                  |       |
| slovak               | sk                              | Y      | Y                  |        |         |         |        | Y                  |       |
| afrikaans            | af                              | Y      | Y                  |        |         |         |        | Y                  |       |
| norwegian            | no                              | Y      | Y                  |        |         |         |        | Y                  |       |
| bengali              | bn                              | Y      | Y(bn-BD)           |        |         |         |        | Y                  |       |
| malagasy             | mg                              | Y      | Y                  |        |         |         |        | Y                  |       |
| maltese              | mt                              | Y      | Y                  |        |         |         |        | Y                  |       |
| queretaro otomi      | otq                             |        | Y                  |        |         |         |        | Y                  |       |
| klingon/tlhingan hol | tlh                             |        | Y                  |        |         |         |        | Y                  |       |
| gujarati             | gu                              | Y      | Y                  |        |         |         |        |                    |       |
| tamil                | ta                              | Y      | Y                  |        |         |         |        |                    |       |
| telugu               | te                              | Y      | Y                  |        |         |         |        |                    |       |
| punjabi              | pa                              | Y      | Y                  |        |         |         |        |                    |       |
| ...                  | ...                             |        |                    |        |         |         |        |                    |       |

More supported language:

```python
import translators as ts

result = ts.google(query_text)
print(ts._google.language_map)
```



### About Chinese Language

| Language        | Language \Translator | Google   | Bing       | Baidu  | Alibaba  | Tencent | Youdao | Sogou | Deepl |
| --------------- | -------------------- | -------- | ---------- | ------ | -------- | ------- | ------ | ----- | ----- |
| chinese(简体)   | zh-CHS               | Y(zh-CN) | Y(zh-Hans) | Y(zh)  | Y(zh)    | Y(zh)   | Y      | Y     | Y(zh) |
| chinese(繁体)   | zh-CHT               | Y(zh-TW) | Y(zh-Hant) | Y(cht) | Y(zh-TW) |         |        | Y     |       |
| chinese(文言文) | wyw                  |          |            | Y      |          |         |        |       |       |
| chinese(粤语)   | yue                  |          | Y          | Y      |          |         |        | Y     |       |
| chinese(白苗文) | mww                  |          | Y          |        |          |         |        | Y     |       |



## Installation

### From PyPI

```shell
pip install translators --upgrade
```

### From Source

```bash
git clone https://github.com/UlionTse/translators.git
cd translators
python setup.py install
```

## Getting Started

```python
import translators as ts

result = ts.baidu(query_text='三十功名尘与土，八千里路云和月。', from_language='wyw', to_language='en')
print(result)

## output:
"""Over the past 30 years, although some fame has been established, it is as insignificant as the dust. After 
eight thousand miles of war between the north and the south, we have experienced many vicissitudes of life."""

## help:
help(ts.google)
```

## License

- Prohibition of commercial use !

  This library is designed to help students and individuals with translation services.

   For commercial use, please purchase API services from translation suppliers.

- Don't make high frequency requests !

  Enterprises provide free services, we should remain grateful, not cause trouble.

[click the detail license.](https://github.com/uliontse/translators/blob/master/LICENSE)