"""Whole-phrase English translation with explicit sources and honest fallback."""
from dataclasses import dataclass
from functools import lru_cache
import re
import requests
from opencc import OpenCC
from .text import clean_hanzi
from .gloss import lookup_meaning

CONVERTER=OpenCC('t2s')
PHRASES={
 '浓汤虾干津白':'Braised napa cabbage with dried shrimp.',
 '腐乳椒丝通菜':'Water spinach in spicy fermented tofu sauce.',
 '蚝油芥兰':'Chinese broccoli with oyster sauce.',
 '烧汁酿玉子豆腐':'Egg tofu with barbecue sauce.',
 '上汤豆苗':'Pea shoots in a light broth.',
 '温室菇菌石头饭':'Hot-stone rice with mushrooms.',
 '炆牛筋腩石头饭':'Hot-stone rice with beef tendon and brisket.',
 '潮式腊味石头饭':'Hot-stone rice with preserved meats.',
 '葡汁咖喱鸡石头饭':'Hot-stone curry chicken with rice.',
 '你好':'Hello', '谢谢':'Thank you.', '我喜欢咖啡':'I like coffee.',
 '我喜欢喝咖啡':'I like drinking coffee.', '图书馆在哪里':'Where is the library?',
 '今天的天气很好':'The weather is nice today.', '今天天气很好':'The weather is nice today.',
 '北京大学':'Peking University.', '我要一杯咖啡':"I'd like a cup of coffee.",
 '免治牛肉石头饭':'Hot-stone rice with minced beef.', '牛肉石头饭':'Hot-stone rice with beef.',
 '海鲜石头饭':'Hot-stone rice with seafood.', '蒜香爆烧肉':'Stir-fried roast pork with garlic.',
 '蒜香烧肉':'Garlic-flavoured roast pork.', '红烧肉':'Braised pork.',
 '宫保鸡丁':'Kung pao chicken.', '麻婆豆腐':'Mapo tofu.',
 '红烧豆腐':'Braised tofu.', '干煸四季豆':'Dry-fried green beans.',
 '清炒时蔬':'Stir-fried seasonal vegetables.', '鱼香茄子':'Eggplant in garlic sauce.',
 '豉汁排骨石头饭':'Hot-stone rice with pork ribs in black bean sauce.',
}
NOUNS={'咖啡':'coffee','茶':'tea','奶茶':'milk tea','米饭':'rice','牛肉':'beef','鸡肉':'chicken',
       '鱼':'fish','蔬菜':'vegetables','豆腐':'tofu','面条':'noodles','中文':'Chinese','汉语':'Mandarin'}

@dataclass(frozen=True)
class Translation:
    text:str
    source:str
    complete:bool


def offline_phrase(text):
    phrase=CONVERTER.convert(clean_hanzi(text))
    if phrase in PHRASES: return PHRASES[phrase]
    match=re.fullmatch(r'(我|你|他|她|我们|他们)(很)?喜欢(喝|吃)?(.+)',phrase)
    if match and match[4] in NOUNS:
        subject={'我':'I','你':'You','他':'He','她':'She','我们':'We','他们':'They'}[match[1]]
        verb='likes' if subject in ('He','She') else 'like'
        action={'喝':'drinking ','吃':'eating ',None:''}[match[3]]
        return f'{subject} {verb} {action}{NOUNS[match[4]]}.'
    return None


@lru_cache(maxsize=128)
def online_phrase(text):
    # Both calls have bounded timeouts; an unavailable provider cannot hang Learn.
    errors=[]
    try:
        response=requests.get('https://translate.googleapis.com/translate_a/single',
                              params={'client':'gtx','sl':'zh-CN','tl':'en','dt':'t','q':text},timeout=(2,3))
        response.raise_for_status()
        translated=''.join(part[0] for part in response.json()[0] if part and part[0]).strip()
        if translated and re.search('[a-zA-Z]',translated): return translated,'Google Translate'
    except (requests.RequestException,ValueError,TypeError,IndexError,KeyError):
        errors.append('Google')
    try:
        response=requests.get('https://api.mymemory.translated.net/get',
                              params={'q':text,'langpair':'zh-CN|en'},timeout=(2,3))
        response.raise_for_status()
        data=response.json()
        translated=data.get('responseData',{}).get('translatedText','').strip()
        if data.get('responseStatus')==200 and translated and re.search('[a-zA-Z]',translated):
            return translated,'MyMemory translation'
    except (requests.RequestException,ValueError,TypeError,KeyError):
        pass
    raise RuntimeError('Sentence translation is temporarily unavailable.')


def sentence_translation(text,allow_online=False):
    phrase=(text or '').strip()
    cached=offline_phrase(phrase)
    if cached: return Translation(cached,'Full translation · offline phrase',True)
    if allow_online and 1<len(clean_hanzi(phrase)) and len(phrase)<=1800:
        try:
            translated,source=online_phrase(phrase)
            return Translation(translated,f'Full translation · {source}',True)
        except RuntimeError:
            pass
    result=lookup_meaning(phrase)
    return Translation(result.text, ('Dictionary meaning' if result.exact else
                       'Full translation unavailable · approximate word meanings'),result.exact)
