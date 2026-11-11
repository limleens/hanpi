"""Speech-to-text evidence stays separate from experimental pitch evidence."""
from types import SimpleNamespace

import numpy as np
import pytest

import app
from hanpi_core.comparison import compare_transcript, comparison_view, transcript_breakdown


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
