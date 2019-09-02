*[translators](https://github.com/shinalone/translators/blob/master/README.md)*
================================================================================

[![PyPI - Version](https://img.shields.io/badge/pypi-v4.0.6-blue.svg)](https://pypi.org/project/translators/)
[![PyPI - License](https://img.shields.io/pypi/l/translators.svg)](https://github.com/shinalone/translators/blob/master/LICENSE)
[![PyPI - Python](https://img.shields.io/badge/python-3.5%20%7C%203.6%20%7C%203.7-blue.svg)](https://docs.python.org/3/)
[![PyPi - Coverage](https://img.shields.io/badge/coverage-90%25-green.svg)]()
[![PyPI - Status](https://img.shields.io/pypi/status/translators.svg)](https://pypi.org/project/translators/)
[![PyPI - Wheel](https://img.shields.io/badge/wheel-yes-brightgreen.svg)](https://pypi.org/project/translators/)


### *1. Description:*

- *Free & Easy translators for Python, such as Google, NetEase(Youdao), etc.*

### *2. Installation & Tutorials:*

- *pip install **[translators](https://pypi.org/project/translators/)***
- *translators.google(text='', from_language='en', to_language='zh-CN', host='https://translate.google.cn', proxy=None)*
- *translators.youdao(text='', from_language='en', to_language='zh-CHS', proxy=None)*

*Examples:*

```python
>>> import translators as ts
>>> ts.google('Hello,World!')
'你好，世界！'

>>> ts.youdao('再见，世界！','zh-CN','ko')
'안녕, 세계야!'
```

### *3. Warning:*

***[Prohibition of Commercial Use !]()***

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
