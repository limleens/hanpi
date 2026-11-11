"""Pinned, compact Mandarin transducer from the official sherpa-onnx release."""
from hashlib import sha256
from pathlib import Path
import os
import shutil
import tarfile
import tempfile

import requests

MODEL_ID='sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23'
MODEL_URL=f'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{MODEL_ID}.tar.bz2'
# Pinned from the official HTTPS release artifact; never bypass a mismatch.
MODEL_SHA256='2cbd71b640d9c37d3784f29367333a4577b0398b62e9deeed418170b081cba8b'
FILES={'encoder':'encoder-epoch-99-avg-1.int8.onnx','decoder':'decoder-epoch-99-avg-1.int8.onnx',
       'joiner':'joiner-epoch-99-avg-1.int8.onnx','tokens':'tokens.txt'}


def digest(path):
    result=sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            result.update(chunk)
    return result.hexdigest()


def install(root):
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    target=root/MODEL_ID
    if all((target/name).is_file() for name in FILES.values()):
        return target
    archive=root/'mandarin-14m.tar.bz2'
    if not archive.is_file() or digest(archive)!=MODEL_SHA256:
        temporary=archive.with_suffix('.download')
        try:
            with requests.get(MODEL_URL,stream=True,timeout=(15,60)) as response:
                response.raise_for_status()
                with temporary.open('wb') as output:
                    for chunk in response.iter_content(1024*1024):
                        output.write(chunk)
            if digest(temporary)!=MODEL_SHA256:
                raise RuntimeError('Mandarin model checksum mismatch; the download was not installed.')
            os.replace(temporary,archive)
        finally:
            temporary.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as folder:
        staged=Path(folder)/MODEL_ID
        staged.mkdir()
        with tarfile.open(archive,'r:bz2') as package:
            # Extract only four expected regular files. No links or arbitrary paths.
            for name in FILES.values():
                member=package.getmember(f'{MODEL_ID}/{name}')
                if not member.isfile():
                    raise RuntimeError('Mandarin model archive contains an invalid entry.')
                with package.extractfile(member) as source,(staged/name).open('wb') as output:
                    shutil.copyfileobj(source,output)
        target.mkdir(exist_ok=True)
        for name in FILES.values():
            os.replace(staged/name,target/name)
    return target


def load(root):
    import sherpa_onnx
    target=Path(root)/MODEL_ID
    if not all((target/name).is_file() for name in FILES.values()):
        raise RuntimeError('The Mandarin model is not installed. Click Prepare Mandarin speech model or run python scripts/prepare_asr.py once (about 75 MB).')
    return sherpa_onnx.OnlineRecognizer.from_transducer(
        **{key:str(target/name) for key,name in FILES.items()},
        num_threads=min(4,os.cpu_count() or 1),sample_rate=16000,feature_dim=80,
        decoding_method='greedy_search',enable_endpoint_detection=False,provider='cpu')
