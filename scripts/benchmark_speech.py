"""Focused ASR regression, not an accuracy study or pronunciation grader.

Pass the official Zipformer test_wavs/0.wav, whose initial 对 is cropped at
0.42 seconds. Cases add synthetic noise or repeat that actual human crop.
No target is supplied to any decoder; repetitions in output are not removed.
"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from hanpi_core import asr,speech_model
from hanpi_core.comparison import readings_match

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--reference-wav',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
audio,rate=sf.read(args.reference_wav,dtype='float32')
if audio.ndim>1: audio=audio.mean(axis=1)
if rate!=16000: audio=resample_poly(audio,16000,rate).astype(np.float32)
word=audio[:6720]
rng=np.random.default_rng(17)
click=np.zeros(16000,dtype=np.float32);click[4000:4160]=.5*np.hanning(160)*rng.normal(size=160)
breath=np.zeros(16000,dtype=np.float32);breath[4000:12000]=.03*np.hanning(8000)*rng.normal(size=8000)
cases={
    'human-word':(word,'对'),
    'quiet-human-word':(word*.12,'对'),
    'surrounding-silence':(np.pad(word,(32000,48000)),'对'),
    'tap-before-word':(np.concatenate([click,np.zeros(16000),word,np.zeros(16000)]),'对'),
    'tap-after-word':(np.concatenate([word,np.zeros(16000),click]),'对'),
    'breath-after-word':(np.concatenate([word,np.zeros(16000),breath]),'对'),
    'word-with-hiss':(word+rng.normal(0,.002,len(word)),'对'),
    'two-real-attempts':(np.concatenate([word,np.zeros(16000),word]),'对对'),
    'silence':(np.zeros(32000),''),
    'hiss':(rng.normal(0,.015,32000),''),
    'tap':(click,''),
    'breath-like-noise':(breath,''),
    'electronic-tone':(.15*np.sin(2*np.pi*180*np.arange(32000)/16000),''),
    'dc-offset':(np.full(32000,.1),''),
}

def raw_decode(model,profile,samples):
    stream=model.create_stream()
    if profile=='compact':
        stream.accept_waveform(16000,np.concatenate([samples,np.zeros(9600,dtype=np.float32)]))
        stream.input_finished()
        while model.is_ready(stream):model.decode_stream(stream)
        return model.get_result(stream).strip()
    stream.accept_waveform(16000,samples);model.decode_stream(stream)
    return stream.result.text.strip()

results={}
for profile in ('compact','accurate'):
    os.environ['HANPI_ASR_PROFILE']=profile;asr._model.cache_clear()
    model=asr._model(profile)
    for filtered in (False,True):
        label=profile+('-speech-filtered' if filtered else '-raw')
        rows=[]
        for name,(samples,expected) in cases.items():
            start=time.monotonic();error=''
            try:
                text=asr.transcribe((16000,samples)) if filtered else raw_decode(model,profile,asr.audio_for_asr((16000,samples)))
            except ValueError as exc:
                text='';error=type(exc).__name__
            match=(readings_match(expected,text) if expected else not text.strip())
            row=dict(case=name,expected=expected,recognized=text,reading_sequence_matches=match,
                     seconds=round(time.monotonic()-start,3),abstention=error)
            rows.append(row)
            print(label,name,repr(text),match,flush=True)
        results[label]={'matched_cases':sum(row['reading_sequence_matches'] for row in rows),'total_cases':len(rows),'cases':rows}
report={'scope':'14 focused cases from one public human word crop plus synthetic noises; not representative ASR accuracy',
        'source_sha256':sha256(args.reference_wav.read_bytes()).hexdigest(),
        'source':'official sherpa-onnx Zipformer 14M test_wavs/0.wav, first 0.42 seconds',
        'raw_transcripts_preserved':True,'results':results}
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({key:(value['matched_cases'],value['total_cases']) for key,value in results.items()}))
