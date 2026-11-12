"""Explicitly prepare local recognition; no recording is uploaded."""
from pathlib import Path
import argparse
import os
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
parser=argparse.ArgumentParser()
parser.add_argument('--backend',choices=['sherpa-onnx','faster-whisper'],default=None)
parser.add_argument('--model',choices=['tiny','base','small'],default=None)
parser.add_argument('--profile',choices=['accurate','compact'],default=None,help='SenseVoice (~163 MB download) or the original compact Zipformer (~75 MB)')
args=parser.parse_args()
if args.backend: os.environ['HANPI_ASR_BACKEND']=args.backend
if args.profile: os.environ['HANPI_ASR_PROFILE']=args.profile
if args.model:
    os.environ['HANPI_ASR_MODEL']=args.model
    os.environ.setdefault('HANPI_ASR_BACKEND','faster-whisper')
from hanpi_core.asr import prepare_model,backend_name
print(f'Preparing {backend_name()} with {sys.executable}. Improved SenseVoice download is about 163 MB; --profile compact retains the original 75 MB model. Speech filtering is bundled.',flush=True)
print('Prepared:',prepare_model(),flush=True)
