"""Explicitly prepare the local multilingual Whisper model before the demo."""
from pathlib import Path
import argparse
import os
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
parser=argparse.ArgumentParser()
parser.add_argument('--backend',choices=['sherpa-onnx','faster-whisper'],default=None)
parser.add_argument('--model',choices=['tiny','base','small'],default=None)
args=parser.parse_args()
if args.backend: os.environ['HANPI_ASR_BACKEND']=args.backend
if args.model:
    os.environ['HANPI_ASR_MODEL']=args.model
    os.environ.setdefault('HANPI_ASR_BACKEND','faster-whisper')
from hanpi_core.asr import prepare_model,backend_name
print(f'Preparing {backend_name()} with {sys.executable}. Default Mandarin model download is about 75 MB; optional Whisper base is about 150 MB.',flush=True)
print('Prepared:',prepare_model(),flush=True)
