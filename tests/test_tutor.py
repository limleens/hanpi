"""Spoken coaching must follow available evidence and actual next actions."""
import numpy as np
from types import SimpleNamespace

import app
from hanpi_core.tutor import TutorCue,practice_cue,phrase_cue
from hanpi_ui.tutor import tutor_view


def test_matched_cue_offers_next_character_or_phrase_without_a_perfect_grade():
    cue=practice_cue(4,4,True,'蒜')
    assert 'Next character' in cue.text and 'whole phrase' in cue.text
    assert cue.mood=='happy' and not cue.example
    assert 'perfect' not in cue.text.lower()


def test_correction_speaks_the_observed_shape_and_correct_target():
    cue=practice_cue(4,2,True,'蒜')
    assert 'pitch rose' in cue.text and 'start high, then drop' in cue.text
    assert cue.example=='蒜' and cue.mood=='guide'


def test_unclear_and_third_tones_are_not_false_errors():
    assert 'clearer pitch' in practice_cue(4,None,True,'蒜').text
    assert 'Third tones can stay low' in practice_cue(3,1,True,'马').text
    assert 'aren’t graded' in practice_cue(5,1,True,'吗').text


def test_sentence_cue_does_not_claim_correct_tones_or_missing_highlights():
    assert 'I heard the phrase' in phrase_cue('你好','你好').text
    assert 'highlighted word' in phrase_cue('我喜欢咖啡','我喜欢茶').text
    cue=phrase_cue('我喜欢咖啡','我很喜欢咖啡')
    assert 'extra words' in cue.text and 'highlight' not in cue.text


def test_tutor_caption_is_escaped_and_original_asset_is_accessible():
    html=tutor_view(TutorCue('<script>alert(1)</script>'))
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert 'aria-live="polite"' in html and '<svg' in html


def test_similar_transcript_spellings_do_not_invent_extra_words():
    cue=phrase_cue('蒜香烧肉','算想烧肉')
    assert 'sound similar' in cue.text and 'extra words' not in cue.text
    assert cue.example=='蒜香烧肉'


def test_practice_ui_cue_uses_actual_tone_evidence_once(monkeypatch):
    calls=[]
    monkeypatch.setattr(app,'_transcribe',lambda audio:('算了',''))
    monkeypatch.setattr(app,'analyze_tone',lambda audio:(calls.append(audio) or SimpleNamespace(detected=2,times=np.array([]),semitones=np.array([]))))
    feedback,_,heard,matched,cue=app._practice_result(object(),'蒜','0',True,with_cue=True)
    assert heard=='算了' and not matched and len(calls)==1
    assert 'pitch rose' in cue.text and 'start high, then drop' in cue.text
    assert 'Syllable matches!' in feedback
    assert 'Good try' not in feedback  # dialogue supplies advice once, not twice
