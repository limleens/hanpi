"""Character alignment of ASR TEXT; never a diagnosis of acoustic errors."""
from dataclasses import dataclass,field
from difflib import SequenceMatcher
from functools import lru_cache
from html import escape

from .text import clean_hanzi,get_syllables


def readings_match(expected,recognized,reading=None):
    """Compare contextual pinyin INCLUDING tone; not an acoustic diagnosis.

    A selected isolated target can supply its spoken/dictionary reading so
    sandhi and alternative polyphonic readings survive the comparison.
    """
    from pypinyin.contrib.tone_convert import to_tone3
    from unicodedata import normalize
    target=get_syllables(expected,reading)
    heard=get_syllables(recognized)
    if not target or len(target)!=len(heard):
        return False
    def key(syllable):
        return to_tone3(normalize('NFC',syllable.spoken_pinyin),neutral_tone_with_five=True)
    return all(key(a)==key(b) for a,b in zip(target,heard))


@lru_cache(maxsize=1)
def _converter():
    from opencc import OpenCC
    return OpenCC('t2s')


def canonical_char(char):
    converted=_converter().convert(char)
    return converted if len(converted)==1 else char


@dataclass(frozen=True)
class SyllableMatch:
    matches: bool
    ignored_ending: str = ''


def match_isolated_syllable(expected,recognized,reading=None):
    """A forgiving TEXT check for one-syllable practice, never sentence grading.

    ASR spelling cannot reliably establish an isolated sound's tone. Compare
    the base syllable here; the acoustic coach checks pitch independently.
    Allow one trailing conversational particle, but no arbitrary extra word.
    Preserve the recognizer's original transcript in all cases.
    """
    from pypinyin.contrib.tone_convert import to_normal
    from unicodedata import normalize
    target=get_syllables(expected,reading)
    heard=get_syllables(recognized)
    if len(target)!=1 or len(heard) not in (1,2):
        return SyllableMatch(False)
    def base(syllable):
        return to_normal(normalize('NFC',syllable.spoken_pinyin))
    ending=heard[1].hanzi if len(heard)==2 else ''
    particle=canonical_char(ending) in {'了','儿','啊','呀','呢','吧','嘛','吗','啦','呐','哦'} if ending else False
    if ending and not particle and base(heard[1]) not in {'le','er'}:
        return SyllableMatch(False)
    matches=base(target[0])==base(heard[0])
    return SyllableMatch(matches,ending if matches else '')


@dataclass(frozen=True)
class Comparison:
    expected: str
    recognized: str
    flags: dict[int,str]
    additions: tuple[str,...]
    sound_alikes: dict[int,str]=field(default_factory=dict)
    heard_parts: dict[int,str]=field(default_factory=dict)
    target_parts: dict[int,str]=field(default_factory=dict)
    spans: dict[int,tuple[int,int,int,int]]=field(default_factory=dict)

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
    heard_parts={}
    target_parts={}
    spans={}
    from pypinyin.contrib.tone_convert import to_normal
    expected_sounds=[to_normal(s.written_pinyin) for s in get_syllables(target)]
    heard_sounds=[to_normal(s.written_pinyin) for s in get_syllables(heard)]
    for op,i1,i2,j1,j2 in SequenceMatcher(None,reference,hypothesis,autojunk=False).get_opcodes():
        for i in range(i1,i2):
            # Unequal replacements are aligned as a segment, never invented
            # one-to-one acoustic/character correspondences.
            paired=op=='equal' or (op=='replace' and i2-i1==j2-j1)
            heard_parts[i]=heard[j1+i-i1] if paired else heard[j1:j2]
            target_parts[i]=target[i] if paired or op=='delete' else target[i1:i2]
            spans[i]=(i,i+1,j1+i-i1,j1+i-i1+1) if paired else (i,i+1,j1,j2) if op=='delete' else (i1,i2,j1,j2)
        if op in ('replace','delete'):
            for i in range(i1,i2):
                j=j1+(i-i1)
                if op=='replace' and i2-i1==j2-j1 and expected_sounds[i]==heard_sounds[j]:
                    sound_alikes[i]=heard[j]
                else:
                    flags[i]='possible missing word' if op=='delete' else 'possible word mismatch'
        if op=='insert':
            additions.append(heard[j1:j2])
    return Comparison(target,heard,flags,tuple(additions),sound_alikes,heard_parts,target_parts,spans)


def comparison_view(expected,recognized,include_matches=False):
    result=compare_transcript(expected,recognized)
    text=''.join(f'<mark class="word-difference" title="{escape(result.flags[i])}">{escape(c)}</mark>'
                 if i in result.flags else escape(c) for i,c in enumerate(result.expected))
    additions='; '.join(result.additions)
    if result.matches:
        summary='Words match. Nice work!'
    elif readings_match(expected,recognized):
        summary='Same pronunciation, different characters.'
    elif result.sound_alikes and not result.flags and not result.additions:
        summary='These sound similar. Hanpi may have chosen the wrong spelling.'
    else:
        summary='Try the highlighted words. Speech recognition can also make mistakes.'
    html=(f'<section class="sentence-comparison" aria-live="polite"><h3>Target</h3><p lang="zh-CN">{text}</p>'
          f'<h3>You said</h3><p lang="zh-CN">{escape(recognized)}</p>'
          f'<p>{escape(summary)}</p>'+(f'<p>Extra transcript text: {escape(additions)}</p>' if additions else '')+
          '<p class="microcopy">Word check, not a tone score.</p>'
          '<small>This does not verify pronunciation. These are text differences, '
          'not detected tone or consonant errors.</small></section>')
    syllables=get_syllables(result.expected)
    indices=range(len(result.expected)) if include_matches else result.flags
    choices=[(f'{result.expected[i]} · {syllables[i].spoken_pinyin}' +
              (f' → {result.heard_parts[i] or "not heard"}' if i in result.flags or i in result.sound_alikes else ''),str(i)) for i in indices]
    return html,choices


def transcript_breakdown(expected,recognized,index):
    """Show aligned ASR spelling/readings, never infer measured tones from text."""
    result=compare_transcript(expected,recognized)
    position=int(index)
    if position not in result.heard_parts:
        raise ValueError('Choose a character from the target.')
    target=result.target_parts[position]
    heard=result.heard_parts[position]
    i1,i2,j1,j2=result.spans[position]
    target_reading=' '.join(s.spoken_pinyin for s in get_syllables(result.expected)[i1:i2])
    heard_reading=' '.join(s.written_pinyin for s in get_syllables(result.recognized)[j1:j2])
    message=(f'{heard} · {heard_reading}' if heard else 'Not heard in this recording')
    return (f'<section class="heard-breakdown"><h3>Target</h3>'
            f'<p lang="zh-CN">{escape(target)} · {escape(target_reading)}</p>'
            f'<h3>You said</h3><p lang="zh-CN">{escape(message)}</p>'
            '<p class="microcopy">Pinyin follows the transcript. Try it alone to check the tone.</p></section>')
