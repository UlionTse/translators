**translate_api**
==============================
*1. Feactures:*
---------------
- *Google. - translate_api is a python3 library that uses the translation functionality of the Google interface.*
- *Switch the server. - The default server is Google-China server, the user can switch to (google.com) server.*
- *All languages can be translated.*

*2. Usage:*
-----------
>>>from translate_api.translate_api import api

>>>print(api())

''

>>>api('Hello,World!')

'你好，世界！'

>>>api('你好，世界！','zh-CN','ko')

'안녕, 세상!'

>>>print(api(text=r'こんにちは世界！',from_language='ja',to_language='en',host='https://translate.google.cn'))

'Hello World!'

*3. Tips:*
----------
- *Default function api(): api(text=r'',from_language='en',to_language='zh-CN',host='https://translate.google.cn')*
- *Finally, you can try switching the `host`(google.com) to use.*
