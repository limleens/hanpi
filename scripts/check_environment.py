"""Run using the exact interpreter used for app.py; no credentials are printed."""
from pathlib import Path
import argparse
import importlib.metadata
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hanpi_core.dictionary import dictionary_status
from hanpi_core.gloss import key_vocabulary

parser=argparse.ArgumentParser()
parser.add_argument('--strict',action='store_true')
parser.add_argument('--asr',action='store_true',help='Also verify the already-prepared local speech model; does not download it')
args=parser.parse_args()
status=dictionary_status()
versions={}
for name in ('gradio','pycccedict','rapidocr','onnxruntime','sherpa-onnx','opencc-python-reimplemented','faster-whisper'):
    try: versions[name]=importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError: versions[name]='NOT INSTALLED'
speech={}
if args.asr:
    from hanpi_core.asr import _model,backend_name
    try:
        _model()
        speech={'backend':backend_name(),'ready':True}
    except Exception as exc:
        speech={'ready':False,'error':str(exc)}
print(json.dumps(dict(speech=speech,interpreter=sys.executable,python=sys.version,packages=versions,
                     dictionary=status.__dict__,vocabulary=key_vocabulary('我喜欢咖啡')),ensure_ascii=False,indent=2))
required=['gradio','pycccedict','rapidocr','onnxruntime','sherpa-onnx','opencc-python-reimplemented']
if args.strict and (not status.ready or any(versions.get(name)=='NOT INSTALLED' for name in required) or (args.asr and not speech.get('ready')) or [word for word,_ in key_vocabulary('我喜欢咖啡')]!=['我','喜欢','咖啡']):
    sys.exit(1)
