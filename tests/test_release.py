"""Release regressions: real dictionary data, offline lookup, OCR and word comparison."""
from pathlib import Path
import gzip

import numpy as np
from PIL import Image
import pytest

from hanpi_core import dictionary,gloss,search,ocr
from hanpi_core.asr import audio_for_asr
from hanpi_core.comparison import compare_transcript,comparison_view
from hanpi_core.text import get_syllables

FIXTURES=Path(__file__).parent/'fixtures'


def test_real_dictionary_uses_utf8_under_windows_style_decoding(monkeypatch):
    from pycccedict.cccedict import CcCedict
    real_open=gzip.open
    def cp1252_default(*args,**kwargs):
        if 't' in kwargs.get('mode',args[1] if len(args)>1 else 'rb') and 'encoding' not in kwargs:
            kwargs['encoding']='cp1252'
        return real_open(*args,**kwargs)
    monkeypatch.setattr(gzip,'open',cp1252_default)
    with pytest.raises(UnicodeDecodeError):
        CcCedict()  # The real upstream bug, not a fake initialization exception.
    dictionary._load.cache_clear()
    try:
        full=dictionary.get_dictionary()
        assert full is not None and len(full.get_entries())>100000
        assert 'coffee' in ' '.join(full.get_entry('咖啡')['definitions'])
        assert dictionary.dictionary_status().ready
    finally:
        dictionary._load.cache_clear()


def test_initialization_failure_is_logged_and_actionable(monkeypatch,caplog):
    dictionary._load.cache_clear()
    def unavailable(*args,**kwargs):
        raise FileNotFoundError('missing bundled dataset fixture')
    monkeypatch.setattr(gzip,'open',unavailable)
    try:
        status=dictionary.dictionary_status()
        assert not status.ready and 'FileNotFoundError' in status.error
        assert 'requirements.txt' in status.message and status.interpreter in status.message
        assert 'initialization failed' in caplog.text
        assert 'missing bundled dataset fixture' in caplog.text
    finally:
        dictionary._load.cache_clear()


def test_real_phrase_segmentation_and_traditional_subsets():
    assert [w for w,_ in gloss.key_vocabulary('我喜欢咖啡')]==['我','喜欢','咖啡']
    assert [w for w,_ in gloss.key_vocabulary('我喜歡咖啡')]==['我','喜歡','咖啡']
    result=gloss.lookup_meaning('免治牛肉石頭飯')
    assert result.text and 'beef' in result.text.lower()
    assert 'not a fluent' in result.note


def test_starter_words_remain_usable_when_full_dictionary_is_unavailable(monkeypatch):
    monkeypatch.setattr(gloss,'_cedict',lambda:None)
    gloss._entry.cache_clear()
    try:
        assert [w for w,_ in gloss.key_vocabulary('我喜欢咖啡')]==['我','喜欢','咖啡']
        result=gloss.lookup_meaning('我喜欢咖啡')
        assert 'coffee' in result.text.lower() and 'limited' in result.source
    finally:
        gloss._entry.cache_clear()


def test_eat_has_an_offline_chinese_equivalent_without_translator(monkeypatch):
    from deep_translator import GoogleTranslator
    def network_forbidden(*args,**kwargs):
        pytest.fail('Offline English lookup must not contact an online translator')
    monkeypatch.setattr(GoogleTranslator,'translate',network_forbidden)
    result=search.search_english('eat')
    first=result.groups[0][0]
    assert (first.hanzi,first.pinyin)==('吃','chī')
    assert 'eat' in first.meaning and result.source=='CC-CEDICT'


def test_english_pagination_discloses_and_reaches_all_results():
    first=search.search_english('eat',page_size=3)
    assert first.has_more and first.total>first.shown
    keys=[]
    page=0
    while True:
        result=search.search_english('eat',page=page,page_size=3)
        keys.extend(c.key for c in result.groups[0])
        if not result.has_more: break
        page+=1
        assert page<200
    assert len(set(keys))==len(keys)==first.total


def test_unmarked_ma_has_all_five_tone_groups_and_definitions():
    result=search.search_pinyin('ma')
    for tone,word,meaning in [(1,'妈','mother'),(2,'麻','hemp'),(3,'马','horse'),(4,'骂','scold'),(5,'吗','question')]:
        assert any(c.hanzi==word and meaning in c.meaning.lower() for c in result.groups[tone-1])
    assert result.total>=sum(map(len,result.groups))


@pytest.mark.parametrize('query,tone',[('ma1',1),('mā',1),('má',2),('ma3',3),('mǎ',3),('mà',4),('ma5',5),('ma0',5)])
def test_numbered_and_accented_pinyin_are_tone_specific(query,tone):
    result=search.search_pinyin(query)
    assert result.groups[tone-1]
    assert all(not group for i,group in enumerate(result.groups) if i!=tone-1)


def test_umlaut_and_multi_syllable_pinyin():
    one={c.key for g in search.search_pinyin('lü4').groups for c in g}
    two={c.key for g in search.search_pinyin('lv4').groups for c in g}
    assert one==two and one
    assert any(c.hanzi=='你好' for c in search.search_pinyin('ni3 hao3').groups[2])


def test_pinyin_candidate_preserves_an_alternate_reading_in_spotlight():
    import app
    lesson=app.prepare_lesson('吗',meaning='Used in morphine',reading='ma3',provenance='CC-CEDICT lookup')
    assert lesson['choices']==[('吗\nmǎ','0:3')]
    assert 'mǎ' in app._target_panel('吗','0','ma3')[0]
    assert get_syllables('吗','ma3')[0].expected_tone==3


def test_tiny_red_preprocessing_upscales_and_preserves_original():
    image=Image.open(FIXTURES/'synthetic-small-red-traditional.png')
    before=image.tobytes()
    variants=list(ocr.preprocess(image))
    assert image.tobytes()==before
    assert any(name.startswith('upscaled') and prepared.height>=image.height*2 for name,prepared in variants)
    assert any(name=='red-text contrast' for name,_ in variants)


@pytest.mark.parametrize('name,expected',[
    ('synthetic-small-red-traditional.png','免治牛肉石頭飯'),
    ('synthetic-clean-chinese.png','我喜欢咖啡'),
])
def test_real_packaged_ocr_on_committed_fixtures(name,expected):
    result=ocr.recognize_image(Image.open(FIXTURES/name))
    assert result.best.text==expected
    assert result.best.engine=='RapidOCR' and result.best.score is not None


def test_low_confidence_ocr_is_not_accepted(monkeypatch):
    from types import SimpleNamespace
    import pytesseract
    monkeypatch.setattr(ocr,'_rapidocr',lambda:lambda image:SimpleNamespace(txts=['不存在的猜测'],scores=[.3]))
    monkeypatch.setattr(pytesseract,'get_languages',lambda config:[])
    with pytest.raises(RuntimeError,match='No reliable Chinese text'):
        ocr.recognize_image(Image.open(FIXTURES/'synthetic-small-red-traditional.png'))


def test_integer_stereo_is_normalized_before_mixing():
    samples=np.tile(np.array([[16384,-8192]],dtype=np.int16),(16000,1))
    normalized=audio_for_asr((16000,samples))
    assert normalized.dtype==np.float32 and normalized.shape==(16000,)
    assert np.allclose(normalized,.125)


@pytest.mark.parametrize('audio,message',[
    (None,'Record'), ((16000,np.zeros(16000)),'No usable speech'),
    ((16000,np.ones(16000*61)*.1),'60 seconds'),
    ((16000,np.full(16000,np.nan)),'invalid'),
])
def test_asr_bad_audio_never_becomes_a_transcript(audio,message):
    with pytest.raises(ValueError,match=message): audio_for_asr(audio)


def test_asr_resampling_keeps_duration():
    assert len(audio_for_asr((8000,np.ones(8000,dtype=np.float32)*.1)))==16000


def test_sentence_variants_and_punctuation_are_not_false_word_errors():
    result=compare_transcript('我喜歡咖啡！','我喜欢咖啡。')
    assert result.matches
    html,choices=comparison_view('我喜歡咖啡！','我喜欢咖啡。')
    assert not choices and 'does not verify pronunciation' in html


def test_missing_and_replaced_words_point_to_original_character_indices():
    missing=compare_transcript('我喜欢咖啡','我咖啡')
    assert missing.flags=={1:'possible missing word',2:'possible missing word'}
    replaced=compare_transcript('我喜欢咖啡','我喜欢茶')
    assert set(replaced.flags)=={3,4}
    html,choices=comparison_view('我喜欢咖啡','我喜欢茶')
    assert [index for _,index in choices]==['3','4']
    assert 'recognition can also make mistakes' in html and 'not detected tone' in html


def test_extra_recognized_words_are_shown_without_blame_on_target_characters():
    result=compare_transcript('我喜欢咖啡','我很喜欢咖啡')
    assert not result.flags and result.additions==('很',)


def test_no_transcript_has_no_fake_grade_and_html_is_escaped():
    with pytest.raises(ValueError,match='No Chinese transcript'):
        compare_transcript('你好','')
    html,_=comparison_view('你好','<script>你好</script>')
    assert '<script>' not in html and '&lt;script&gt;' in html


def test_rare_dictionary_candidates_are_still_learnable_hanzi():
    from hanpi_core.text import clean_hanzi
    import app
    assert clean_hanzi('𠯪')=='𠯪'
    lesson=app.prepare_lesson('𠯪',reading='dai3')
    assert lesson['choices']==[('𠯪\ndǎi','0:3')]


def test_saved_alternate_dictionary_reading_survives_reopen(monkeypatch,tmp_path):
    from hanpi_core.library import save_entry
    import app
    monkeypatch.setenv('HANPI_LIBRARY_PATH',str(tmp_path/'readings.sqlite3'))
    saved=save_entry('word','吗','Used in morphine',reading='ma3')
    assert saved.written_pinyin=='mǎ'
    restored=app.prepare_lesson('吗',saved.id)
    assert restored['choices']==[('吗\nmǎ','0:3')]


@pytest.mark.parametrize('previous',['','My own meaning'])
def test_online_failure_keeps_offline_results_or_user_meaning(monkeypatch,previous):
    import app
    def offline(text):
        raise RuntimeError('Online provider unavailable')
    monkeypatch.setattr(app,'translate_online',offline)
    text,note,notice=app._translate_phrase('我喜欢咖啡',previous)
    assert text==previous if previous else 'coffee' in text.lower()
    assert 'Offline dictionary results remain available' in notice
