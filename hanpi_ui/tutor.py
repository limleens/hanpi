"""An original tiger and short, escaped coaching captions."""
from html import escape
from pathlib import Path
from hanpi_core.tutor import TutorCue

TIGER=(Path(__file__).parent/'tiger.svg').read_text(encoding='utf-8')


def tutor_view(cue:TutorCue):
    mood=cue.mood if cue.mood in ('ready','guide','happy') else 'ready'
    return (f'<section class="tutor-card tutor-{mood}"><div class="tutor-avatar">{TIGER}</div>'
            '<div class="tutor-bubble"><span class="tutor-name">hǔ · your speaking buddy</span>'
            f'<p role="status" aria-live="polite">{escape(cue.text)}</p></div></section>')
