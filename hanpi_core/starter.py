"""Limited emergency vocabulary, not a replacement for the full CC-CEDICT."""
# Simplified, traditional, numbered pinyin, definitions. Definitions are factual
# common vocabulary; full CC-CEDICT readings/definitions take precedence.
WORDS = [
    ('吃','吃','chi1',['to eat']), ('喝','喝','he1',['to drink']),
    ('喜欢','喜歡','xi3 huan1',['to like']), ('咖啡','咖啡','ka1 fei1',['coffee']),
    ('我','我','wo3',['I; me']), ('你','你','ni3',['you']), ('你好','你好','ni3 hao3',['hello']),
    ('妈','媽','ma1',['mother; mom']), ('麻','麻','ma2',['hemp; numb']),
    ('马','馬','ma3',['horse']), ('骂','罵','ma4',['to scold']), ('吗','嗎','ma5',['question particle']),
    ('饭','飯','fan4',['cooked rice; meal']), ('牛肉','牛肉','niu2 rou4',['beef']),
    ('鸡肉','雞肉','ji1 rou4',['chicken meat']), ('石头','石頭','shi2 tou5',['stone']),
    ('水','水','shui3',['water']), ('茶','茶','cha2',['tea']), ('奶茶','奶茶','nai3 cha2',['milk tea']),
    ('中国','中國','Zhong1 guo2',['China']), ('学习','學習','xue2 xi2',['to study; to learn']),
    ('谢谢','謝謝','xie4 xie5',['thank you']), ('图书馆','圖書館','tu2 shu1 guan3',['library']),
    ('哪里','哪裡','na3 li3',['where']), ('在','在','zai4',['at; to be in']),
    ('天气','天氣','tian1 qi4',['weather']), ('今天','今天','jin1 tian1',['today']),
    ('好','好','hao3',['good; well']), ('爱','愛','ai4',['to love']),
    ('书','書','shu1',['book']), ('面条','麵條','mian4 tiao2',['noodles']),
    ('蔬菜','蔬菜','shu1 cai4',['vegetables']), ('豆腐','豆腐','dou4 fu5',['tofu']),
    ('米饭','米飯','mi3 fan4',['cooked rice']), ('鱼','魚','yu2',['fish']),
    ('肉','肉','rou4',['meat']), ('菜单','菜單','cai4 dan1',['menu']),
    ('朋友','朋友','peng2 you5',['friend']), ('学校','學校','xue2 xiao4',['school']),
    ('钱','錢','qian2',['money']), ('买','買','mai3',['to buy']), ('卖','賣','mai4',['to sell']),
]
ENTRIES = [dict(simplified=s, traditional=t, pinyin=p, definitions=d) for s,t,p,d in WORDS]
BY_WORD = {word:entry for entry in ENTRIES for word in (entry['simplified'],entry['traditional'])}
