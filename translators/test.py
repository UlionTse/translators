# coding=utf-8
# author=UlionTse

from translators.server import *


query_text1 = '季姬寂，集鸡，鸡即棘鸡。棘鸡饥叽，季姬及箕稷济鸡。👍👍👍'
query_text2 = "北国风光，千里冰封，万里雪飘。\n望长城内外，惟余莽莽；大河上下，顿失滔滔。\n山舞银蛇，原驰蜡象，欲与天公试比高。\n"
query_text3 = 'All the past, a number of heroes, but also look at the present.'

html_text = """
<!DOCTYPE html>
<html>
<body>

<address>
Written by <a href="mailto:webmaster@example.com">Donald Duck</a>.<br> 
Visit us at:<br>
Example.com<br>
Box 564, Disneyland<br>
USA
</address>

<p>
北国风光，千里冰封，万里雪飘。望长城内外，惟余莽莽；大河上下，顿失滔滔。山舞银蛇，原驰蜡象，欲与天公试比高。\n
须晴日，看红装素裹，分外妖娆。江山如此多娇，引无数英雄竞折腰。惜秦皇汉武，略输文采；唐宗宋祖，稍逊风骚。一代天骄，成吉思汗，只识弯弓射大雕。\n
俱往矣，数风流人物，还看今朝。\n
</p>

<p></p>
<p> </p>
<p>5%</p>
<p>123\t</p>

<strong>hello world</strong>

<div class="codetext notranslate">
<code>
import translators as ts
</code>
</div>

</body>
</html>
"""


def test0():
    r = translate_html(html_text, to_language='en', translator=translators_pool[0], n_jobs=8,
                       if_ignore_empty_query=True, if_show_time_stat=True)
    print(r)


def test1():
    # for query_text in [query_text1, query_text2, query_text3]:
    for query_text in [query_text2]:
        print('alibaba:\n', alibaba(query_text))
        print('argos:\n', argos(query_text))
        print('baidu:\n', baidu(query_text))
        print('bing:\n', bing(query_text))
        print('caiyun:\n', caiyun(query_text))
        print('deepl:\n', deepl(query_text))
        print('google:\n', google(query_text))
        print('icaba:\n', iciba(query_text))
        # print('iflytek:\n', iflytek(query_text))  # todo
        print('itranslate:\n', itranslate(query_text))
        print('lingvanex:\n', lingvanex(query_text))
        print('mglip:\n', mglip(query_text))
        print('modernMt:\n', modernMt(query_text))
        print('myMemory:\n', myMemory(query_text))
        # print('niutrans:\n', niutrans(query_text))  # todo
        print('papago:\n', papago(query_text))
        print('qqFanyi:\n', qqFanyi(query_text))
        print('qqTranSmart:\n', qqTranSmart(query_text))
        print('reverso:\n', reverso(query_text))
        print('sogou:\n', sogou(query_text))
        print('translateCom:\n', translateCom(query_text))
        print('utibet:\n', utibet(query_text))
        # print('volcEngine:\n', volcEngine(query_text))  # todo
        # print('yandex:\n', yandex(query_text))  # todo
        print('youdao:\n', youdao(query_text))


if __name__ == "__main__":
    ts_status_list = preaccelerate()
    print(ts_status_list)

    test0()
    test1()
