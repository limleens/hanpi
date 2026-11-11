"""State and error paths behind the mobile Results → Spotlight journey."""
import asyncio
from types import SimpleNamespace

import numpy as np
import pytest

import app
from hanpi_core import gloss, voice
from hanpi_core.library import get_entry, save_entry
from hanpi_ui.presentation import character_choices, character_styles, spotlight


def test_shared_lesson_keeps_all_characters_and_dictionary_provenance():
    lesson = app.prepare_lesson('我喜欢咖啡' * 12)
    assert len(lesson['choices']) == 60
    assert lesson['text'] == '我喜欢咖啡' * 12
    assert 'coffee' in lesson['meaning']
    assert 'not a fluent' in lesson['note']
    assert [word for _, word in lesson['words']][:3] == ['我', '喜欢', '咖啡']


def test_input_does_not_implicitly_translate_english(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Typing must not send a translation request')
    monkeypatch.setattr(app, 'translate_to_chinese', forbidden)
    with pytest.raises(ValueError, match='explicitly translate'):
        app.prepare_lesson('coffee')


def test_saved_meaning_only_follows_the_same_phrase(monkeypatch, tmp_path):
    monkeypatch.setenv('HANPI_LIBRARY_PATH', str(tmp_path / 'saved.sqlite3'))
    saved = save_entry('sentence', '咖啡', 'My coffee note')
    restored = app.prepare_lesson('咖啡', saved.id)
    assert restored['meaning'] == 'My coffee note'
    assert restored['saved_id'] == str(saved.id)
    changed = app.prepare_lesson('你好', saved.id)
    assert changed['meaning'] == 'Hello'
    assert changed['saved_id'] is None


def test_character_choices_align_pinyin_and_preserve_sandhi():
    assert character_choices('你好') == [('你\nní', '0:2'), ('好\nhǎo', '1:3')]
    html, speech = spotlight('你好', '0')
    assert 'nǐ → spoken ní' in html
    assert speech == '你好'
    assert spotlight('你好', '1')[1] == '好'
    assert spotlight('你好', '-1')[1] == '你好'
    assert 'input[value$=":2"]' in character_styles()


@pytest.mark.parametrize('detected,expected_count', [(4, 1), (1, 0), (None, 0)])
def test_only_matching_isolated_tones_increment_saved_practice(monkeypatch, tmp_path, detected, expected_count):
    monkeypatch.setenv('HANPI_LIBRARY_PATH', str(tmp_path / 'practice.sqlite3'))
    saved = save_entry('sentence', '骂', 'To scold')
    result = SimpleNamespace(detected=detected, times=np.array([]), semitones=np.array([]), reason='Synthetic test evidence')
    monkeypatch.setattr(app, 'analyze_tone', lambda audio: result)
    feedback, chart, _ = app._assess_and_track(object(), '骂', '0', False, saved.id)
    assert get_entry(saved.id).practice_count == expected_count
    assert 'consonants' in feedback and 'whole-sentence' in feedback
    assert '100%' not in feedback
    if detected is None:
        assert "Couldn't judge" in feedback
    elif detected == 4:
        assert 'shape looks close' in feedback
    else:
        assert "Let's shape" in feedback


def test_invalid_selection_cannot_grade_the_last_character():
    message, chart, transcript = app._assess(None, '你好', '-1')
    assert message == 'Choose a character first.'
    assert chart is None and transcript == ''


def test_silent_or_missing_recording_is_not_a_success():
    feedback, chart, _ = app._assess(None, '骂', '0')
    assert "Couldn't judge" in feedback and 'Record' in feedback
    assert chart is None


def test_neural_failure_returns_browser_fallback_only_after_listen(monkeypatch):
    async def unavailable(*args, **kwargs):
        raise RuntimeError('Natural voice is temporarily unavailable.')
    monkeypatch.setattr(app, 'synthesize_neural', unavailable)
    path, message, fallback = asyncio.run(app._listen('你好', voice.DEFAULT_VOICE, 1, 'Natural voice (online)'))
    assert path is None and fallback == '你好'
    assert 'browser Mandarin voice' in message


def test_browser_mode_never_calls_neural_provider(monkeypatch):
    async def forbidden(*args, **kwargs):
        pytest.fail('Browser mode must not contact neural TTS')
    monkeypatch.setattr(app, 'synthesize_neural', forbidden)
    path, message, fallback = asyncio.run(app._listen('咖啡', voice.DEFAULT_VOICE, 1.25, 'Browser voice'))
    assert path is None and fallback == '咖啡'
    assert 'device' in message
    assert voice._rate(1.25) == '+25%'


def test_tts_protocol_errors_are_converted_to_fallback_and_partial_audio_removed(monkeypatch, tmp_path):
    import edge_tts
    from edge_tts.exceptions import NoAudioReceived
    class NoAudio:
        def __init__(self, *args, **kwargs):
            pass
        async def save(self, path):
            from pathlib import Path
            Path(path).write_bytes(b'partial')
            raise NoAudioReceived('Provider did not return audio')
    monkeypatch.setattr(edge_tts, 'Communicate', NoAudio)
    monkeypatch.setattr(voice, '_CACHE_DIR', tmp_path)
    with pytest.raises(RuntimeError, match='temporarily unavailable'):
        asyncio.run(voice.synthesize_neural('你好'))
    assert list(tmp_path.glob('*.mp3')) == []


def test_optional_whisper_missing_is_actionable(monkeypatch):
    monkeypatch.setattr(app.importlib.util, 'find_spec', lambda name: None)
    text, message = app._transcribe((16000, np.zeros(16000)))
    assert text == '' and 'Type or Scan' in message and 'requirements-asr.txt' in message


def test_english_translation_is_explicit_and_directional(monkeypatch):
    from deep_translator import GoogleTranslator
    calls = []
    def translate(self, text):
        calls.append((self.source, self.target, text))
        return '咖啡'
    monkeypatch.setattr(GoogleTranslator, 'translate', translate)
    assert gloss.translate_to_chinese('coffee') == '咖啡'
    assert calls == [('en', 'zh-CN', 'coffee')]
    lesson = app.prepare_lesson('咖啡', meaning='coffee')
    assert lesson['meaning'] == 'coffee' and lesson['note'].startswith('Online translation')


def test_unknown_vocabulary_is_not_invented(monkeypatch):
    monkeypatch.setattr(gloss, '_exact', lambda word: '')
    assert gloss.key_vocabulary('汉字') == []
