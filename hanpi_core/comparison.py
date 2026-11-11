"""Character alignment of ASR TEXT; never a diagnosis of acoustic errors."""
from dataclasses import dataclass,field
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
    sound_alikes: dict[int,str]=field(default_factory=dict)

    @property
    def matches(self):
        return not self.flags and not self.additions and not self.sound_alikes


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
    sound_alikes={}
    from pypinyin.contrib.tone_convert import to_normal
    expected_sounds=[to_normal(s.written_pinyin) for s in get_syllables(target)]
    heard_sounds=[to_normal(s.written_pinyin) for s in get_syllables(heard)]
    for op,i1,i2,j1,j2 in SequenceMatcher(None,reference,hypothesis,autojunk=False).get_opcodes():
        if op in ('replace','delete'):
            for i in range(i1,i2):
                j=j1+(i-i1)
                if op=='replace' and i2-i1==j2-j1 and expected_sounds[i]==heard_sounds[j]:
                    sound_alikes[i]=heard[j]
                else:
                    flags[i]='possible missing word' if op=='delete' else 'possible word mismatch'
        if op=='insert':
            additions.append(heard[j1:j2])
    return Comparison(target,heard,flags,tuple(additions),sound_alikes)


def comparison_view(expected,recognized):
    result=compare_transcript(expected,recognized)
    text=''.join(f'<mark class="word-difference" title="{escape(result.flags[i])}">{escape(c)}</mark>'
                 if i in result.flags else escape(c) for i,c in enumerate(result.expected))
    additions='; '.join(result.additions)
    summary=('The transcript text matches the target. This does not verify pronunciation or tones.' if result.matches else
             ('The words sound similar. Spelling may be a recognition mistake; listen back.' if result.sound_alikes and not result.flags and not result.additions else 'A few words may need another try. Speech recognition can also make mistakes.'))
    html=(f'<section class="sentence-comparison" aria-live="polite"><h3>Expected</h3><p lang="zh-CN">{text}</p>'
          f'<h3>What we heard</h3><p lang="zh-CN">{escape(recognized)}</p>'
          f'<p>{escape(summary)}</p>'+(f'<p>Extra transcript text: {escape(additions)}</p>' if additions else '')+
          '<small>Punctuation and Simplified/Traditional variants are ignored in alignment. '
          'These are text differences, not detected tone or consonant errors.</small></section>')
    syllables=get_syllables(result.expected)
    choices=[(f'{result.expected[i]} · {syllables[i].spoken_pinyin}',str(i)) for i,flag in result.flags.items()]
    return html,choices
