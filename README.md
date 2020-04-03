*[translators](https://github.com/uliontse/translators/blob/master/README.md)*
================================================================================

[![PyPI - Version](https://img.shields.io/badge/pypi-v4.4.3-blue.svg)](https://pypi.org/project/translators/)
[![PyPI - License](https://img.shields.io/pypi/l/translators.svg)](https://github.com/shinalone/translators/blob/master/LICENSE)
[![PyPI - Python](https://img.shields.io/badge/python-3.5%20%7C%203.6%20%7C%203.7%20%7C%203.8-blue.svg)](https://docs.python.org/3/)
[![PyPi - Coverage](https://img.shields.io/badge/coverage-90%25-green.svg)]()
[![PyPI - Status](https://img.shields.io/pypi/status/translators.svg)](https://pypi.org/project/translators/)
[![PyPI - Wheel](https://img.shields.io/badge/wheel-yes-brightgreen.svg)](https://pypi.org/project/translators/)


### *1. Description:*

- *Free & Easy translators for Python, such as Google, Microsoft(Bing), Baidu, Alibaba, Tencent, NetEase(Youdao), Sogou, etc.*

### *2. Installation & Tutorials:*

- *pip install **[translators](https://pypi.org/project/translators/)***
- *translators.google(query_text, from_language, to_language)*
- *detail to [help]()(translators.google)*

*Examples:*

```python
>>>import translators as ts

>>>ts.google('怒发冲冠凭栏处，潇潇雨歇抬望眼。', 'auto', 'en')
"At the anger rushing to the crown, Xiaoxiao Yuxie looked up."

>>>ts.bing('仰天长啸，壮怀激烈。','auto','en')
"The sky is long and squealing, strong and fierce."

>>>ts.baidu('三十功名尘与土，八千里路云和月。', 'wyw', 'en')
"""Over the past 30 years, although some fame has been established, it is as insignificant as the dust. After 
eight thousand miles of war between the north and the south, we have experienced many vicissitudes of life."""

>>>ts.sogou('莫等闲，白了少年头，空悲切。', 'auto', 'en')
"Don't take it for granted, white head, empty sorrow."

>>>ts.youdao('靖康耻，犹未雪。臣子恨，何时灭。驾长车踏破贺兰山缺。', 'auto', 'en')
"Jingkang shame, still not snow. When the courtiers hate, out. Drive a long car through helan mountain."

>>>ts.tencent('壮志饥餐胡虏肉，笑谈渴饮匈奴血。', 'auto', 'en')
"Ambition to eat hungry Hu captive meat, laugh about thirst for Xiongnu blood."

>>>ts.alibaba('待从头，收拾旧山河，朝天阙。', 'auto', 'en')
"Stay from the beginning, clean up the old mountains and rivers, and face the sky."
```


### *3. License*

***[Warning: Prohibition of Commercial Use !](https://github.com/uliontse/translators/blob/master/LICENSE)***

*This module is designed to help students and individuals with translation services.   
For commercial use, please purchase API services from translation suppliers.*

### *4. Dictionary of `LANGUAGES`:*

```python
LANGUAGES = {
    'af': 'afrikaans',
    'sq': 'albanian',
    'am': 'amharic',
    'ar': 'arabic',
    'hy': 'armenian',
    'az': 'azerbaijani',
    'eu': 'basque',
    'be': 'belarusian',
    'bn': 'bengali',
    'bs': 'bosnian',
    'bg': 'bulgarian',
    'ca': 'catalan',
    'ceb': 'cebuano',
    'ny': 'chichewa',
    'zh-CN': 'chinese (simplified)',
    'zh-TW': 'chinese (traditional)',
    'co': 'corsican',
    'hr': 'croatian',
    'cs': 'czech',
    'da': 'danish',
    'nl': 'dutch',
    'en': 'english',
    'eo': 'esperanto',
    'et': 'estonian',
    'tl': 'filipino',
    'fi': 'finnish',
    'fr': 'french',
    'fy': 'frisian',
    'gl': 'galician',
    'ka': 'georgian',
    'de': 'german',
    'el': 'greek',
    'gu': 'gujarati',
    'ht': 'haitian creole',
    'ha': 'hausa',
    'haw': 'hawaiian',
    'iw': 'hebrew',
    'hi': 'hindi',
    'hmn': 'hmong',
    'hu': 'hungarian',
    'is': 'icelandic',
    'ig': 'igbo',
    'id': 'indonesian',
    'ga': 'irish',
    'it': 'italian',
    'ja': 'japanese',
    'jw': 'javanese',
    'kn': 'kannada',
    'kk': 'kazakh',
    'km': 'khmer',
    'ko': 'korean',
    'ku': 'kurdish (kurmanji)',
    'ky': 'kyrgyz',
    'lo': 'lao',
    'la': 'latin',
    'lv': 'latvian',
    'lt': 'lithuanian',
    'lb': 'luxembourgish',
    'mk': 'macedonian',
    'mg': 'malagasy',
    'ms': 'malay',
    'ml': 'malayalam',
    'mt': 'maltese',
    'mi': 'maori',
    'mr': 'marathi',
    'mn': 'mongolian',
    'my': 'myanmar (burmese)',
    'ne': 'nepali',
    'no': 'norwegian',
    'ps': 'pashto',
    'fa': 'persian',
    'pl': 'polish',
    'pt': 'portuguese',
    'pa': 'punjabi',
    'ro': 'romanian',
    'ru': 'russian',
    'sm': 'samoan',
    'gd': 'scots gaelic',
    'sr': 'serbian',
    'st': 'sesotho',
    'sn': 'shona',
    'sd': 'sindhi',
    'si': 'sinhala',
    'sk': 'slovak',
    'sl': 'slovenian',
    'so': 'somali',
    'es': 'spanish',
    'su': 'sundanese',
    'sw': 'swahili',
    'sv': 'swedish',
    'tg': 'tajik',
    'ta': 'tamil',
    'te': 'telugu',
    'th': 'thai',
    'tr': 'turkish',
    'uk': 'ukrainian',
    'ur': 'urdu',
    'uz': 'uzbek',
    'vi': 'vietnamese',
    'cy': 'welsh',
    'xh': 'xhosa',
    'yi': 'yiddish',
    'yo': 'yoruba',
    'zu': 'zulu'
}
```
