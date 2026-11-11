"""Hanpi — snap, translate, learn! Run with: python app.py."""
from __future__ import annotations

from html import escape
from pathlib import Path
import importlib.util
import os
import sys

import gradio as gr
import matplotlib.pyplot as plt
import numpy as np

from hanpi_core.ocr import recognize_image
from hanpi_core.dictionary import dictionary_status
from hanpi_core.translation import sentence_translation
from hanpi_core.search import search_english, search_pinyin
from hanpi_core.comparison import comparison_view
from hanpi_core.asr import prepare_model, backend_name
from hanpi_core.gloss import meaning_for, lookup_meaning, translate_online, translate_to_chinese
from hanpi_core.library import save_entry, list_entries, get_entry, delete_entry, mark_practiced
from hanpi_core.text import clean_hanzi, get_syllables
from hanpi_core.tones import PRACTICE_TIPS, TONES, analyze_tone
from hanpi_core.voice import synthesize_neural, DEFAULT_VOICE
from hanpi_ui.presentation import character_choices, character_styles, spotlight, vocabulary_view

CSS = (Path(__file__).parent / 'hanpi_ui' / 'style.css').read_text(encoding='utf-8') + character_styles()

BROWSER_SPEECH = """(text, rate, status) => {
    if (!text) return status;
    if (!('speechSynthesis' in window))
        return 'Speech is unavailable in this browser. Try a browser with Mandarin speech support.';
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'zh-CN'; utterance.rate = Number(rate);
    const voice = window.speechSynthesis.getVoices().find(v => /^zh[-_](CN|Hans)/i.test(v.lang));
    if (voice) utterance.voice = voice;
    window.speechSynthesis.speak(utterance);
    return status;
}"""


def _notice(text):
    return f'<div class="notice" role="status" aria-live="polite">{escape(text)}</div>' if text else ''


def _target_panel(text: str, index: str, reading=None):
    """Keep context when sandhi changes the selected character's pronunciation."""
    return spotlight(text, index, reading)


def prepare_lesson(text, saved_id=None, meaning=None, reading=None, provenance=None, allow_online=False):
    """One data path for Scan, Type, search, ASR and Saved."""
    text = (text or '').strip()
    if not clean_hanzi(text):
        raise ValueError('Enter Chinese text, scan a photo, or explicitly translate an English search.')
    saved = get_entry(saved_id) if saved_id else None
    if saved and saved.hanzi != clean_hanzi(text):
        saved = None
    if saved:
        meaning, note = saved.meaning, 'Saved meaning · stored on this host.'
        if len(clean_hanzi(text))==1: reading=saved.written_pinyin
    elif meaning is not None:
        note = provenance or 'Online translation · review the meaning in context.'
    else:
        result = sentence_translation(text,allow_online=allow_online)
        meaning = result.text
        note = result.source
    choices = character_choices(text, reading)
    vocabulary, words = vocabulary_view(text)
    return dict(text=text, choices=choices, meaning=meaning, reading=reading,
                note=note, vocabulary=vocabulary, words=words, saved_id=str(saved.id) if saved else None)


def _library_view():
    entries = list_entries()
    cards = '<div class="library-grid">' + ''.join(
        f'<article class="library-card"><div class="meta">{escape(e.kind.upper())} · '
        f'{e.practice_count} practice(s)</div>'
        f'<div class="hanzi" lang="zh-CN">{escape(e.hanzi)}</div>'
        f'<div class="reading">{escape(e.written_pinyin)}</div>'
        f'<div class="meaning">{escape(e.meaning)}</div></article>' for e in entries
    ) + '</div>' if entries else '<div class="library-empty">Your saved phrases will appear here.<br>Find a little Chinese worth keeping.</div>'
    choices = [(f'{e.hanzi} · {e.meaning}', str(e.id)) for e in entries]
    return gr.update(choices=choices, value=str(entries[0].id) if entries else None), cards, f'{len(entries)} saved item(s)'


async def _listen(text, voice, rate, mode):
    if not clean_hanzi(text):
        return None, 'Choose a phrase or character first.', ''
    if mode == 'Browser voice':
        return None, 'Playing the browser Mandarin voice. Available voices depend on your device.', text
    try:
        audio = await synthesize_neural(text, voice=voice, rate=float(rate))
        return audio, 'Natural Mandarin is ready. Tap play if your browser blocks autoplay.', ''
    except (RuntimeError, ValueError) as exc:
        return None, f'{exc} Trying the browser Mandarin voice; availability depends on your device.', text


def _transcribe(audio):
    if audio is None:
        return '', 'Record a phrase first, then transcribe it.'
    if importlib.util.find_spec('sherpa_onnx' if backend_name()=='sherpa-onnx' else 'faster_whisper') is None:
        return '', 'The speech dependency is missing in this interpreter. Run python -m pip install -r requirements.txt (or requirements-asr.txt for optional Whisper). You can use Type or Scan now.'
    try:
        from hanpi_core.asr import transcribe
        text = transcribe(audio)
        if not clean_hanzi(text):
            return '', 'No Chinese speech was recognised. Try again, or use Type.'
        return text, 'Check the transcript, then use this text. Transcription does not grade pronunciation.'
    except (ValueError,RuntimeError) as exc:
        return '', str(exc)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception('Mandarin transcription failed')
        return '', f'Transcription failed ({type(exc).__name__}). Run scripts/check_environment.py in this app’s interpreter, or use a corrected transcript.'

def _pitch_figure(xs: np.ndarray, ys: np.ndarray, expected_tone: int):
    if not len(xs):
        return None
    fig, ax = plt.subplots(figsize=(8, 3.3))
    fig.patch.set_facecolor("#fbf8f3")
    ax.set_facecolor("#fbf8f3")
    ax.plot(xs, ys, color="#b8663b", linewidth=3, label="Your measured pitch")
    refs = {
        1: [0, 0, 0, 0, 0], 2: [-2.4, -1.5, -.6, 1, 2.6],
        3: [1.5, -1.2, -2.2, -1.3, .8], 4: [2.7, 1.6, 0, -1.8, -3.3],
    }
    if expected_tone in refs:
        reference = np.interp(xs, np.linspace(0, 1, 5), refs[expected_tone])
        reference -= float(np.median(reference))
        ax.plot(xs, reference, color="#6c8c90", linewidth=2, linestyle="--",
                label="Schematic expected tone (not voice-matched)")
    ax.axhline(0, color="#b5a99b", alpha=.5, linewidth=1)
    ax.set_xlabel("Position within voiced syllable")
    ax.set_ylabel("Pitch (semitones relative to median)")
    ax.set_xlim(0, 1)
    ax.legend(loc="lower left", fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    plt.close(fig)
    return fig

def _practice_result(audio, text, selected_index, use_asr=False, reading=None):
    syllables = get_syllables(text, reading)
    try:
        index = int(selected_index)
        if not 0 <= index < len(syllables):
            raise ValueError
        syllable = syllables[index]
    except (ValueError, TypeError):
        return 'Choose a character first.', None, '', False
    try:
        score = analyze_tone(audio)
    except ValueError as exc:
        return f"### Try a clearer sound\n\n{exc}", None, '', False
    expected = syllable.expected_tone
    matched = expected != 5 and score.detected == expected
    if expected == 5:
        heading = 'Neutral tone is not automatically graded.'
    elif score.detected is None:
        heading = 'Keep going — try a clearer sound.'
    elif matched:
        heading = 'Your tone shape looks close.'
    elif expected==3 and score.detected==1:
        heading = 'A steady attempt — third tones can stay low.'
    else:
        heading = 'Good try — let’s shape it together.'
    feedback = (f'### {heading}\n\n{PRACTICE_TIPS[expected]}\n\n'
                '*Practice guidance, not a pronunciation grade.*')
    transcript = _transcribe(audio)[0] if use_asr else ''
    return feedback, _pitch_figure(score.times, score.semitones, expected), transcript, matched


def _assess(audio, text, selected_index, use_asr=False):
    return _practice_result(audio, text, selected_index, use_asr)[:3]


def _assess_and_track(audio, text, selection, use_asr, saved_id, reading=None):
    feedback, chart, transcript, matched = _practice_result(audio, text, selection, use_asr, reading)
    saved = get_entry(saved_id)
    if matched and saved and saved.hanzi == clean_hanzi(text):
        mark_practiced(saved_id)
    return feedback, chart, transcript


def _heading(eyebrow, title, description):
    return (f'<div class="screen-heading"><p class="eyebrow">{escape(eyebrow)}</p>'
            f'<h1>{escape(title)}</h1><p>{escape(description)}</p></div>')


def _translate_phrase(text, previous):
    try:
        return translate_online(text), 'Online translation · review before saving.', _notice('Translation ready.')
    except (ValueError, RuntimeError) as exc:
        fallback=lookup_meaning(text)
        return (previous or fallback.text), (gr.skip() if previous else f'{fallback.source} · {fallback.note}'), _notice(f'{exc} Offline dictionary results remain available.')


def build_app():
    with gr.Blocks(title='Hanpi · snap, translate, learn!', analytics_enabled=False) as demo:
        phrase = gr.State('')
        lesson_reading = gr.State(None)
        lookup_candidates = gr.State({})
        lookup_query = gr.State('')
        lookup_page = gr.State(0)
        selected = gr.State(None)
        active_saved = gr.State(None)
        origin = gr.State('Scan')
        stage = gr.State('results')
        use_asr = gr.State(False)
        with gr.Row():
            gr.HTML('<header id="brand"><div class="brand-mark" aria-hidden="true"><span class="brand-glyph">汉</span><span class="brand-tone">ˇ</span></div>'
                    '<div><div class="wordmark">hanpi<span class="wordmark-dot">.</span></div><div class="tagline">snap, translate, learn!</div></div></header>')

        with gr.Row(elem_id='search-row'):
            search = gr.Textbox(label='Search Chinese or English', placeholder='Search Chinese or English…',
                                lines=1, max_lines=1, show_label=False, container=False, scale=5, min_width=140, elem_id='search-box')
            search_button = gr.Button('Search', scale=0, min_width=82, elem_id='search-button')
        search_mode = gr.Radio(['Chinese → English','English → Chinese','Pinyin lookup'], value='Chinese → English', label='Search mode', interactive=True, elem_id='search-mode')
        notice = gr.HTML('' if dictionary_status().ready else _notice(dictionary_status().message), elem_id='notice')
        with gr.Column(visible=False, elem_classes='surface',elem_id='lookup-results') as lookup_view:
            lookup_summary = gr.Markdown('')
            lookup_groups = [gr.Radio(choices=[], value=None, label=f'Tone {i+1}', interactive=True, visible=False,elem_id=f'lookup-tone-{i+1}') for i in range(5)]
            more_results = gr.Button('More matches', visible=False, variant='secondary')
        english_button = gr.Button('Translate English online', visible=False)
        with gr.Column() as scan_view:
            gr.HTML('<section class="welcome-panel">' +
                    _heading('YOUR NEXT LITTLE DISCOVERY', 'Chinese is everywhere.', 'Snap a sign, find its meaning, then say it out loud.') +
                    '<div class="hanpi-friend" aria-hidden="true"><span class="friend-eye friend-eye-left"></span>'
                    '<span class="friend-eye friend-eye-right"></span><span class="friend-smile"></span>'
                    '<span class="friend-note">nǐ hǎo!</span><span class="friend-spark">✳</span></div></section>')
            with gr.Column(elem_classes='surface'):
                photo = gr.Image(label='Scan Chinese', type='pil', sources=['upload', 'webcam', 'clipboard'], height=245,
                                 elem_id='photo', webcam_options=gr.WebcamOptions(mirror=False, constraints={'facingMode':'environment'}))
                gr.Markdown('Point your camera at Chinese text, or drop an image here.', elem_classes='microcopy')
                scan_button = gr.Button('Recognize characters', variant='primary')
                ocr_status = gr.Markdown('')
                ocr_review = gr.Textbox(label='Verify detected Chinese before learning', lines=3, visible=False)
                ocr_alternatives = gr.Dropdown(choices=[], label='Other OCR candidates · verify carefully', visible=False, interactive=True)
                confirm_ocr = gr.Button('Use verified text', variant='primary', visible=False)
                gr.Markdown('Camera and microphone need HTTPS on your phone. Upload works too.', elem_classes='microcopy')
            type_shortcut = gr.Button('Type a phrase instead', variant='secondary')

        with gr.Column(visible=False) as type_view:
            gr.HTML(_heading('START WITH A FEW WORDS', 'A phrase to make your own.', 'Type Chinese and let curiosity take it from there.'))
            with gr.Column(elem_classes='surface'):
                typed = gr.Textbox(label='Chinese phrase', placeholder='例如：我喜欢咖啡', lines=3)
                learn_button = gr.Button('Learn this phrase', variant='primary')
                gr.Examples([['我喜欢咖啡'], ['图书馆在哪里'], ['你好'], ['北京大学']], inputs=[typed], label='A little inspiration', elem_id='examples')

        with gr.Column(visible=False) as speak_view:
            gr.HTML(_heading('FROM YOUR VOICE', 'Say something in Chinese.', 'Turn a recording into a phrase to explore.'))
            with gr.Column(elem_classes='surface'):
                speech_input = gr.Audio(sources=['microphone','upload'], type='numpy', format='wav', label='Record a Chinese phrase')
                transcribe_button = gr.Button('Use my recording', variant='secondary')
                asr_status = gr.Markdown('Say a short phrase, then use your recording.', elem_classes='microcopy')
                spoken_text = gr.Textbox(label='Recognized Chinese', lines=2, interactive=False)
                use_text = gr.Button('Use this text', variant='primary')

        with gr.Column(visible=False) as saved_view:
            gr.HTML(_heading('YOUR LITTLE COLLECTION', 'Worth coming back to.', 'Words and phrases you’ve made a connection with.'))
            saved_total = gr.Markdown('')
            saved_cards = gr.HTML('')
            with gr.Column(elem_classes='surface'):
                saved_choice = gr.Dropdown(choices=[], label='Choose a saved word or phrase', interactive=True)
                with gr.Row():
                    reopen_button = gr.Button('Practise again', variant='primary')
                    remove_button = gr.Button('Remove star', variant='secondary')
                gr.Markdown('Stored on this host. Shared by anyone signed in to this demo; not per-user cloud sync.', elem_classes='microcopy')

        with gr.Column(visible=False, elem_id='lesson') as lesson_view:
            back_to_input = gr.Button('← Back', size='sm', scale=0, min_width=0, elem_id='new-phrase')
            with gr.Column() as reading_view:
                gr.HTML('<div class="screen-heading" id="lesson-heading"><p class="eyebrow">A PHRASE, A LITTLE POSSIBILITY</p>'
                        '<h2>Let’s learn this phrase</h2></div>')
                characters = gr.Radio(choices=[], value=None, label='Characters and pinyin', show_label=False,
                                      interactive=True, container=False, elem_id='character-choices')
                gr.Markdown('Tap a character or its pinyin to practise. Colour shows the spoken tone.', elem_id='tone-legend')
            with gr.Column() as phrase_info:
                with gr.Column(elem_classes='surface'):
                    meaning = gr.Textbox(label='English translation', show_label=False, container=False, lines=2, interactive=False, elem_id='meaning')
                    meaning_note = gr.Markdown('', elem_id='meaning-note')
                    with gr.Row():
                        listen_phrase = gr.Button('Listen to phrase', min_width=0, variant='primary')
                        save_phrase = gr.Button('☆ Save phrase', min_width=0, variant='secondary')
                    whole_button = gr.Button('Try the whole phrase', variant='secondary')
                    translate_button = gr.Button('Translate full sentence', variant='secondary')
                    with gr.Accordion('Voice & speed', open=False, elem_classes='voice-options'):
                        voice = gr.Radio([('Female', DEFAULT_VOICE), ('Male', 'zh-CN-YunxiNeural')],value=DEFAULT_VOICE,label='Voice')
                        speed = gr.Radio([('0.75×',.75),('1×',1.),('1.25×',1.25)],value=1.,label='Speed')
                        mode = gr.Radio(['Natural voice (online)','Browser voice'],value='Natural voice (online)',label='Playback')
                    with gr.Accordion('Change Chinese text', open=False,visible=False):
                        editor = gr.Textbox(label='Chinese text (editable)', lines=3)
                        update_button = gr.Button('Update phrase', variant='secondary')
                        gr.Markdown('Learning may use an online service for the full English translation.', elem_classes='microcopy')
                with gr.Accordion('Words in this phrase',open=False):
                    gr.Markdown('#### A few words to know', elem_id='vocab-heading')
                    vocabulary = gr.HTML('')
                    word_choice = gr.Dropdown(choices=[], label='Word from this phrase', interactive=True, allow_custom_value=True)
                    word_meaning = gr.Textbox(label='Word meaning (editable)')
                    save_word = gr.Button('☆ Save word', variant='secondary')

            with gr.Column(visible=False) as focus_view:
                focus_card = gr.HTML('', elem_id='spotlight-card')
                current_speech = gr.Textbox(visible=False)
                with gr.Row() as focus_actions:
                    listen_character = gr.Button('Listen', min_width=0, variant='primary')
                    try_button = gr.Button('Try it', min_width=0, variant='secondary')
                with gr.Column(visible=False, elem_classes='surface') as recording_view:
                    mini_target = gr.HTML('',elem_id='mini-target')
                    recording = gr.Audio(sources=['microphone','upload'], type='numpy', format='wav', label='Say this syllable', elem_id='practice-recording')
                    check_button = gr.Button('Check my tone', variant='primary')
                    feedback = gr.Markdown('', elem_id='feedback')
                    retry_button = gr.Button('Try again', variant='secondary')
                    with gr.Column(visible=False):
                        chart = gr.Plot(label='Measured pitch and schematic target')
                        transcript = gr.Textbox(label='Optional transcript · not a pronunciation grade', interactive=False)
                        gr.Markdown('A pitch shape cannot independently verify consonants or vowels.', elem_classes='microcopy')
                with gr.Row():
                    back_to_phrase = gr.Button('Back to phrase', min_width=0, variant='secondary')
                    next_button = gr.Button('Next character', min_width=0, variant='secondary')
                star_character = gr.Button('☆ Save this character', size='sm')

            with gr.Column(visible=False, elem_classes='surface') as whole_view:
                whole_target = gr.Markdown('### Try the whole phrase')
                with gr.Column() as whole_capture:
                    listen_whole = gr.Button('Listen to full phrase', variant='primary')
                    whole_recording = gr.Audio(sources=['microphone','upload'], type='numpy', format='wav', label='Record my attempt', elem_id='whole-recording')
                    review_button = gr.Button('Review recording', variant='secondary')
                    whole_feedback = gr.Markdown('Transcription compares words, not tones. Recordings stay local.', elem_classes='microcopy')
                whole_prepare = gr.Button('Prepare Mandarin speech model (~75 MB)', variant='secondary',visible=False)
                heard_text = gr.State('')
                compare_button = gr.Button('Compare corrected transcript',variant='secondary',visible=False)
                comparison = gr.HTML('')
                flagged_characters = gr.Radio(choices=[],label='Words to try again · tap one',interactive=True,visible=False,elem_id='word-differences')
                record_again = gr.Button('Record again',visible=False,variant='secondary')
                with gr.Row():
                    finish_button = gr.Button('Finish practice', variant='primary')
                    whole_back = gr.Button('Back to phrase', min_width=0, variant='secondary')

            with gr.Column(visible=False) as completion_view:
                gr.HTML('<div class="completion"><div class="seal" aria-hidden="true">✓</div><h2>Nice practice session!</h2><p>Want to save this phrase?</p></div>')
                complete_save = gr.Button('☆ Save phrase', min_width=0, variant='primary')
                with gr.Row():
                    again_button = gr.Button('Practice again', min_width=0, variant='secondary')
                    done_button = gr.Button('Done', min_width=0, variant='secondary')

            reference_audio = gr.Audio(label='Mandarin reference', interactive=False, autoplay=True, visible=False)
            voice_status = gr.Markdown('', elem_classes='microcopy')
            fallback_text = gr.Textbox(visible=False)

        with gr.Row(elem_id='bottom-nav'):
            nav_buttons = {
                name: gr.Button(name, min_width=0, elem_classes=['nav-item', 'nav-active'] if name=='Scan' else ['nav-item'])
                for name in ('Scan','Type','Speak','Saved')
            }


        # A single transition target keeps input methods and result state consistent.
        lesson_outputs = [stage,reading_view,focus_actions,mini_target,whole_target,whole_capture,record_again,translate_button,phrase, lesson_reading, selected, lookup_view, active_saved, origin, editor, characters,
                          meaning, meaning_note, vocabulary, word_choice, word_meaning, lesson_view,
                          scan_view, type_view, speak_view, saved_view, phrase_info, focus_view,
                          recording_view, whole_view, completion_view, focus_card, current_speech,
                          recording, feedback, chart, transcript, reference_audio, voice_status,
                          fallback_text, notice, english_button, search, whole_recording, whole_feedback, heard_text, comparison, flagged_characters, *nav_buttons.values()]

        def show_phrase():
            return {stage:'results',lesson_view:gr.update(visible=True,elem_classes=['stage-results']),reading_view:gr.update(visible=True),focus_card:gr.update(visible=True),focus_actions:gr.update(visible=True),phrase_info:gr.update(visible=True), focus_view:gr.update(visible=False),
                    recording_view:gr.update(visible=False), whole_view:gr.update(visible=False),
                    completion_view:gr.update(visible=False), characters:gr.update(value=None), selected:None,
                    recording:None, feedback:'', chart:None, transcript:'',
                    reference_audio:gr.update(value=None, visible=False), voice_status:'', fallback_text:''}

        def open_lesson(raw, source='Type', saved_id=None, supplied_meaning=None, reading=None, provenance=None):
            try:
                data = prepare_lesson(raw, saved_id, supplied_meaning, reading, provenance,allow_online=True)
            except (ValueError, RuntimeError) as exc:
                return {notice:_notice(str(exc)), english_button:gr.update(visible=bool((raw or '').strip()) and not clean_hanzi(raw)), search:raw or ''}
            values = show_phrase()
            values.update({translate_button:gr.update(visible=not data['note'].startswith('Full translation') and len(clean_hanzi(data['text']))>1),phrase:data['text'], lesson_reading:data['reading'], lookup_view:gr.update(visible=False), origin:source, editor:data['text'], active_saved:data['saved_id'],
                           characters:gr.update(choices=data['choices'], value=None),
                           meaning:data['meaning'], meaning_note:data['note'], vocabulary:data['vocabulary'],
                           word_choice:gr.update(choices=data['words'], value=None), word_meaning:'',
                           lesson_view:gr.update(visible=True,elem_classes=['stage-results']),whole_target:f'### {data["text"]}', scan_view:gr.update(visible=False),
                           type_view:gr.update(visible=False), speak_view:gr.update(visible=False), saved_view:gr.update(visible=False),
                           notice:'', english_button:gr.update(visible=False), whole_recording:None, whole_feedback:'Listen, record, then check what we heard.', heard_text:'', comparison:'', flagged_characters:gr.update(choices=[],value=None,visible=False)})
            values.update(nav_state(source))
            return values

        def scan(image):
            try:
                result=recognize_image(image)
                choices=[(f'{c.text} · {c.variant}',c.text) for c in result.candidates]
                message='We found possible text — please verify and edit it before creating a lesson.'
                if result.uncertain: message+=' The image or competing readings make this uncertain.'
                return {ocr_review:gr.update(value=result.best.text,visible=True),
                        ocr_alternatives:gr.update(choices=choices,value=result.best.text,visible=len(choices)>1),
                        confirm_ocr:gr.update(visible=True),ocr_status:message,notice:''}
            except (ValueError,RuntimeError) as exc:
                return {ocr_review:gr.update(value='',visible=False),ocr_alternatives:gr.update(visible=False),
                        confirm_ocr:gr.update(visible=False),ocr_status:str(exc),notice:_notice(str(exc))}

        def lookup(raw, direction, page=0):
            raw = (raw or '').strip()
            if direction != 'Pinyin lookup' and clean_hanzi(raw):
                values=open_lesson(raw, 'Type')
                values[search_mode]='Chinese → English'
                return values
            try:
                result = search_pinyin(raw, page) if direction == 'Pinyin lookup' else search_english(raw, page)
            except ValueError as exc:
                return {notice:_notice(str(exc))}
            candidates={c.key:c for group in result.groups for c in group}
            values={lookup_view:gr.update(visible=True), lesson_view:gr.update(visible=False,elem_classes=['stage-input']), scan_view:gr.update(visible=False),
                    type_view:gr.update(visible=False),speak_view:gr.update(visible=False),saved_view:gr.update(visible=False),lookup_query:raw, lookup_page:page,
                    lookup_candidates:candidates, notice:'',
                    english_button:gr.update(visible=direction!='Pinyin lookup'),
                    search_mode:'Pinyin lookup' if direction=='Pinyin lookup' else 'English → Chinese',
                    lookup_summary:f'**{result.source}** · {result.total} match(es) for **{escape(raw)}**. '
                                   f'Page {page+1}: showing {result.shown}. Choose a reading to learn. '
                                   + ('Unmarked pinyin includes all written tones; multi-syllable entries group by their first written tone.' if direction=='Pinyin lookup' else 'Common word lookup works offline.'),
                    more_results:gr.update(visible=result.has_more)}
            for i,(component,group) in enumerate(zip(lookup_groups,result.groups)):
                label=f'Tone {i+1}' if direction=='Pinyin lookup' else 'English → Chinese matches'
                if i==4 and direction=='Pinyin lookup': label='Tone 5 · neutral'
                values[component]=gr.update(choices=[(c.label,c.key) for c in group], value=None, visible=bool(group), label=label)
            if not candidates:
                values[notice]=_notice('No offline match found. Check spelling or try a shorter word. Online translation is an optional extra.')
            return values

        def choose_candidate(key, candidates):
            candidate=candidates.get(key)
            if candidate is None:
                return {notice:_notice('Run Search again to choose a current result.')}
            reading=candidate.numbered if len(candidate.hanzi)==1 else None
            return open_lesson(candidate.hanzi,'Type',supplied_meaning=candidate.meaning,
                               reading=reading, provenance=f'{candidate.source} lookup · {candidate.pinyin}; verify in context.')

        def english_search(raw):
            try:
                return open_lesson(translate_to_chinese(raw), 'Type', supplied_meaning=raw)
            except (ValueError, RuntimeError):
                values=lookup(raw,'English → Chinese')
                values[notice]=_notice('Online translation is unavailable. These offline dictionary results are still usable.')
                return values

        def nav_state(destination):
            return {button:gr.update(elem_classes=['nav-item','nav-active'] if name==destination else ['nav-item'])
                    for name, button in nav_buttons.items()}

        def navigate(destination):
            choice_update, cards, total = _library_view()
            values = {lookup_view:gr.update(visible=False), scan_view:gr.update(visible=destination=='Scan'), type_view:gr.update(visible=destination=='Type'),
                    speak_view:gr.update(visible=destination=='Speak'), saved_view:gr.update(visible=destination=='Saved'),
                    lesson_view:gr.update(visible=False,elem_classes=['stage-input']), notice:'', english_button:gr.update(visible=False),
                    saved_choice:choice_update, saved_cards:cards, saved_total:total,
                    reference_audio:gr.update(value=None, visible=False), voice_status:'', fallback_text:''}
            values.update(nav_state(destination))
            return values

        def focus(text, index, reading=None):
            choices = character_choices(text, reading)
            try:
                position = int(str(index).split(':')[0])
                if not 0 <= position < len(choices):
                    raise ValueError
            except (TypeError, ValueError):
                return show_phrase()
            html, spoken = _target_panel(text, str(position), reading)
            return {stage:'focus',lesson_view:gr.update(visible=True,elem_classes=['stage-focus']),reading_view:gr.update(visible=True),focus_actions:gr.update(visible=True),characters:gr.update(value=choices[position][1]), selected:str(position), focus_card:gr.update(value=html,visible=True), current_speech:spoken,
                    phrase_info:gr.update(visible=False), focus_view:gr.update(visible=True),
                    recording_view:gr.update(visible=False), whole_view:gr.update(visible=False), completion_view:gr.update(visible=False),
                    recording:None, feedback:'', chart:None, transcript:'', notice:'',
                    reference_audio:gr.update(value=None, visible=False), voice_status:'', fallback_text:''}

        def complete():
            values = show_phrase()
            values.update({stage:'complete',lesson_view:gr.update(visible=True,elem_classes=['stage-complete']),reading_view:gr.update(visible=False),phrase_info:gr.update(visible=False), completion_view:gr.update(visible=True)})
            return values

        def next_character(text, index, reading=None):
            try:
                position = int(index) + 1
            except (ValueError, TypeError):
                position = 0
            return focus(text, str(position), reading) if position < len(get_syllables(text, reading)) else complete()

        def save_item(kind, text, gloss, reading=None):
            try:
                item = save_entry(kind, clean_hanzi(text), gloss,reading=reading)
                choice_update, cards, total = _library_view()
                values = {notice:_notice(f'Saved {item.hanzi} to Starred.'), saved_choice:choice_update, saved_cards:cards, saved_total:total}
                if kind == 'sentence':
                    values[active_saved] = str(item.id)
                return values
            except (ValueError, OSError) as exc:
                return {notice:_notice(str(exc))}

        def keep_word(text, word, gloss):
            if not word or word != clean_hanzi(word) or word not in clean_hanzi(text):
                return {notice:_notice('Choose a Chinese word from the current phrase first.')}
            return save_item('word', word, gloss)

        def keep_character(text, index, reading=None):
            try:
                syllables = get_syllables(text, reading)
                position = int(index)
                if not 0 <= position < len(syllables):
                    raise ValueError
                word = syllables[position].hanzi
                return save_item('word', word, meaning_for(word),syllables[position].written_pinyin)
            except (TypeError, ValueError):
                return {notice:_notice('Choose a character first.')}

        def reopen(entry_id):
            item = get_entry(entry_id)
            return open_lesson(item.hanzi, 'Saved', str(item.id)) if item else {notice:_notice('Choose a saved item first.')}

        def remove(entry_id):
            if not delete_entry(entry_id):
                return {notice:_notice('Choose a saved item first.')}
            choice_update, cards, total = _library_view()
            return {notice:_notice('Star removed.'), saved_choice:choice_update, saved_cards:cards, saved_total:total}

        def translate(text, previous):
            result=sentence_translation(text,allow_online=True)
            return result.text,result.source,''

        async def listen(text, reference_voice, playback_speed, playback_mode):
            path, message, browser_text = await _listen(text, reference_voice, playback_speed, playback_mode)
            return gr.update(value=path, visible=bool(path)), message, browser_text

        def whole_practice():
            values = show_phrase()
            values.update({whole_capture:gr.update(visible=True),whole_target:gr.update(visible=True),record_again:gr.update(visible=False),comparison:'',flagged_characters:gr.update(choices=[],value=None,visible=False),whole_recording:None,stage:'whole',lesson_view:gr.update(visible=True,elem_classes=['stage-whole']),reading_view:gr.update(visible=False),phrase_info:gr.update(visible=False), whole_view:gr.update(visible=True)})
            return values

        def compare_words(text,heard):
            try:
                html,choices=comparison_view(text,heard)
                return html,gr.update(choices=choices,value=None,visible=bool(choices))
            except ValueError as exc:
                return _notice(str(exc)),gr.update(choices=[],value=None,visible=False)

        def review_whole(audio,text):
            if audio is None:
                return '', 'Record your attempt first. You can play it back and choose a character to practise.', '', gr.update(choices=[],value=None,visible=False),gr.update(visible=True),gr.update(visible=True),gr.update(visible=False),'whole'
            heard,message=_transcribe(audio)
            if not heard:
                return '',message,'',gr.update(choices=[],value=None,visible=False),gr.update(visible=True),gr.update(visible=True),gr.update(visible=False),'whole'
            html,choices=compare_words(text,heard)
            return heard,message,html,choices,gr.update(visible=False),gr.update(visible=False),gr.update(visible=True),'whole-feedback'

        def start_recording(text,index,reading):
            values=focus(text,index,reading)
            syllables=get_syllables(text,reading)
            selected_syllable=syllables[int(index)]
            values.update({stage:'record',lesson_view:gr.update(visible=True,elem_classes=['stage-record']),
                           reading_view:gr.update(visible=False),focus_card:gr.update(visible=False),focus_actions:gr.update(visible=False),
                           recording_view:gr.update(visible=True),mini_target:f'<b>{escape(selected_syllable.hanzi)}</b> · {escape(selected_syllable.spoken_pinyin)}'})
            return values

        def back(current,source,text,index,reading):
            if current=='results': return navigate(source)
            if current=='record': return focus(text,index,reading)
            if current=='whole-feedback': return whole_practice()
            return show_phrase()

        route_outputs = [lookup_view,scan_view,type_view,speak_view,saved_view,lesson_view,notice,english_button,*nav_buttons.values(),saved_choice,saved_cards,saved_total,reference_audio,voice_status,fallback_text]
        focus_outputs = [whole_capture,whole_target,record_again,comparison,flagged_characters,whole_recording,stage,lesson_view,reading_view,focus_actions,mini_target,characters,selected,focus_card,current_speech,phrase_info,focus_view,recording_view,whole_view,completion_view,recording,feedback,chart,transcript,notice,reference_audio,voice_status,fallback_text]
        save_outputs = [notice,saved_choice,saved_cards,saved_total,active_saved]
        for destination, button in nav_buttons.items():
            button.click(lambda dest=destination:navigate(dest), outputs=route_outputs)
        type_shortcut.click(lambda:navigate('Type'), outputs=route_outputs)
        stage_events=[]
        stage_events.append(back_to_input.click(back,inputs=[stage,origin,phrase,selected,lesson_reading],outputs=list(dict.fromkeys(route_outputs+focus_outputs))))
        lookup_outputs = lesson_outputs + [lookup_summary,lookup_candidates,lookup_query,lookup_page,more_results,search_mode,*lookup_groups]
        more_results.click(lambda query,direction,page:lookup(query,direction,page+1), inputs=[lookup_query,search_mode,lookup_page], outputs=lookup_outputs)
        for group in lookup_groups:
            group.input(choose_candidate, inputs=[group,lookup_candidates], outputs=lesson_outputs)
        opening_events = []
        opening_events.append(search_button.click(lookup, inputs=[search,search_mode], outputs=lookup_outputs))
        opening_events.append(search.submit(lookup, inputs=[search,search_mode], outputs=lookup_outputs))
        opening_events.append(english_button.click(english_search, inputs=search, outputs=lookup_outputs))
        opening_events.append(learn_button.click(lambda text:open_lesson(text,'Type'), inputs=typed, outputs=lesson_outputs))
        opening_events.append(typed.submit(lambda text:open_lesson(text,'Type'), inputs=typed, outputs=lesson_outputs))
        scan_button.click(scan, inputs=photo, outputs=[ocr_review,ocr_alternatives,confirm_ocr,ocr_status,notice])
        ocr_alternatives.input(lambda text:text or '',inputs=ocr_alternatives,outputs=ocr_review)
        opening_events.append(confirm_ocr.click(lambda text:open_lesson(text,'Scan'),inputs=ocr_review,outputs=lesson_outputs))
        opening_events.append(update_button.click(open_lesson, inputs=[editor,origin,active_saved], outputs=lesson_outputs))
        transcribe_button.click(_transcribe, inputs=speech_input, outputs=[spoken_text,asr_status])
        opening_events.append(use_text.click(lambda text:open_lesson(text,'Speak'), inputs=spoken_text, outputs=lesson_outputs))
        focus_event = characters.input(focus, inputs=[phrase,characters,lesson_reading], outputs=focus_outputs)
        focus_event.then(fn=None, inputs=None, outputs=None, js="""() => {
            document.getElementById('lesson')?.scrollIntoView({
                behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block:'start'});
        }""")
        stage_events.append(next_button.click(next_character, inputs=[phrase,selected,lesson_reading], outputs=focus_outputs))
        stage_events.append(back_to_phrase.click(show_phrase, outputs=focus_outputs))
        stage_events.append(whole_back.click(show_phrase, outputs=focus_outputs))
        stage_events.append(whole_button.click(whole_practice, outputs=focus_outputs))
        stage_events.append(try_button.click(start_recording,inputs=[phrase,selected,lesson_reading],outputs=focus_outputs))
        check_button.click(_assess_and_track, inputs=[recording,phrase,selected,use_asr,active_saved,lesson_reading], outputs=[feedback,chart,transcript])
        retry_button.click(lambda:(None,'Ready when you are. Record one clear syllable.',None,''), outputs=[recording,feedback,chart,transcript])
        review_button.click(review_whole, inputs=[whole_recording,phrase], outputs=[heard_text,whole_feedback,comparison,flagged_characters,whole_capture,whole_target,record_again,stage])
        stage_events.append(record_again.click(whole_practice,outputs=focus_outputs))
        compare_button.click(compare_words, inputs=[phrase,heard_text], outputs=[comparison,flagged_characters])
        stage_events.append(flagged_characters.input(focus, inputs=[phrase,flagged_characters,lesson_reading], outputs=focus_outputs))
        stage_events.append(finish_button.click(complete, outputs=focus_outputs))
        stage_events.append(done_button.click(show_phrase, outputs=focus_outputs))
        stage_events.append(again_button.click(lambda text,reading:focus(text,'0',reading), inputs=[phrase,lesson_reading], outputs=focus_outputs))
        translate_button.click(translate, inputs=[phrase,meaning], outputs=[meaning,meaning_note,notice])
        word_choice.input(lambda word:meaning_for(word or ''), inputs=word_choice, outputs=word_meaning)
        save_word.click(keep_word, inputs=[phrase,word_choice,word_meaning], outputs=save_outputs)
        star_character.click(keep_character, inputs=[phrase,selected,lesson_reading], outputs=save_outputs)
        for button in (save_phrase,complete_save):
            button.click(lambda text,gloss,reading:save_item('sentence',text,gloss,reading), inputs=[phrase,meaning,lesson_reading], outputs=save_outputs)
        opening_events.append(reopen_button.click(reopen, inputs=saved_choice, outputs=lesson_outputs))
        remove_button.click(remove, inputs=saved_choice, outputs=save_outputs)
        demo.load(_library_view, outputs=[saved_choice,saved_cards,saved_total])
        for button, text in ((listen_phrase,phrase),(listen_character,current_speech),(listen_whole,phrase)):
            event = button.click(listen, inputs=[text,voice,speed,mode], outputs=[reference_audio,voice_status,fallback_text])
            event.then(fn=None, inputs=[fallback_text,speed,voice_status], outputs=voice_status, js=BROWSER_SPEECH)
        for event in opening_events + stage_events:
            event.then(fn=None, inputs=None, outputs=None, js="""() => {
                const lesson = document.getElementById('lesson');
                if (lesson && lesson.getClientRects().length) lesson.scrollIntoView({
                    behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block:'start'});
            }""")
    return demo


def make_theme():
    theme=gr.themes.Soft(primary_hue='orange',secondary_hue='stone',neutral_hue='stone',
                         font=['Inter','ui-sans-serif','system-ui']).set(
        body_background_fill='#fffaf0',body_text_color='#17364c',body_text_color_subdued='#4b6473',
        background_fill_primary='#fffaf0',background_fill_secondary='#ffffff',
        block_background_fill='#ffffff',block_label_background_fill='#fff4df',
        block_label_text_color='#17364c',block_title_text_color='#17364c',
        input_background_fill='#ffffff',color_accent='#ff950a')
    values=theme.to_dict()['theme']
    # Match every dark token to its light counterpart, including built-in audio.
    mirrored={key:values[key[:-5]] for key in values if key.endswith('_dark') and key[:-5] in values}
    return theme.set(**mirrored)


def launch_app():
    """Local by default. Remote mode must retain authentication for shared SQLite data."""
    share = os.environ.get('HANPI_SHARE','0') == '1'
    host = os.environ.get('HANPI_HOST','127.0.0.1')
    remote = share or host not in ('127.0.0.1','localhost')
    username, password = os.environ.get('HANPI_DEMO_USER'), os.environ.get('HANPI_DEMO_PASSWORD')
    if remote and (not username or not password or len(password) < 10):
        raise RuntimeError('Remote mode shares one local Starred library. Set HANPI_DEMO_USER and HANPI_DEMO_PASSWORD (at least 10 characters) before enabling it.')
    print(f'Hanpi Python: {sys.executable}',flush=True)
    print(dictionary_status().message, flush=True)
    return build_app().launch(server_name=host, server_port=int(os.environ.get('PORT','7860')), share=share,
                              auth=(username,password) if remote else None, inbrowser=not share, show_error=True,
                              theme=make_theme(), css=CSS)


if __name__ == '__main__':
    launch_app()
