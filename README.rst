**translate_api**
=================
*1. Feactures:*
---------------
- *Google. - translate_api is a python3 library that uses the translation functionality of the Google interface.*
- *Switch the server. - The default server is Google-China server, the user can switch to (google.com) server.*
- *All languages can be translated.*

*2. Usage:*
-----------
>>>from translate_api.translate_api import api

>>>api('Hello,World!')

'你好，世界！'

>>>api('こんにちは！','ja','ko')

'안녕하세요!'


*3. Tips:*
----------
- *pip install translate_api*
- *api(text=r'',from_language='en',to_language='zh-CN',host='https://translate.google.cn')*
