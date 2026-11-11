"""Escaped presentation and accessible choices; no browser event bridges."""
from html import escape

from hanpi_core.gloss import key_vocabulary
from hanpi_core.text import get_syllables
from hanpi_core.tones import PRACTICE_TIPS

PALETTE = {
    1: ('#365db3', '#edf2fc'), 2: ('#237a68', '#eaf5ef'),
    3: ('#7755a7', '#f1ecf8'), 4: ('#b94d43', '#fceee9'),
    5: ('#68645f', '#f0eeeb'),
}


def character_choices(text, reading=None):
    return [(f'{s.hanzi}\n{s.spoken_pinyin}', f'{s.index}:{s.expected_tone}') for s in get_syllables(text, reading)]


def character_styles():
    # Tone metadata travels in native Radio values, so global CSS stays stable.
    # No HTML-to-Gradio JavaScript bridge or injected per-phrase stylesheet.
    return '\n'.join(
        f'#character-choices label:has(input[value$=":{tone}"])'
        f'{{--tone:{color};--tone-bg:{background};}}'
        for tone, (color, background) in PALETTE.items()
    )


def spotlight(text, index, reading=None):
    syllables = get_syllables(text, reading)
    if not syllables:
        return '', ''
    try:
        position = int(index)
        if not 0 <= position < len(syllables):
            raise ValueError
    except (TypeError, ValueError):
        position = 0
    s = syllables[position]
    color, background = PALETTE[s.expected_tone]
    sandhi = s.written_pinyin != s.spoken_pinyin
    note = (f'Written {escape(s.written_pinyin)} → spoken {escape(s.spoken_pinyin)} · tone sandhi'
            if sandhi else f'{escape(s.spoken_pinyin)} · tone {s.expected_tone if s.expected_tone != 5 else "neutral"}')
    html = (f'<section class="spotlight" style="--tone:{color};--tone-bg:{background}">'
            f'<p class="eyebrow">SPOTLIGHT · {position + 1} / {len(syllables)}</p>'
            f'<div class="focus-hanzi" lang="zh-CN">{escape(s.hanzi)}</div>'
            f'<div class="focus-pinyin">{escape(s.spoken_pinyin)}</div>'
            f'<p class="sandhi">{note}</p>'
            '<h3>Listen, then give it a try.</h3>'
            f'<p class="tone-tip">{escape(PRACTICE_TIPS[s.expected_tone])}</p></section>')
    # A changed tone needs phrase context for a faithful TTS example.
    return html, ''.join(s.hanzi for s in syllables) if sandhi else s.hanzi


def vocabulary_view(text):
    words = key_vocabulary(text)
    if not words:
        return '<p class="muted">No dictionary words found. You can add your own meaning.</p>', []
    html = '<div class="vocabulary-grid">' + ''.join(
        f'<article class="vocab"><span lang="zh-CN">{escape(word)}</span>'
        f'<small>{escape(" ".join(s.written_pinyin for s in get_syllables(word)))}</small>'
        f'<p>{escape(meaning)}</p></article>' for word, meaning in words
    ) + '</div>'
    return html, [(f'{word} · {meaning}', word) for word, meaning in words]
