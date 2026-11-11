from PIL import Image
from hanpi_core import ocr


def test_image_ocr_no_longer_truncates_at_24(monkeypatch):
    class Result:
        txts = ["汉" * 80]
    monkeypatch.setattr(ocr, "_rapidocr", lambda: lambda _image: Result())
    text, engine = ocr.extract_hanzi(Image.new("RGB", (400, 160), "white"))
    assert len(text) == 80
    assert engine == "RapidOCR"
