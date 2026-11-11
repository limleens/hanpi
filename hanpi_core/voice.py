"""Optional human-sounding Mandarin reference audio.

Uses Edge's online neural voices through edge-tts. This is NOT offline.
Audio is generated only after an explicit user action. Browser TTS stays
available separately when this third-party service cannot be reached.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
import tempfile
import time
from uuid import uuid4

from .text import clean_hanzi

VOICES = {
    "Xiaoxiao · warm & clear": "zh-CN-XiaoxiaoNeural",
    "Yunxi · conversational": "zh-CN-YunxiNeural",
    "Xiaoyi · bright & friendly": "zh-CN-XiaoyiNeural",
}
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
TTS_MAX_CHARACTERS = 300
_CACHE_DIR = Path(tempfile.gettempdir()) / "hanpi_neural_audio"


def prepare_text(text: str) -> str:
    """Never truncate content silently. Reject excessive service requests."""
    phrase = (text or "").strip()
    chars = clean_hanzi(phrase)
    if not chars:
        raise ValueError("Upload a photo or enter Hanzi before playing audio.")
    if len(chars) > TTS_MAX_CHARACTERS:
        raise ValueError(
            f"Select a shorter passage (up to {TTS_MAX_CHARACTERS} Hanzi) "
            "for natural voice playback. OCR and pinyin retain the full passage."
        )
    return phrase


def _rate(rate: float) -> str:
    speed = float(rate)
    if not 0.65 <= speed <= 1.20:
        raise ValueError("Voice speed must be between 0.65x and 1.20x.")
    return f"{round((speed - 1.0) * 100):+d}%"


def _clear_old_files() -> None:
    """Clean old generated samples; don't delete files still in use."""
    now = time.time()
    for f in _CACHE_DIR.glob("*.mp3"):
        try:
            if now - f.stat().st_mtime > 86400:
                f.unlink(missing_ok=True)
        except OSError:
            pass


async def synthesize_neural(text: str, voice: str = DEFAULT_VOICE, rate: float = 0.90) -> str:
    """Create one MP3 per request, returned as a Gradio audio output path."""
    phrase = prepare_text(text)
    if voice not in VOICES.values():
        raise ValueError("Choose a listed Mandarin voice.")
    speed = _rate(rate)
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError("Install edge-tts for online neural speech.") from exc

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _clear_old_files()
    path = _CACHE_DIR / f"{uuid4().hex}.mp3"
    try:
        client = edge_tts.Communicate(phrase, voice=voice, rate=speed)
        await asyncio.wait_for(client.save(str(path)), timeout=35)
        if path.stat().st_size < 100:
            raise RuntimeError("Voice provider returned no usable audio.")
        return str(path)
    except (OSError, RuntimeError, asyncio.TimeoutError, ConnectionError) as exc:
        path.unlink(missing_ok=True)
        raise RuntimeError(
            "Natural voice is temporarily unavailable. "
            "Use the built-in browser voice instead."
        ) from exc


def voice_options() -> list[tuple[str, str]]:
    return [(label, value) for label, value in VOICES.items()]
