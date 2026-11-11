"""CPU OCR with bounded preprocessing, real model scores and mandatory review."""
from dataclasses import dataclass
from functools import lru_cache
import logging

import numpy as np
from PIL import Image, ImageFilter, ImageOps
from .text import clean_hanzi

LOG=logging.getLogger(__name__)


@dataclass(frozen=True)
class OCRCandidate:
    text: str
    score: float | None
    variant: str
    engine: str = 'RapidOCR'


@dataclass(frozen=True)
class OCRResult:
    best: OCRCandidate
    candidates: tuple[OCRCandidate,...]
    uncertain: bool


@lru_cache(maxsize=1)
def _rapidocr():
    from rapidocr import RapidOCR
    return RapidOCR()


def preprocess(image):
    if image is None:
        raise ValueError('Upload a photo before selecting Recognize characters.')
    image=ImageOps.exif_transpose(image)
    if image.mode in ('RGBA','LA') or 'transparency' in image.info:
        rgba=image.convert('RGBA')
        background=Image.new('RGBA',rgba.size,'white')
        image=Image.alpha_composite(background,rgba).convert('RGB')
    else:
        image=image.convert('RGB')
    if min(image.size)<2:
        raise ValueError('This crop is too small. Retake it closer with more detail.')
    if max(image.size)>2400:
        image.thumbnail((2400,2400),Image.Resampling.LANCZOS)
    yield 'original',image
    small=min(image.size)<100 or max(image.size)<500
    if small:
        factor=min(4,max(2,round(90/min(image.size))))
        image=image.resize((image.width*factor,image.height*factor),Image.Resampling.LANCZOS)
        image=ImageOps.expand(image,border=16,fill='white')
        yield f'upscaled {factor}x',image
    gray=ImageOps.autocontrast(ImageOps.grayscale(image),cutoff=1)
    gray=gray.filter(ImageFilter.UnsharpMask(radius=1,percent=140,threshold=3))
    yield 'contrast and sharpen',gray.convert('RGB')
    rgb=np.asarray(image,dtype=np.float32)
    redness=np.maximum(rgb[:,:,0]-(rgb[:,:,1]+rgb[:,:,2])/2,0)
    if float(redness.max())>20 and float(redness.std())>3:
        red=Image.fromarray(np.clip(255-redness*2,0,255).astype(np.uint8))
        red=ImageOps.autocontrast(red,cutoff=1).filter(ImageFilter.UnsharpMask(radius=1,percent=120,threshold=2))
        yield 'red-text contrast',red.convert('RGB')


def _candidate(result,variant):
    texts=getattr(result,'txts',None)
    scores=getattr(result,'scores',None)
    if texts is None and isinstance(result,(tuple,list)):
        rows=result[0] if len(result)==2 else result
        texts=[row[1] for row in (rows or []) if len(row)>=2]
        scores=[row[2] for row in (rows or []) if len(row)>=3]
    texts=list(texts or [])
    chinese=[(i,clean_hanzi(text)) for i,text in enumerate(texts) if clean_hanzi(text)]
    if not chinese:
        return None
    weighted=[]
    if scores is not None:
        for i,text in chinese:
            if i<len(scores) and np.isfinite(scores[i]):
                weighted.extend([float(scores[i])]*len(text))
    score=float(np.mean(weighted)) if weighted else None
    if score is not None and score<.55:
        return None
    return OCRCandidate(''.join(text for _,text in chinese),score,variant)


def recognize_image(image):
    candidates=[]
    errors=[]
    try:
        engine=_rapidocr()
        for variant,prepared in preprocess(image):
            try:
                candidate=_candidate(engine(np.asarray(prepared)),variant)
                if candidate:
                    candidates.append(candidate)
                    # Ordinary clean pages need no expensive series of retries.
                    if variant=='original' and candidate.score is not None and candidate.score>=.94 and min(prepared.size)>=120:
                        break
            except Exception as exc:
                LOG.warning('OCR variant %s failed: %s',variant,type(exc).__name__)
                errors.append(f'RapidOCR {variant}: {type(exc).__name__}')
    except ValueError:
        raise
    except Exception as exc:
        LOG.exception('RapidOCR initialization failed')
        errors.append(f'RapidOCR: {type(exc).__name__}: {exc}')
    if not candidates:
        try:
            import pytesseract
            languages=set(pytesseract.get_languages(config=''))
            chinese=languages.intersection({'chi_sim','chi_tra'})
            if chinese:
                prepared=list(preprocess(image))[-1][1]
                data=pytesseract.image_to_data(prepared,lang='+'.join(sorted(chinese)),config='--psm 6',output_type=pytesseract.Output.DICT)
                words=[(clean_hanzi(t),float(c)/100) for t,c in zip(data['text'],data['conf']) if clean_hanzi(t) and float(c)>=55]
                if words:
                    candidates.append(OCRCandidate(''.join(t for t,_ in words),float(np.mean([c for _,c in words])),'fallback','Tesseract'))
        except Exception as exc:
            LOG.warning('Tesseract fallback unavailable: %s',type(exc).__name__)
    if not candidates:
        if image is None:
            raise ValueError('Upload a photo before selecting Recognize characters.')
        raise RuntimeError('No reliable Chinese text was found. Crop around one line, use better light, or retake closer. You can type the text instead. '+ ' '.join(errors))
    support={c.text:sum(other.text==c.text for other in candidates) for c in candidates}
    candidates.sort(key=lambda c:((c.score if c.score is not None else .5)+min(support[c.text]-1,2)*.015),reverse=True)
    unique=list({c.text:c for c in reversed(candidates)}.values())
    unique.sort(key=lambda c:(c.score if c.score is not None else .5),reverse=True)
    best=candidates[0]
    return OCRResult(best,tuple([best]+[c for c in unique if c.text!=best.text]),
                     best.score is None or best.score<.88 or len(unique)>1)


def extract_hanzi(image):
    """Compatibility API; UI uses recognize_image and asks the user to verify."""
    result=recognize_image(image)
    return result.best.text,result.best.engine
