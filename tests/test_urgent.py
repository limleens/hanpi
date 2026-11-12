import pytest
from hanpi_core.translation import sentence_translation,online_phrase
from hanpi_core.comparison import compare_transcript,comparison_view

@pytest.mark.parametrize('text,english',[
 ('我喜欢咖啡','I like coffee.'),('蒜香爆燒肉','Stir-fried roast pork with garlic.'),
 ('免治牛肉石頭飯','Hot-stone rice with minced beef.'),('你喜欢喝茶','You like drinking tea.'),
])
def test_full_phrase_translation_offline(text,english):
    result=sentence_translation(text)
    assert result.complete and result.text==english


def test_unknown_phrase_is_not_mislabeled_as_full_translation():
    result=sentence_translation('汉汉汉汉')
    assert not result.complete and 'approximate' in result.source


def test_homophones_are_not_treated_as_definite_word_errors():
    result=compare_transcript('蒜香烧肉','算想燒肉')
    assert not result.flags and result.sound_alikes
    html,choices=comparison_view('蒜香烧肉','算想燒肉')
    assert not choices and 'sound similar' in html
    assert not result.matches


def test_unseen_sentence_uses_real_translation_response(monkeypatch):
    from hanpi_core import translation
    translation.online_phrase.cache_clear()
    class Response:
        def raise_for_status(self): pass
        def json(self): return [[['We will go to the park tomorrow.','明天我们一起去公园']]]
    monkeypatch.setattr(translation.requests,'get',lambda *args,**kwargs:Response())
    result=translation.sentence_translation('明天我们一起去公园',allow_online=True)
    assert result.complete and result.text=='We will go to the park tomorrow.'
    translation.online_phrase.cache_clear()


def test_low_third_tone_gets_encouragement_without_an_invented_pass(monkeypatch):
    import app
    import numpy as np
    from types import SimpleNamespace
    monkeypatch.setattr(app,'analyze_tone',lambda audio:SimpleNamespace(detected=1,times=np.array([]),semitones=np.array([]),reason='level'))
    feedback,_,_,matched=app._practice_result(object(),'马','0')
    assert 'third tones can stay low' in feedback and not matched
