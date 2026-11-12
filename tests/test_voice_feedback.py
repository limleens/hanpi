"""Speech-to-text evidence stays separate from experimental pitch evidence."""
from types import SimpleNamespace

import numpy as np
import pytest

import app
from hanpi_core.comparison import compare_transcript, comparison_view, transcript_breakdown, readings_match, match_isolated_syllable


def pitch(monkeypatch, tone):
    monkeypatch.setattr(app, 'analyze_tone', lambda audio: SimpleNamespace(
        detected=tone, times=np.array([]), semitones=np.array([])))


@pytest.mark.parametrize('target,heard', [('马', '马'), ('燒', '烧。')])
def test_word_match_displays_actual_transcript_and_pinyin(monkeypatch, target, heard):
    pitch(monkeypatch, app.get_syllables(target)[0].expected_tone)
    monkeypatch.setattr(app, '_transcribe', lambda audio: (heard, ''))
    feedback, _, transcript, matched = app._practice_result(object(), target, '0', True)
    assert transcript == heard and f'**You said:** {heard}' in feedback
    assert 'Words match!' in feedback and '**Target:**' in feedback
    assert app.get_syllables(heard)[0].written_pinyin in feedback
    assert '**Tone shape:**' in feedback and matched


def test_actual_heard_word_is_not_replaced_by_expected_word(monkeypatch):
    pitch(monkeypatch, 3)
    monkeypatch.setattr(app, '_transcribe', lambda audio: ('猫', ''))
    feedback, _, transcript, matched = app._practice_result(object(), '马', '0', True)
    assert transcript == '猫' and '**You said:** 猫 · māo' in feedback
    assert '**Target:** 马 · mǎ' in feedback
    assert 'Words match!' not in feedback and not matched


def test_transcript_tone_and_measured_pitch_are_separate(monkeypatch):
    pitch(monkeypatch, 4)
    monkeypatch.setattr(app, '_transcribe', lambda audio: ('马', ''))
    feedback, _, _, matched = app._practice_result(object(), '妈', '0', True)
    assert '**You said:** 马 · mǎ' in feedback
    assert '**Tone shape:** falling (fourth tone)' in feedback
    assert '**Target:** level (first tone)' in feedback
    assert 'Words match!' not in feedback and not matched


def test_asr_failure_does_not_fake_a_word_match_or_hide_pitch(monkeypatch):
    pitch(monkeypatch, 4)
    monkeypatch.setattr(app, '_transcribe', lambda audio: ('', 'No speech'))
    feedback, _, transcript, matched = app._practice_result(object(), '骂', '0', True)
    assert 'couldn’t make out' in feedback and 'falling (fourth tone)' in feedback
    assert not matched and transcript == '' and 'Words match!' not in feedback


def test_missing_model_is_not_mislabeled_as_bad_speech(monkeypatch, caplog):
    pitch(monkeypatch, 4)
    monkeypatch.setattr(app, '_transcribe', lambda audio: ('', 'The Mandarin model is not ready. Run scripts/prepare_asr.py.'))
    feedback, _, _, matched = app._practice_result(object(), '骂', '0', True)
    assert 'Voice recognition isn’t ready' in feedback and not matched
    assert 'scripts/prepare_asr.py' in caplog.text


def test_pitch_failure_does_not_erase_real_transcript(monkeypatch):
    monkeypatch.setattr(app, '_transcribe', lambda audio: ('马', ''))
    def fail(audio):
        raise ValueError('Not enough voiced sound.')
    monkeypatch.setattr(app, 'analyze_tone', fail)
    feedback, chart, transcript, matched = app._practice_result(object(), '马', '0', True)
    assert '**You said:** 马' in feedback and 'Not enough voiced sound.' in feedback
    assert chart is None and transcript == '马' and not matched


def test_sentence_breakdown_uses_actual_aligned_replacement():
    result = compare_transcript('我喜欢咖啡', '我喜欢茶')
    assert result.heard_parts[3] == result.heard_parts[4] == '茶'
    assert result.target_parts[3] == '咖啡'
    html = transcript_breakdown('我喜欢咖啡', '我喜欢茶', '3')
    assert '咖啡 · kā fēi' in html and '茶 · chá' in html
    assert 'Pinyin follows the transcript' in html


def test_missing_word_and_insertions_do_not_shift_target_breakdown():
    result = compare_transcript('我喜欢咖啡', '我很咖啡')
    assert result.heard_parts[3] == '咖' and result.heard_parts[4] == '啡'
    html = transcript_breakdown('我喜欢咖啡', '我咖啡', 1)
    assert 'Not heard in this recording' in html


def test_matched_sentence_words_are_also_available_for_spotlight():
    html, choices = comparison_view('你好', '你好', include_matches=True)
    assert 'Words match. Nice work!' in html
    assert [index for _, index in choices] == ['0', '1']
    assert '好 · hǎo' in transcript_breakdown('你好', '你好', 1)


def test_invalid_breakdown_has_no_invented_alignment():
    with pytest.raises(ValueError):
        transcript_breakdown('你好', '你', 9)


def test_word_breakdown_keeps_polyphonic_and_sandhi_context():
    assert '行 · háng' in transcript_breakdown('银行', '银行', 1)
    assert '你 · ní' in transcript_breakdown('你好', '你好', 0)


@pytest.mark.parametrize('expected,heard,match',[
    ('蒜','算',True),('蒜','算。',True),('香','乡',True),('蒜香烧肉','算乡烧肉',True),
    ('你好','泥好',True),('银行','银航',True),('蒜','酸',False),('妈','马',False),
    ('蒜','算算',False),('蒜','',False),('','算',False),('女','旅',False),
])
def test_reading_match_requires_same_syllables_and_tones(expected,heard,match):
    assert readings_match(expected,heard) is match


def test_user_suan_homophone_counts_as_success_with_matching_pitch(monkeypatch,tmp_path):
    from hanpi_core.library import save_entry,get_entry
    monkeypatch.setenv('HANPI_LIBRARY_PATH',str(tmp_path/'homophone.sqlite3'))
    saved=save_entry('word','蒜','garlic')
    pitch(monkeypatch,4)
    monkeypatch.setattr(app,'_transcribe',lambda audio:('算',''))
    feedback,_,transcript=app._assess_and_track(object(),'蒜','0',True,saved.id)
    assert 'Sounds match!' in feedback and '**You said:** 算 · suàn' in feedback
    assert '**Target:** 蒜 · suàn' in feedback and 'matches the target' in feedback
    assert 'may have misheard' not in feedback and 'Start high, then drop' not in feedback
    assert transcript=='算' and get_entry(saved.id).practice_count==1


@pytest.mark.parametrize('detected',[1,None])
def test_homophone_does_not_override_mismatched_or_unclear_pitch(monkeypatch,detected):
    pitch(monkeypatch,detected)
    monkeypatch.setattr(app,'_transcribe',lambda audio:('算',''))
    feedback,_,_,matched=app._practice_result(object(),'蒜','0',True)
    assert 'Sounds match!' in feedback and not matched
    assert 'matches the target' not in feedback


def test_homophone_uses_selected_polyphonic_reading(monkeypatch):
    pitch(monkeypatch,2)
    monkeypatch.setattr(app,'_transcribe',lambda audio:('航',''))
    assert app._practice_result(object(),'行','0',True,reading='hang2')[3]
    assert not app._practice_result(object(),'行','0',True,reading='xing2')[3]


def test_sentence_homophone_is_positive_without_claiming_matching_text():
    html,_=comparison_view('蒜香烧肉','算乡烧肉',include_matches=True)
    assert 'Same pronunciation, different characters.' in html
    assert not compare_transcript('蒜香烧肉','算乡烧肉').matches
    assert 'Word check, not a tone score' in html


@pytest.mark.parametrize('heard',['算了','蒜了','算儿','算兒','酸了','蒜啊','蒜呢','蒜吧','算嘛','蒜啦','算而','算二','蒜乐'])
def test_short_extra_endings_do_not_fail_isolated_practice(monkeypatch,heard):
    pitch(monkeypatch,4)
    monkeypatch.setattr(app,'_transcribe',lambda audio:(heard,''))
    feedback,_,transcript,matched=app._practice_result(object(),'蒜','0',True)
    assert 'Syllable matches!' in feedback and matched
    assert 'Extra ending ignored' in feedback
    assert f'**You said:** {heard}' in feedback and transcript==heard
    assert 'falling (fourth tone) — matches the target' in feedback


@pytest.mark.parametrize('heard',['算头','蒜人','算了吧','我来算了','算算','双了','了算',''])
def test_leniency_is_not_an_arbitrary_substring_match(heard):
    result=match_isolated_syllable('蒜',heard)
    assert not result.matches and result.ignored_ending==''


@pytest.mark.parametrize('detected',[1,None])
def test_extra_ending_does_not_fabricate_a_pitch_match(monkeypatch,detected):
    pitch(monkeypatch,detected)
    monkeypatch.setattr(app,'_transcribe',lambda audio:('算了',''))
    feedback,_,_,matched=app._practice_result(object(),'蒜','0',True)
    assert 'Syllable matches!' in feedback and not matched
    assert 'matches the target' not in feedback


def test_isolated_syllable_uses_acoustic_pitch_not_asr_spelling_tone(monkeypatch):
    pitch(monkeypatch,4)
    monkeypatch.setattr(app,'_transcribe',lambda audio:('酸',''))
    feedback,_,transcript,matched=app._practice_result(object(),'蒜','0',True)
    assert 'Syllable matches!' in feedback and matched
    assert '**You said:** 酸 · suān' in feedback and transcript=='酸'
    assert 'falling (fourth tone) — matches the target' in feedback
    assert not readings_match('蒜','酸')


def test_forgiving_match_keeps_polyphonic_selection_and_sandhi(monkeypatch):
    assert match_isolated_syllable('行','航了','hang2').matches
    assert not match_isolated_syllable('行','航了','xing2').matches
    pitch(monkeypatch,2)
    monkeypatch.setattr(app,'_transcribe',lambda audio:('泥了',''))
    feedback,_,_,matched=app._practice_result(object(),'你好','0',True)
    assert '**Target:** 你 · ní' in feedback and matched


def test_sentence_comparison_still_reports_extra_words():
    assert not match_isolated_syllable('我喜欢咖啡','我喜欢咖啡了').matches
    assert not readings_match('我喜欢咖啡','我喜欢咖啡了')
    assert compare_transcript('我喜欢咖啡','我喜欢咖啡了').additions==('了',)
