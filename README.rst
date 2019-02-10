**translate_api**
=================
*1. Features:*
---------------
- *Google&NetEase. - translate_api is a python library that uses the translation functionality of the Google and Youdao interface.*
- *All languages can be translated(**google_translate**).*
- ***youdao_translate** is very friendly to Chinese translation, which is why I add it. (available in 11 foreign languages)*


*2. Usage:*
-----------
>>>from translate_api import google_translate,youdao_translate

>>>google_translate('Hello,World!')

'你好，世界！'

>>>youdao_translate('再见，世界！','zh-CN','ko')

'안녕, 세계야!'




*3. Tips:*
----------
- *pip install translate_api*
- *google_translate(text=r'',from_language='en',to_language='zh-CN',host='https://translate.google.cn', proxy=None)*
- *youdao_translate(text=r'',from_language='en',to_language='zh-CHS',proxy=None)*
