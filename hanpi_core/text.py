"""Extract per-character written and spoken pinyin from Hanzi."""

from __future__ import annotations
import re
from dataclasses import dataclass

HANZI = re.compile(r"[\u3400-\u9fff\uf900-\ufaff\U00020000-\U0002fa1f\U00030000-\U000323af]")
# Storage safeguard, not a recognition limit.
MAX_HANZI = 10000

# Minimal demo mode if PyPinyin isn't installed; never silently transliterate
# arbitrary Chinese using single-character lookup (polyphones are contextual).
EXAMPLES = {
    "你好": [("nǐ", "ní", 2), ("hǎo", "hǎo", 3)],
    "中国": [("zhōng", "zhōng", 1), ("guó", "guó", 2)],
    "谢谢": [("xiè", "xiè", 4), ("xie", "xie", 5)],
    "妈妈": [("mā", "mā", 1), ("ma", "ma", 5)],
    "汉字": [("hàn", "hàn", 4), ("zì", "zì", 4)],
    "学习": [("xué", "xué", 2), ("xí", "xí", 2)],
    "妈": [("mā", "mā", 1)], "麻": [("má", "má", 2)],
    "马": [("mǎ", "mǎ", 3)], "骂": [("mà", "mà", 4)],
}

@dataclass(frozen=True)
class Syllable:
    index: int
    hanzi: str
    written_pinyin: str
    spoken_pinyin: str
    expected_tone: int

    @property
    def title(self):
        label = " (sandhi)" if self.written_pinyin != self.spoken_pinyin else ""
        return f"{self.index + 1}. {self.hanzi} · {self.spoken_pinyin}{label}"

def clean_hanzi(text: str, max_hanzi: int | None = None) -> str:
    """Keep all recognised Hanzi; never silently truncate OCR or input."""
    result = "".join(HANZI.findall(text or ""))
    return result if max_hanzi is None else result[:max_hanzi]

def get_syllables(text: str, reading: str | None = None) -> list[Syllable]:
    hanzi = clean_hanzi(text)
    if not hanzi:
        return []
    if reading and len(hanzi) == 1:
        from pypinyin.contrib.tone_convert import to_tone, to_tone3
        numbered = to_tone3(reading.lower(), neutral_tone_with_five=True)
        if numbered[-1:] not in '12345' or ' ' in numbered:
            raise ValueError('Choose a valid numbered dictionary reading.')
        accented = to_tone(numbered)
        return [Syllable(0, hanzi, accented, accented, int(numbered[-1]))]
    try:
        from pypinyin import Style, lazy_pinyin
    except ImportError:
        demo = EXAMPLES.get(hanzi)
        if demo is None:
            raise RuntimeError("Install with pip install -r requirements.txt to read arbitrary Hanzi. Demo mode supports the bundled examples only.") from None
        return [Syllable(i, char, w, s, tone)
                for i, (char, (w, s, tone)) in enumerate(zip(hanzi, demo))]
    opts = {"neutral_tone_with_five": True}
    written = lazy_pinyin(hanzi, style=Style.TONE, **opts)
    spoken = lazy_pinyin(hanzi, style=Style.TONE, tone_sandhi=True, **opts)
    numbered = lazy_pinyin(hanzi, style=Style.TONE3, tone_sandhi=True, **opts)
    return [Syllable(i, c, w, s, int(n[-1]) if n and n[-1] in "12345" else 5)
            for i, (c, w, s, n) in enumerate(zip(hanzi, written, spoken, numbered))]
