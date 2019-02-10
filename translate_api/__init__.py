__version__ = "2.4.0"
__author__ = "UlionTse"

from .google import google_api as google_translate
from .youdao import youdao_api as youdao_translate

'''
__version__ = "2.4.0"
__author__ = "UlionTse"


For example:
-----------
>>> from translate_api import google_translate,youdao_translate
>>> google_translate('Hello,World!')

'你好，世界！'

>>>youdao_translate('再见，世界！','zh-CN','ko')

'안녕, 세계야!'
'''