"""Offline reverse-English and tone-aware pinyin indexes over real CC-CEDICT."""
from dataclasses import dataclass
from functools import lru_cache
import re
import unicodedata

from pypinyin.contrib.tone_convert import to_tone
from .dictionary import get_dictionary, dictionary_status
from .starter import ENTRIES


@dataclass(frozen=True)
class Candidate:
    hanzi: str
    traditional: str
    numbered: str
    pinyin: str
    meaning: str
    tone: int
    source: str

    @property
    def key(self):
        return f'{self.hanzi}|{self.numbered}|{self.meaning}'

    @property
    def label(self):
        return f'{self.hanzi} · {self.pinyin} · {self.meaning}'


@dataclass(frozen=True)
class SearchPage:
    groups: list[list[Candidate]]
    total: int
    shown: int
    has_more: bool
    source: str


COMMON_RANK = {entry['simplified']:i for i,entry in enumerate(ENTRIES)}

TONE_MARKS = {'\u0304':1,'\u0301':2,'\u030c':3,'\u0300':4}


def normalize_pinyin(query):
    text = query.lower().strip().replace('u:','v').replace('’',"'")
    if not text or len(text)>100 or not all(c.isalpha() or c in "012345 '-:" or unicodedata.combining(c) for c in text):
        raise ValueError('Enter pinyin such as ma, ma3, mǎ, or ni3 hao3.')
    base, tones = [], []
    for c in unicodedata.normalize('NFD', text):
        if c in TONE_MARKS:
            tones.append(TONE_MARKS[c])
        elif c == '\u0308' and base and base[-1]=='u':
            base[-1]='v'
        elif c in '012345':
            tones.append(5 if c=='0' else int(c))
        elif c.isascii() and c.isalpha():
            base.append(c)
    if not base:
        raise ValueError('Enter pinyin such as ma, ma3 or mǎ.')
    return ''.join(base), tuple(tones) if tones else None


def _canonical(text):
    text = re.sub(r'\([^)]*\)|\[[^]]*\]', '', text.lower())
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip().removeprefix('to ')


@lru_cache(maxsize=1)
def _index():
    dictionary = get_dictionary()
    entries = dictionary.get_entries() if dictionary else ENTRIES
    candidates, english, pinyin = [], {}, {}
    merged = {}
    for entry in entries:
        numbered = entry['pinyin'].lower().replace('u:', 'v')
        key=entry['simplified'],numbered
        group=merged.setdefault(key,dict(traditional=entry['traditional'],definitions=[]))
        for definition in entry['definitions']:
            definition=definition.strip()
            if not definition.startswith('CL:') and definition not in group['definitions']:
                group['definitions'].append(definition)
    for (word,numbered),entry in merged.items():
        definitions=sorted(entry['definitions'],key=lambda d:(d.lower().startswith(('variant of','surname ','used in','see ')),len(d)))
        if not definitions:
            continue
        meaning='; '.join(definitions[:4])
        tokens = numbered.split()
        tone = int(tokens[0][-1]) if tokens and tokens[0][-1:] in '12345' else 5
        candidate = Candidate(word,entry['traditional'],numbered,' '.join(to_tone(s) for s in tokens),meaning,tone,
                              'CC-CEDICT' if dictionary else 'starter dictionary (limited)')
        i=len(candidates)
        candidates.append(candidate)
        base = re.sub('[^a-zv]','',numbered)
        pinyin.setdefault(base,[]).append(i)
        for token in set(re.findall('[a-z]+', _canonical(' '.join(definitions)))):
            english.setdefault(token,set()).add(i)
    return candidates, english, pinyin


def _common_rank(candidate):
    return COMMON_RANK.get(candidate.hanzi,1000),len(candidate.hanzi),len(candidate.meaning),candidate.hanzi


def search_english(query, page=0, page_size=20):
    query=_canonical(query)
    tokens=set(re.findall('[a-z]+',query))
    if not tokens:
        raise ValueError('Enter an English word or phrase, for example eat or coffee.')
    candidates,index,_=_index()
    ids=set.intersection(*(index.get(token,set()) for token in tokens))
    def rank(i):
        c=candidates[i]
        exact=any(_canonical(d)==query for d in c.meaning.split(';'))
        return (not exact,*_common_rank(c))
    ordered=[candidates[i] for i in sorted(ids,key=rank)]
    start=max(0,page)*page_size
    selected=ordered[start:start+page_size]
    source='CC-CEDICT' if dictionary_status().ready else 'starter dictionary (limited)'
    return SearchPage([selected,[],[],[],[]],len(ordered),len(selected),start+len(selected)<len(ordered),source)


def search_pinyin(query, page=0, per_tone=6):
    base,tones=normalize_pinyin(query)
    candidates,_,index=_index()
    groups=[[] for _ in range(5)]
    for i in index.get(base,[]):
        c=candidates[i]
        actual=tuple(int(n[-1]) if n[-1:] in '12345' else 5 for n in c.numbered.split())
        if tones is not None and tones != actual:
            continue
        groups[c.tone-1].append(c)
    for group in groups:
        group.sort(key=_common_rank)
    start=max(0,page)*per_tone
    selected=[group[start:start+per_tone] for group in groups]
    return SearchPage(selected,sum(map(len,groups)),sum(map(len,selected)),
                      any(len(group)>start+per_tone for group in groups),
                      'CC-CEDICT' if dictionary_status().ready else 'starter dictionary (limited)')
