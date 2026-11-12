"""Small evidence-led dialogue tree; no LLM or invented pronunciation claims."""
from dataclasses import dataclass


@dataclass(frozen=True)
class TutorCue:
    text: str
    example: str = ''
    mood: str = 'ready'


def practice_cue(expected,detected,found,example):
    if found is False:
        return TutorCue('The transcript came out differently. Let’s listen, then try once more.',example,'guide')
    if expected==5:
        return TutorCue('Keep it short and light. Neutral tones aren’t graded here.',example,'guide')
    if detected is None:
        text=('I found the syllable. Let’s get a clearer pitch: one sound, then stop.' if found else
              'Let’s try one clear sound, then stop. I couldn’t check that pitch yet.')
        return TutorCue(text,'','guide')
    if detected==expected:
        text=('Nice, the pitch shape looks close. Next character, or the whole phrase?' if found else
              'The pitch shape looks close. Want another try, or the next character?')
        return TutorCue(text,'','happy')
    if expected==3 and detected==1:
        return TutorCue('Third tones can stay low. Let’s listen and try this one on its own.',example,'guide')
    observed={1:'stayed level',2:'rose',3:'dipped and rose',4:'fell'}[detected]
    aim={1:'keep your voice high and steady',2:'let your voice rise',
         3:'start low, dip, then rise gently',4:'start high, then drop'}[expected]
    return TutorCue(f'That pitch {observed}. For this one, {aim}. Listen, then try again.',example,'guide')


def phrase_cue(expected,heard):
    from .comparison import compare_transcript,readings_match
    result=compare_transcript(expected,heard)
    if result.matches or readings_match(expected,heard):
        return TutorCue('I heard the phrase. Nice practice! Want to work on a character, or finish here?','','happy')
    if result.flags:
        return TutorCue('Let’s take it one word at a time. Tap a highlighted word and I’ll break it down.','','guide')
    if result.additions:
        return TutorCue('The transcript has some extra words. Want to listen and try the phrase once more?',expected,'guide')
    return TutorCue('Those spellings sound similar. Let’s listen, then try the phrase again.',expected,'guide')
