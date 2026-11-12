"""Conservative speech detection and endpoint trimming; never word alignment."""
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import numpy as np

RATE = 16000
VAD_PATH = Path(__file__).parent / 'assets' / 'silero_vad_v5.onnx'
VAD_SHA256 = '6b99cbfd39246b6706f98ec13c7c50c6b299181f2474fa05cbc8046acc274396'
NO_SPEECH_NOTICE = 'I couldn’t catch clear speech. Say it once, then stop.'


class NoSpeechError(ValueError):
    """The recording contains no sufficiently clear speech activity."""


@dataclass(frozen=True)
class SpeechWindow:
    samples: np.ndarray
    start: int
    end: int
    regions: tuple[tuple[int, int], ...]
    original_samples: int


@lru_cache(maxsize=1)
def detector_config():
    import sherpa_onnx
    if not VAD_PATH.is_file() or sha256(VAD_PATH.read_bytes()).hexdigest() != VAD_SHA256:
        raise RuntimeError('The bundled speech detector is missing or damaged. Restore hanpi_core/assets from the repository.')
    return sherpa_onnx.VadModelConfig(
        silero_vad=sherpa_onnx.SileroVadModelConfig(
            model=str(VAD_PATH), threshold=.35, min_speech_duration=.064,
            min_silence_duration=.20, max_speech_duration=65),
        sample_rate=RATE, num_threads=1, provider='cpu')


def _regions(samples):
    import sherpa_onnx
    # A detector owns recurrent state: never share it between recordings/users.
    vad = sherpa_onnx.VoiceActivityDetector(detector_config(), buffer_size_in_seconds=70)
    padded = np.pad(samples, (0, RATE // 2))
    for position in range(0, len(padded), 512):
        vad.accept_waveform(padded[position:position + 512])
    vad.flush()
    found = []
    while not vad.empty():
        part = vad.front
        start, end = max(0, part.start), min(len(samples), part.start + len(part.samples))
        if start < end:
            found.append((start, end))
        vad.pop()
    return tuple(found)


def _stationary_tone(samples):
    """Reject obvious steady electronic tones, not ordinary voiced harmonics."""
    if len(samples) < RATE // 4:
        return False
    power = np.abs(np.fft.rfft(samples * np.hanning(len(samples)))) ** 2
    frequencies = np.fft.rfftfreq(len(samples), 1 / RATE)
    power[frequencies < 65] = 0
    total = float(power.sum())
    if total <= 1e-12:
        return True
    peak = frequencies[int(np.argmax(power))]
    return float(power[np.abs(frequencies - peak) < 12].sum()) / total > .985


def prepare_speech(samples):
    """Trim surrounding non-speech; retain all internal pauses and repetitions.

    320 ms pre-roll protects unvoiced Mandarin initials. 180 ms post-roll
    protects final consonants/vowel tails. This does not remove speech words,
    infer how many words were said, or collapse duplicate ASR text.
    """
    source = np.asarray(samples, dtype=np.float32)
    if source.ndim != 1 or not len(source) or not np.isfinite(source).all():
        raise ValueError('Provide a finite, mono recording.')
    centered = np.ascontiguousarray(source - np.mean(source))
    if float(np.sqrt(np.mean(centered.astype(np.float64) ** 2))) < .00005 or _stationary_tone(centered):
        raise NoSpeechError(NO_SPEECH_NOTICE)
    regions = _regions(centered)
    if not regions:
        raise NoSpeechError(NO_SPEECH_NOTICE)
    start = max(0, regions[0][0] - int(.32 * RATE))
    end = min(len(source), regions[-1][1] + int(.18 * RATE))
    return SpeechWindow(centered[start:end], start, end, regions, len(source))
