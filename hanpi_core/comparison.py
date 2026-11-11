"""Character alignment of ASR TEXT; never a diagnosis of acoustic errors."""
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from html import escape

from .text import clean_hanzi,get_syllables


@lru_cache(maxsize=1)
def _converter():
    from opencc import OpenCC
    return OpenCC('t2s')


def canonical_char(char):
    converted=_converter().convert(char)
    return converted if len(converted)==1 else char


@dataclass(frozen=True)
class Comparison:
    expected: str
    recognized: str
    flags: dict[int,str]
    additions: tuple[str,...]

    @property
    def matches(self):
        return not self.flags and not self.additions


def compare_transcript(expected,recognized):
    target=clean_hanzi(expected)
    heard=clean_hanzi(recognized)
    if not target:
        raise ValueError('Choose a Chinese target sentence first.')
    if not heard:
        raise ValueError('No Chinese transcript to compare. Transcribe a recording or enter a corrected transcript.')
    if max(len(target),len(heard))>2500:
        raise ValueError('Compare a shorter sentence (up to 2,500 characters); nothing has been truncated.')
    reference=''.join(canonical_char(c) for c in target)
    hypothesis=''.join(canonical_char(c) for c in heard)
    flags={}
    additions=[]
    for op,i1,i2,j1,j2 in SequenceMatcher(None,reference,hypothesis,autojunk=False).get_opcodes():
        if op in ('replace','delete'):
            for i in range(i1,i2):
                flags[i]='possible missing word' if op=='delete' else 'possible word mismatch'
        if op=='insert':
            additions.append(heard[j1:j2])
    return Comparison(target,heard,flags,tuple(additions))


def comparison_view(expected,recognized):
    result=compare_transcript(expected,recognized)
    text=''.join(f'<mark class="word-difference" title="{escape(result.flags[i])}">{escape(c)}</mark>'
                 if i in result.flags else escape(c) for i,c in enumerate(result.expected))
    additions='; '.join(result.additions)
    summary=('The transcript text matches the target. This does not verify pronunciation or tones.' if result.matches else
             'Possible word differences in the transcript. ASR can be wrong: check and edit what it heard.')
    html=(f'<section class="sentence-comparison" aria-live="polite"><h3>Expected</h3><p lang="zh-CN">{text}</p>'
          f'<h3>I heard · check this transcript</h3><p lang="zh-CN">{escape(recognized)}</p>'
          f'<p>{escape(summary)}</p>'+(f'<p>Extra transcript text: {escape(additions)}</p>' if additions else '')+
          '<small>Punctuation and Simplified/Traditional variants are ignored in alignment. '
          'These are text differences, not detected tone or consonant errors.</small></section>')
    syllables=get_syllables(result.expected)
    choices=[(f'{result.expected[i]} · {syllables[i].spoken_pinyin} — {flag}',str(i)) for i,flag in result.flags.items()]
    return html,choices
