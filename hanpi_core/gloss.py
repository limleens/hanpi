"""Offline Chinese-English dictionary lookups using CC-CEDICT (CC BY-SA 4.0).
See https://cc-cedict.org/ . Online translation requires an explicit click.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache

from .text import clean_hanzi

GLOSSES = {
    "你好": "Hello", "你": "You", "好": "Good; well",
    "中国": "China", "中": "Middle; central", "国": "Country; nation",
    "谢谢": "Thank you", "谢": "To thank", "妈妈": "Mom; mother",
    "妈": "Mom", "麻": "Hemp; numb", "马": "Horse", "骂": "To scold",
    "汉字": "Chinese characters", "汉": "Chinese language", "字": "Character",
    "学习": "To study; to learn", "学": "To study", "习": "To practise",
    "我": "I; me", "爱": "To love", "吃": "To eat", "饭": "Cooked rice; meal",
}

@dataclass(frozen=True)
class Meaning:
    text: str
    source: str
    exact: bool
    note: str

@lru_cache(maxsize=1)
def _cedict():
    try:
        from pycccedict.cccedict import CcCedict
        return CcCedict()
    except (ImportError, OSError, ValueError):
        return None

@lru_cache(maxsize=4096)
def _entry(word: str):
    dictionary = _cedict()
    if dictionary is None:
        return None
    try:
        return dictionary.get_entry(word)
    except (KeyError, ValueError, TypeError):
        return None

def _short_definition(entry) -> str:
    if not entry:
        return ""
    for item in entry.get("definitions", []):
        word = str(item).strip()
        if word and not word.startswith("CL:"):
            return word[:180]
    return ""

def _exact(word: str) -> str:
    return GLOSSES.get(word, "") or _short_definition(_entry(word))

def lookup_meaning(text: str) -> Meaning:
    """Return exact definitions, or a labelled word-by-word gloss for passages."""
    hanzi = clean_hanzi(text)
    if not hanzi:
        return Meaning("", "none", False, "Enter Chinese text to see its meaning.")
    direct = _exact(hanzi)
    if direct:
        origin = "curated" if hanzi in GLOSSES else "CC-CEDICT"
        return Meaning(direct, origin, True, "Dictionary meaning; verify readings in context.")
    if _cedict() is None:
        return Meaning("", "unavailable", False,
                       "Install the requirements to enable the offline CC-CEDICT dictionary.")
    parts, unknown = [], []
    pos = 0
    while pos < len(hanzi):
        match = None
        for size in range(min(16, len(hanzi) - pos), 0, -1):
            word = hanzi[pos:pos+size]
            meaning = _exact(word)
            if meaning:
                match = (word, meaning)
                break
        if match:
            word, meaning = match
            parts.append(f"{word}: {meaning}")
            pos += len(word)
        else:
            unknown.append(hanzi[pos])
            parts.append(f"{hanzi[pos]}: ?")
            pos += 1
    note = "Approximate word-by-word dictionary gloss, not a fluent sentence translation."
    if unknown:
        note += " Unknown characters: " + "".join(unknown[:40]) + ("…" if len(unknown) > 40 else "")
    return Meaning(" · ".join(parts), "CC-CEDICT segmented gloss", False, note)

def meaning_for(text: str) -> str:
    return lookup_meaning(text).text

def translate_online(text: str) -> str:
    """Translate text only when the user explicitly opts in."""
    hanzi = clean_hanzi(text)
    if not hanzi:
        raise ValueError("Enter Chinese text first.")
    if len(hanzi) > 2500:
        raise ValueError("Online translation supports up to 2,500 Hanzi per request; select a shorter passage. OCR and pinyin retain all characters.")
    try:
        from deep_translator import GoogleTranslator
    except ImportError as exc:
        raise RuntimeError("Install deep-translator to enable online translation.") from exc
    try:
        translated = GoogleTranslator(source="zh-CN", target="en").translate(hanzi)
    except Exception as exc:
        raise RuntimeError("Online translation failed. Check your connection or type the meaning manually.") from exc
    if not translated or not str(translated).strip():
        raise RuntimeError("No translation was returned.")
    return str(translated).strip()


def key_vocabulary(text: str, limit: int = 6) -> list[tuple[str, str]]:
    """A few distinct dictionary words; this never truncates the actual passage."""
    hanzi = clean_hanzi(text)
    words, seen, pos = [], set(), 0
    while pos < len(hanzi) and len(words) < limit:
        for size in range(min(16, len(hanzi) - pos), 0, -1):
            word = hanzi[pos:pos + size]
            meaning = _exact(word)
            if meaning:
                if word not in seen:
                    words.append((word, meaning))
                    seen.add(word)
                pos += size
                break
        else:
            pos += 1
    return words


def translate_to_chinese(text: str) -> str:
    """Explicit opt-in English search; never called while typing or on page load."""
    query = (text or '').strip()
    if not query or len(query) > 2500:
        raise ValueError('Enter an English word or phrase under 2,500 characters.')
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source='en', target='zh-CN').translate(query)
    except Exception as exc:
        raise RuntimeError('Online translation is unavailable. Try Chinese text or Scan instead.') from exc
    if not clean_hanzi(translated):
        raise RuntimeError('No Chinese translation was returned. Try Chinese text or Scan instead.')
    return str(translated).strip()
