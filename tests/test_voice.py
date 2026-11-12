"""Tests for Mandarin neural voice without making network requests."""
import asyncio
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from hanpi_core import voice


def test_prepare_text_preserves_sentence_punctuation():
    assert voice.prepare_text("你好，世界！") == "你好，世界！"


def test_tts_rejects_blank_or_excessive_length():
    with pytest.raises(ValueError):
        voice.prepare_text("English only")
    with pytest.raises(ValueError):
        voice.prepare_text("汉" * (voice.TTS_MAX_CHARACTERS + 1))


def test_rate_and_voice_validation():
    assert voice._rate(0.90) == "-10%"
    assert voice._rate(1.0) == "+0%"
    with pytest.raises(ValueError):
        voice._rate(0.2)


def test_neural_synthesis_output(monkeypatch, tmp_path):
    class FakeCommunicate:
        def __init__(self, phrase, voice, rate):
            assert phrase == "你好，世界！"
            assert voice == "zh-CN-XiaoxiaoNeural"
            assert rate == "-10%"

        async def save(self, filename):
            Path(filename).write_bytes(b"ID3" + b"\0" * 150)

    monkeypatch.setitem(sys.modules, "edge_tts", SimpleNamespace(Communicate=FakeCommunicate))
    monkeypatch.setattr(voice, "_CACHE_DIR", tmp_path)
    result = asyncio.run(voice.synthesize_neural("你好，世界！", rate=0.90))
    assert Path(result).exists()
    assert Path(result).stat().st_size > 100

    with pytest.raises(ValueError):
        asyncio.run(voice.synthesize_neural("你好", voice="unapproved-voice"))


def test_remote_phone_mode_requires_auth(monkeypatch):
    import app
    monkeypatch.setenv("HANPI_SHARE", "1")
    monkeypatch.delenv("HANPI_DEMO_USER", raising=False)
    monkeypatch.delenv("HANPI_DEMO_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="HANPI_DEMO_USER"):
        app.launch_app()


def test_branded_login_keeps_configured_authentication(monkeypatch):
    import app
    import secrets
    from types import SimpleNamespace
    password=secrets.token_urlsafe(20)
    monkeypatch.setenv('HANPI_SHARE','1')
    monkeypatch.setenv('HANPI_DEMO_USER','qa-demo')
    monkeypatch.setenv('HANPI_DEMO_PASSWORD',password)
    monkeypatch.setattr(app,'build_app',lambda:SimpleNamespace(launch=lambda **kwargs:kwargs))
    settings=app.launch_app()
    assert settings['auth']==('qa-demo',password)
    assert 'hanpi-welcome' in settings['auth_message']
    assert password not in settings['auth_message']
