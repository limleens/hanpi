"""Mandarin speech-to-text, not pronunciation or tone grading."""
from functools import lru_cache
from pathlib import Path
from math import gcd
import os
import logging

import numpy as np
from scipy.signal import resample_poly


def backend_name():
    backend=os.getenv('HANPI_ASR_BACKEND','sherpa-onnx')
    if backend not in ('sherpa-onnx','faster-whisper'):
        raise ValueError('HANPI_ASR_BACKEND must be sherpa-onnx or faster-whisper.')
    return backend


def model_name():
    name=os.getenv('HANPI_ASR_MODEL','base')
    if name not in ('tiny','base','small') and not Path(name).is_dir():
        raise ValueError('HANPI_ASR_MODEL must be tiny, base, small, or a local model directory.')
    return name


def cache_directory():
    return Path(os.getenv('HANPI_ASR_CACHE',str(Path(os.getenv('XDG_CACHE_HOME',str(Path.home()/'.cache')))/'hanpi-asr')))


def prepare_model():
    """Explicit one-time download; no microphone recording leaves the machine."""
    try:
        if backend_name()=='sherpa-onnx':
            from .speech_model import install
            location=install(cache_directory())
            _model.cache_clear()
            _model()
            return location
        from faster_whisper.utils import download_model
        name=model_name()
        cache_directory().mkdir(parents=True,exist_ok=True)
        location=name if Path(name).is_dir() else download_model(name,cache_dir=str(cache_directory()))
        _model.cache_clear()
        _model()
        return location
    except Exception as exc:
        logging.getLogger(__name__).exception('Mandarin model setup failed')
        raise RuntimeError(f'Mandarin model setup failed ({type(exc).__name__}). Run python scripts/prepare_asr.py in the same venv. '
                           'The default model downloads from the official GitHub release; optional Faster-Whisper uses Hugging Face. Check the console for the underlying error.') from exc


@lru_cache(maxsize=1)
def _model():
    try:
        if backend_name()=='sherpa-onnx':
            from .speech_model import load
            return load(cache_directory())
        from faster_whisper import WhisperModel
        return WhisperModel(model_name(),device='cpu',compute_type='int8',cpu_threads=min(4,os.cpu_count() or 1),
                            num_workers=1,download_root=str(cache_directory()),local_files_only=True)
    except ImportError as exc:
        raise RuntimeError('Install dependencies using the same Python as app.py: python -m pip install -r requirements.txt.') from exc
    except Exception as exc:
        raise RuntimeError('The Mandarin speech model is not ready. Use Prepare Mandarin speech model, '
                           'or run python scripts/prepare_asr.py once. Recordings stay local.') from exc


def audio_for_asr(audio):
    if audio is None:
        raise ValueError('Record a sentence first.')
    rate,data=audio
    if not 8000<=rate<=192000:
        raise ValueError('Unsupported recording rate. Use a normal WAV recording.')
    a=np.asarray(data)
    if a.ndim not in (1,2) or not a.size:
        raise ValueError('No usable audio samples were provided.')
    # Normalize integer stereo BEFORE mixing; otherwise writing clips the audio.
    if np.issubdtype(a.dtype,np.integer):
        a=a.astype(np.float32)/max(abs(np.iinfo(a.dtype).min),np.iinfo(a.dtype).max)
    else:
        a=a.astype(np.float32)
    if a.ndim==2:
        a=np.mean(a,axis=1)
    if not np.all(np.isfinite(a)):
        raise ValueError('The recording contains invalid audio samples.')
    duration=len(a)/rate
    if not .25<=duration<=60:
        raise ValueError('Record a sentence between 0.25 and 60 seconds. Nothing has been truncated.')
    if float(np.sqrt(np.mean(a.astype(np.float64)**2)))<.002:
        raise ValueError('No usable speech was detected. Move closer to the microphone and try again.')
    if rate!=16000:
        divisor=gcd(rate,16000)
        a=resample_poly(a,16000//divisor,rate//divisor).astype(np.float32)
    return np.ascontiguousarray(a)


def transcribe(audio):
    samples=audio_for_asr(audio)
    if backend_name()=='sherpa-onnx':
        recognizer=_model()
        stream=recognizer.create_stream()
        stream.accept_waveform(16000,np.concatenate([samples,np.zeros(9600,dtype=np.float32)]))
        stream.input_finished()
        while recognizer.is_ready(stream):
            recognizer.decode_stream(stream)
        text=recognizer.get_result(stream).strip()
        if not text:
            raise ValueError('No clear Mandarin transcript was returned. Retry or enter a corrected transcript.')
        return text
    segments,_=_model().transcribe(samples,language='zh',beam_size=5,temperature=0,
                                   condition_on_previous_text=False,vad_filter=True,
                                   vad_parameters={'min_silence_duration_ms':500})
    # Never prime ASR with the target sentence: that would bias the comparison.
    text=''.join(s.text.strip() for s in segments if s.no_speech_prob<.6 and s.avg_logprob>-1.2).strip()
    if not text:
        raise ValueError('The model could not hear clear Mandarin. Listen back, retry, or enter a corrected transcript for comparison.')
    return text
