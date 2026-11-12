"""Actual bundled VAD on non-speech; deterministic endpoint/decoder regressions."""
import numpy as np
import pytest

import app
from hanpi_core import speech,asr


@pytest.mark.parametrize('kind',['silence','dc','hiss','click','breath','vibration'])
def test_background_sounds_do_not_become_speech(kind):
    rng=np.random.default_rng(15)
    audio=np.zeros(32000,dtype=np.float32)
    if kind=='dc': audio[:]=.1
    if kind=='hiss': audio=rng.normal(0,.015,32000).astype(np.float32)
    if kind=='click': audio[8000:8160]=.6*np.hanning(160)*rng.normal(size=160)
    if kind=='breath': audio[8000:16000]=.03*np.hanning(8000)*rng.normal(size=8000)
    if kind=='vibration': audio=.15*np.sin(2*np.pi*180*np.arange(32000)/16000)
    with pytest.raises(speech.NoSpeechError): speech.prepare_speech(audio)


def test_endpoint_trim_keeps_both_real_speech_regions_and_internal_pause(monkeypatch):
    monkeypatch.setattr(speech,'_regions',lambda audio:((16000,20000),(35000,40000)))
    rng=np.random.default_rng(5);audio=rng.normal(0,.05,64000).astype(np.float32)
    result=speech.prepare_speech(audio)
    assert result.start==10880 and result.end==42880
    assert result.regions==((16000,20000),(35000,40000))
    assert len(result.samples)==32000
    assert np.allclose(result.samples,(audio-audio.mean())[10880:42880])


def test_short_activity_is_not_trimmed_away(monkeypatch):
    monkeypatch.setattr(speech,'_regions',lambda audio:((4480,6720),))
    audio=np.random.default_rng(9).normal(0,.05,6720).astype(np.float32)
    result=speech.prepare_speech(audio)
    assert result.start==0 and result.end==len(audio)


def test_no_speech_gate_prevents_decoder_call(monkeypatch):
    def forbidden():pytest.fail('Non-speech must not reach the recognizer')
    monkeypatch.setattr(asr,'_model',forbidden)
    click=np.zeros(32000,dtype=np.float32);click[8000:8160]=.6*np.hanning(160)
    with pytest.raises(speech.NoSpeechError):asr.transcribe((16000,click))


def test_rejected_background_sound_never_gets_a_positive_tone_grade(monkeypatch):
    monkeypatch.setattr(app,'_transcribe',lambda audio:('',speech.NO_SPEECH_NOTICE))
    monkeypatch.setattr(app,'analyze_tone',lambda audio:pytest.fail('Noise is not a syllable'))
    feedback,figure,transcript,matched=app._practice_result(object(),'妈','0',True)
    assert 'clear speech' in feedback and not matched
    assert figure is None and transcript==''


def test_very_quiet_electronic_noise_cannot_receive_a_tone_grade(monkeypatch):
    monkeypatch.setattr(app,'analyze_tone',lambda audio:pytest.fail('Rejected audio must not be tone graded'))
    noise=.001*np.sin(2*np.pi*180*np.arange(32000)/16000)
    message,figure,transcript,matched=app._practice_result((16000,noise),'妈','0',True)
    assert 'clear speech' in message and not matched
    assert figure is None and transcript==''


def test_profile_validation_and_legacy_selection(monkeypatch,tmp_path):
    from hanpi_core.speech_model import MODEL_ID,ACCURATE_ID
    monkeypatch.setenv('HANPI_ASR_CACHE',str(tmp_path))
    monkeypatch.setenv('HANPI_ASR_PROFILE','auto')
    (tmp_path/MODEL_ID).mkdir()
    assert asr.engine_profile()=='compact'
    (tmp_path/ACCURATE_ID).mkdir()
    for name in ('model.int8.onnx','tokens.txt'):(tmp_path/ACCURATE_ID/name).touch()
    assert asr.engine_profile()=='accurate'
    monkeypatch.setenv('HANPI_ASR_PROFILE','unknown')
    with pytest.raises(ValueError):asr.engine_profile()


def test_automatic_profile_upgrade_does_not_reuse_an_incompatible_decoder(monkeypatch):
    from hanpi_core import speech_model
    monkeypatch.setenv('HANPI_ASR_BACKEND','sherpa-onnx')
    monkeypatch.setattr(speech_model,'load',lambda root:'compact-decoder')
    monkeypatch.setattr(speech_model,'load_accurate',lambda root:'accurate-decoder')
    asr._model.cache_clear()
    try:
        assert asr._model('compact')=='compact-decoder'
        assert asr._model('accurate')=='accurate-decoder'
        assert asr._model('compact')=='compact-decoder'
    finally:asr._model.cache_clear()
