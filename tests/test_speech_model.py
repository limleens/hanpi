"""Pinned model installation works offline, repairs corruption and rejects links."""
from hashlib import sha256
import io
import tarfile

import pytest
from hanpi_core import speech_model as models


def archive_fixture(monkeypatch,tmp_path,*,bad_file=False,link=False):
    files={'model.int8.onnx':b'model-fixture','tokens.txt':b'tokens-fixture'}
    monkeypatch.setattr(models,'ACCURATE_ID','fixture-model')
    monkeypatch.setattr(models,'ACCURATE_FILES',{name:sha256(data).hexdigest() for name,data in files.items()})
    archive=tmp_path/'fixture-model.tar.bz2'
    with tarfile.open(archive,'w:bz2') as output:
        for name,data in files.items():
            info=tarfile.TarInfo('fixture-model/'+name)
            if link and name=='model.int8.onnx':
                info.type=tarfile.SYMTYPE;info.linkname='/outside'
                output.addfile(info);continue
            if bad_file and name=='model.int8.onnx':data=b'tampered'
            info.size=len(data);output.addfile(info,io.BytesIO(data))
        unsafe=tarfile.TarInfo('../../must-not-be-written');unsafe.size=3
        output.addfile(unsafe,io.BytesIO(b'bad'))
    monkeypatch.setattr(models,'ACCURATE_SHA256',models.digest(archive))
    monkeypatch.setattr(models.requests,'get',lambda *a,**kw:pytest.fail('Verified cached archive must not download'))
    return files


def test_verified_archive_install_and_repair(monkeypatch,tmp_path):
    files=archive_fixture(monkeypatch,tmp_path)
    target=models.install_accurate(tmp_path)
    assert {p.name for p in target.iterdir()}==set(files)
    for name,data in files.items():assert (target/name).read_bytes()==data
    (target/'model.int8.onnx').write_bytes(b'corrupt')
    assert models.install_accurate(tmp_path)==target
    assert (target/'model.int8.onnx').read_bytes()==files['model.int8.onnx']
    assert models.install_accurate(tmp_path)==target


@pytest.mark.parametrize('bad_file,link',[(True,False),(False,True)])
def test_invalid_expected_model_file_never_gets_installed(monkeypatch,tmp_path,bad_file,link):
    archive_fixture(monkeypatch,tmp_path,bad_file=bad_file,link=link)
    with pytest.raises(RuntimeError):models.install_accurate(tmp_path)
    assert not (tmp_path/'fixture-model').exists()


def test_bad_download_checksum_cleans_temporary_file(monkeypatch,tmp_path):
    monkeypatch.setattr(models,'ACCURATE_ID','fixture-model')
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def raise_for_status(self):pass
        def iter_content(self,*args):yield b'not-the-model'
    monkeypatch.setattr(models.requests,'get',lambda *args,**kwargs:Response())
    with pytest.raises(RuntimeError,match='checksum mismatch'):models.install_accurate(tmp_path)
    assert not list(tmp_path.iterdir())
