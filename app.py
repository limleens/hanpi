"""Hanpi — snap, translate, learn! Run with: python app.py."""
from __future__ import annotations

from html import escape
from pathlib import Path
import importlib.util
import os

import gradio as gr
import matplotlib.pyplot as plt
import numpy as np

from hanpi_core.ocr import extract_hanzi
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


def _target_panel(text: str, index: str):
    """Keep context when sandhi changes the selected character's pronunciation."""
    return spotlight(text, index)


def prepare_lesson(text, saved_id=None, meaning=None):
    """One data path for Scan, Type, search, ASR and Saved."""
    text = (text or '').strip()
    if not clean_hanzi(text):
        raise ValueError('Enter Chinese text, scan a photo, or explicitly translate an English search.')
    choices = character_choices(text)
    saved = get_entry(saved_id) if saved_id else None
    if saved and saved.hanzi != clean_hanzi(text):
        saved = None
    if saved:
        meaning, note = saved.meaning, 'Saved meaning · stored on this host.'
    elif meaning is not None:
        note = 'Online translation · review the meaning in context.'
    else:
        result = lookup_meaning(text)
        meaning = result.text
        note = f'{result.source} · {result.note}'
    vocabulary, words = vocabulary_view(text)
    return dict(text=text, choices=choices, meaning=meaning,
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
    if importlib.util.find_spec('faster_whisper') is None:
        return '', 'Speech input needs the optional Whisper install (requirements-asr.txt). You can use Type or Scan now.'
    try:
        from hanpi_core.asr import transcribe
        text = transcribe(audio)
        if not clean_hanzi(text):
            return '', 'No Chinese speech was recognised. Try again, or use Type.'
        return text, 'Check the transcript, then use this text. Transcription does not grade pronunciation.'
    except Exception:
        return '', 'Transcription is unavailable. Check the optional model download, or use Type or Scan.'

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

def _practice_result(audio, text, selected_index, use_asr=False):
    syllables = get_syllables(text)
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
        return f"### Couldn't judge that recording.\n\n{exc}", None, '', False
    expected = syllable.expected_tone
    matched = expected != 5 and score.detected == expected
    if expected == 5:
        heading = 'Neutral tone is not automatically graded.'
    elif score.detected is None:
        heading = "Couldn't judge that recording."
    elif matched:
        heading = 'Your tone shape looks close.'
    else:
        heading = "Let's shape that tone."
    feedback = (f'### {heading}\n\n{PRACTICE_TIPS[expected]}\n\n'
                f'Expected **{TONES[expected]}** · observed **{TONES.get(score.detected, "uncertain")}**. '
                f'{score.reason}\n\n'
                '*Experimental pitch coaching for one syllable. This does not verify consonants, '
                'vowels or whole-sentence pronunciation.*')
    transcript = _transcribe(audio)[0] if use_asr else ''
    return feedback, _pitch_figure(score.times, score.semitones, expected), transcript, matched


def _assess(audio, text, selected_index, use_asr=False):
    return _practice_result(audio, text, selected_index, use_asr)[:3]


def _assess_and_track(audio, text, selection, use_asr, saved_id):
    feedback, chart, transcript, matched = _practice_result(audio, text, selection, use_asr)
    saved = get_entry(saved_id)
    if matched and saved and saved.hanzi == clean_hanzi(text):
        mark_practiced(saved_id)
    return feedback, chart, transcript


def _heading(eyebrow, title, description):
    return (f'<div class="screen-heading"><p class="eyebrow">{escape(eyebrow)}</p>'
            f'<h1>{escape(title)}</h1><p>{escape(description)}</p></div>')


def build_app():
    with gr.Blocks(title='Hanpi · snap, translate, learn!', analytics_enabled=False) as demo:
        phrase = gr.State('')
        selected = gr.State(None)
        active_saved = gr.State(None)
        origin = gr.State('Scan')
        settings_open = gr.State(False)
        with gr.Row():
            gr.HTML('<header id="brand"><div class="brand-mark" aria-hidden="true"><span class="brand-glyph">汉</span><span class="brand-tone">ˇ</span></div>'
                    '<div><div class="wordmark">hanpi<span class="wordmark-dot">.</span></div><div class="tagline">snap, translate, learn!</div></div></header>')
            settings_toggle = gr.Button('Settings', scale=0, min_width=88, elem_id='settings-toggle')
        with gr.Row(elem_id='search-row'):
            search = gr.Textbox(label='Search Chinese or English', placeholder='Search Chinese or English…',
                                lines=1, max_lines=1, show_label=False, container=False, scale=5, min_width=140, elem_id='search-box')
            search_button = gr.Button('Search', scale=0, min_width=82, elem_id='search-button')
        notice = gr.HTML('', elem_id='notice')
        english_button = gr.Button('Translate English online', visible=False)
        with gr.Column(visible=False, elem_id='settings-panel') as settings:
            gr.Markdown('### Make it sound like you\nNatural voice sends the selected text to an online speech service only when you tap Listen.')
            voice = gr.Radio([('Female', DEFAULT_VOICE), ('Male', 'zh-CN-YunxiNeural')], value=DEFAULT_VOICE, label='Mandarin voice')
            speed = gr.Radio([('0.75×', .75), ('1×', 1.), ('1.25×', 1.25)], value=1., label='Speed')
            mode = gr.Radio(['Natural voice (online)', 'Browser voice'], value='Natural voice (online)', label='Playback')
            use_asr = gr.Checkbox(False, label='Use optional Whisper transcripts during practice')
            gr.Markdown('Pitch coaching is experimental and only evaluates one isolated syllable. It does not detect phoneme errors.\n\n'
                        'Saved vocabulary is stored on this host, shared across authenticated sessions. It is not cloud sync.', elem_classes='microcopy')

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
                transcribe_button = gr.Button('Transcribe recording', variant='secondary')
                asr_status = gr.Markdown('Optional Whisper transcription needs requirements-asr.txt and a model download. Type and Scan work without it.', elem_classes='microcopy')
                spoken_text = gr.Textbox(label='Check your transcript', lines=2)
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
            back_to_input = gr.Button('← New phrase', size='sm', scale=0, min_width=0, elem_id='new-phrase')
            gr.HTML('<div class="screen-heading" id="lesson-heading"><p class="eyebrow">A PHRASE, A LITTLE POSSIBILITY</p>'
                    '<h2>Let’s learn this phrase</h2></div>')
            characters = gr.Radio(choices=[], value=None, label='Characters and pinyin', show_label=False,
                                  interactive=True, container=False, elem_id='character-choices')
            gr.Markdown('Tap a character or its pinyin to practise. Colour shows the spoken tone.', elem_id='tone-legend')
            with gr.Column() as phrase_info:
                with gr.Column(elem_classes='surface'):
                    meaning = gr.Textbox(label='English meaning (editable)', show_label=False, container=False, lines=2, elem_id='meaning')
                    meaning_note = gr.Markdown('', elem_id='meaning-note')
                    with gr.Row():
                        listen_phrase = gr.Button('Listen to phrase', variant='primary')
                        save_phrase = gr.Button('☆ Save phrase', variant='secondary')
                    whole_button = gr.Button('Try the whole phrase', variant='secondary')
                    with gr.Accordion('Edit text & translate', open=False):
                        editor = gr.Textbox(label='Chinese text (editable)', lines=3)
                        update_button = gr.Button('Update phrase', variant='secondary')
                        gr.Markdown('Online translation sends this phrase to an external provider only when clicked.', elem_classes='microcopy')
                        translate_button = gr.Button('Translate phrase online', variant='secondary')
                gr.Markdown('#### A few words to know', elem_id='vocab-heading')
                vocabulary = gr.HTML('')
                with gr.Accordion('Keep a word', open=False):
                    word_choice = gr.Dropdown(choices=[], label='Word from this phrase', interactive=True, allow_custom_value=True)
                    word_meaning = gr.Textbox(label='Word meaning (editable)')
                    save_word = gr.Button('☆ Save word', variant='secondary')

            with gr.Column(visible=False) as focus_view:
                focus_card = gr.HTML('', elem_id='spotlight-card')
                current_speech = gr.Textbox(visible=False)
                with gr.Row():
                    listen_character = gr.Button('Listen', variant='primary')
                    try_button = gr.Button('Try it', variant='secondary')
                with gr.Column(visible=False, elem_classes='surface') as recording_view:
                    recording = gr.Audio(sources=['microphone','upload'], type='numpy', format='wav', label='Say this syllable', elem_id='practice-recording')
                    check_button = gr.Button('Check my tone', variant='primary')
                    feedback = gr.Markdown('', elem_id='feedback')
                    retry_button = gr.Button('Try again', variant='secondary')
                    with gr.Accordion('Pitch detail', open=False):
                        chart = gr.Plot(label='Measured pitch and schematic target')
                        transcript = gr.Textbox(label='Optional transcript · not a pronunciation grade', interactive=False)
                        gr.Markdown('A pitch shape cannot independently verify consonants or vowels.', elem_classes='microcopy')
                with gr.Row():
                    back_to_phrase = gr.Button('Back to phrase', variant='secondary')
                    next_button = gr.Button('Next character', variant='secondary')
                star_character = gr.Button('☆ Save this character', size='sm')

            with gr.Column(visible=False, elem_classes='surface') as whole_view:
                gr.Markdown('### Try the whole phrase\nListen, record, then play your recording back. Choose any character above to work on its tone.')
                listen_whole = gr.Button('Listen to full phrase', variant='primary')
                whole_recording = gr.Audio(sources=['microphone','upload'], type='numpy', format='wav', label='Record my attempt')
                review_button = gr.Button('Review recording', variant='secondary')
                whole_feedback = gr.Markdown('Whole-phrase tones are not automatically graded.', elem_classes='microcopy')
                with gr.Row():
                    finish_button = gr.Button('Finish practice', variant='primary')
                    whole_back = gr.Button('Back to phrase', variant='secondary')

            with gr.Column(visible=False) as completion_view:
                gr.HTML('<div class="completion"><div class="seal" aria-hidden="true">✓</div><h2>Nice practice session!</h2><p>Want to save this phrase?</p></div>')
                complete_save = gr.Button('☆ Save phrase', variant='primary')
                with gr.Row():
                    again_button = gr.Button('Practice again', variant='secondary')
                    done_button = gr.Button('Done', variant='secondary')

            reference_audio = gr.Audio(label='Mandarin reference', interactive=False, autoplay=True, visible=False)
            voice_status = gr.Markdown('', elem_classes='microcopy')
            fallback_text = gr.Textbox(visible=False)

        with gr.Row(elem_id='bottom-nav'):
            nav_buttons = {
                name: gr.Button(name, min_width=0, elem_classes=['nav-item', 'nav-active'] if name=='Scan' else ['nav-item'])
                for name in ('Scan','Type','Speak','Saved')
            }


        # A single transition target keeps input methods and result state consistent.
        lesson_outputs = [phrase, selected, active_saved, origin, editor, characters,
                          meaning, meaning_note, vocabulary, word_choice, word_meaning, lesson_view,
                          scan_view, type_view, speak_view, saved_view, phrase_info, focus_view,
                          recording_view, whole_view, completion_view, focus_card, current_speech,
                          recording, feedback, chart, transcript, reference_audio, voice_status,
                          fallback_text, notice, english_button, search, whole_recording, whole_feedback, *nav_buttons.values()]

        def show_phrase():
            return {phrase_info:gr.update(visible=True), focus_view:gr.update(visible=False),
                    recording_view:gr.update(visible=False), whole_view:gr.update(visible=False),
                    completion_view:gr.update(visible=False), characters:gr.update(value=None), selected:None,
                    recording:None, feedback:'', chart:None, transcript:'',
                    reference_audio:gr.update(value=None, visible=False), voice_status:'', fallback_text:''}

        def open_lesson(raw, source='Type', saved_id=None, supplied_meaning=None):
            try:
                data = prepare_lesson(raw, saved_id, supplied_meaning)
            except (ValueError, RuntimeError) as exc:
                return {notice:_notice(str(exc)), english_button:gr.update(visible=bool((raw or '').strip()) and not clean_hanzi(raw)), search:raw or ''}
            values = show_phrase()
            values.update({phrase:data['text'], origin:source, editor:data['text'], active_saved:data['saved_id'],
                           characters:gr.update(choices=data['choices'], value=None),
                           meaning:data['meaning'], meaning_note:data['note'], vocabulary:data['vocabulary'],
                           word_choice:gr.update(choices=data['words'], value=None), word_meaning:'',
                           lesson_view:gr.update(visible=True), scan_view:gr.update(visible=False),
                           type_view:gr.update(visible=False), speak_view:gr.update(visible=False), saved_view:gr.update(visible=False),
                           notice:'', english_button:gr.update(visible=False), whole_recording:None, whole_feedback:'Whole-phrase tones are not automatically graded.'})
            values.update(nav_state(source))
            return values

        def scan(image):
            try:
                text, engine = extract_hanzi(image)
            except (ValueError, RuntimeError) as exc:
                return {notice:_notice(str(exc))}
            values = open_lesson(text, 'Scan')
            values[notice] = _notice(f'Found Chinese characters with {engine}. Check the text before you practise.')
            return values

        def english_search(raw):
            try:
                return open_lesson(translate_to_chinese(raw), 'Type', supplied_meaning=raw)
            except (ValueError, RuntimeError) as exc:
                return {notice:_notice(str(exc))}

        def nav_state(destination):
            return {button:gr.update(elem_classes=['nav-item','nav-active'] if name==destination else ['nav-item'])
                    for name, button in nav_buttons.items()}

        def navigate(destination):
            choice_update, cards, total = _library_view()
            values = {scan_view:gr.update(visible=destination=='Scan'), type_view:gr.update(visible=destination=='Type'),
                    speak_view:gr.update(visible=destination=='Speak'), saved_view:gr.update(visible=destination=='Saved'),
                    lesson_view:gr.update(visible=False), notice:'', english_button:gr.update(visible=False),
                    saved_choice:choice_update, saved_cards:cards, saved_total:total,
                    reference_audio:gr.update(value=None, visible=False), voice_status:'', fallback_text:''}
            values.update(nav_state(destination))
            return values

        def focus(text, index):
            choices = character_choices(text)
            try:
                position = int(str(index).split(':')[0])
                if not 0 <= position < len(choices):
                    raise ValueError
            except (TypeError, ValueError):
                return show_phrase()
            html, spoken = _target_panel(text, str(position))
            return {characters:gr.update(value=choices[position][1]), selected:str(position), focus_card:html, current_speech:spoken,
                    phrase_info:gr.update(visible=False), focus_view:gr.update(visible=True),
                    recording_view:gr.update(visible=False), whole_view:gr.update(visible=False), completion_view:gr.update(visible=False),
                    recording:None, feedback:'', chart:None, transcript:'', notice:'',
                    reference_audio:gr.update(value=None, visible=False), voice_status:'', fallback_text:''}

        def complete():
            values = show_phrase()
            values.update({phrase_info:gr.update(visible=False), completion_view:gr.update(visible=True)})
            return values

        def next_character(text, index):
            try:
                position = int(index) + 1
            except (ValueError, TypeError):
                position = 0
            return focus(text, str(position)) if position < len(get_syllables(text)) else complete()

        def save_item(kind, text, gloss):
            try:
                item = save_entry(kind, clean_hanzi(text), gloss)
                choice_update, cards, total = _library_view()
                gr.Info(f'Saved {item.hanzi} to Starred.')
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

        def keep_character(text, index):
            try:
                syllables = get_syllables(text)
                position = int(index)
                if not 0 <= position < len(syllables):
                    raise ValueError
                word = syllables[position].hanzi
                return save_item('word', word, meaning_for(word))
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
            try:
                return translate_online(text), 'Online translation · review before saving.', _notice('Translation ready.')
            except (ValueError, RuntimeError) as exc:
                return previous, gr.skip(), _notice(str(exc))

        async def listen(text, reference_voice, playback_speed, playback_mode):
            path, message, browser_text = await _listen(text, reference_voice, playback_speed, playback_mode)
            return gr.update(value=path, visible=bool(path)), message, browser_text

        def whole_practice():
            values = show_phrase()
            values.update({phrase_info:gr.update(visible=False), whole_view:gr.update(visible=True)})
            return values

        def review_whole(audio, transcribe):
            if audio is None:
                return 'Record your attempt first. You can play it back and choose a character to practise.'
            if transcribe:
                text, message = _transcribe(audio)
                return f'Transcript: {text}\n\n{message}\n\nWhole-phrase tones are not graded.' if text else message
            return 'Listen back to your recording. Pick a character above for isolated-syllable feedback. Whole-phrase tones are not graded.'

        route_outputs = [scan_view,type_view,speak_view,saved_view,lesson_view,notice,english_button,*nav_buttons.values(),saved_choice,saved_cards,saved_total,reference_audio,voice_status,fallback_text]
        focus_outputs = [characters,selected,focus_card,current_speech,phrase_info,focus_view,recording_view,whole_view,completion_view,recording,feedback,chart,transcript,notice,reference_audio,voice_status,fallback_text]
        save_outputs = [notice,saved_choice,saved_cards,saved_total,active_saved]
        settings_toggle.click(lambda opened:(not opened, gr.update(visible=not opened)), inputs=settings_open, outputs=[settings_open,settings])
        for destination, button in nav_buttons.items():
            button.click(lambda dest=destination:navigate(dest), outputs=route_outputs)
        type_shortcut.click(lambda:navigate('Type'), outputs=route_outputs)
        back_to_input.click(navigate, inputs=origin, outputs=route_outputs)
        opening_events = []
        opening_events.append(search_button.click(lambda text:open_lesson(text,'Type'), inputs=search, outputs=lesson_outputs))
        opening_events.append(search.submit(lambda text:open_lesson(text,'Type'), inputs=search, outputs=lesson_outputs))
        opening_events.append(english_button.click(english_search, inputs=search, outputs=lesson_outputs))
        opening_events.append(learn_button.click(lambda text:open_lesson(text,'Type'), inputs=typed, outputs=lesson_outputs))
        opening_events.append(typed.submit(lambda text:open_lesson(text,'Type'), inputs=typed, outputs=lesson_outputs))
        opening_events.append(scan_button.click(scan, inputs=photo, outputs=lesson_outputs))
        opening_events.append(update_button.click(open_lesson, inputs=[editor,origin,active_saved], outputs=lesson_outputs))
        transcribe_button.click(_transcribe, inputs=speech_input, outputs=[spoken_text,asr_status])
        opening_events.append(use_text.click(lambda text:open_lesson(text,'Speak'), inputs=spoken_text, outputs=lesson_outputs))
        focus_event = characters.input(focus, inputs=[phrase,characters], outputs=focus_outputs)
        focus_event.then(fn=None, inputs=None, outputs=None, js="""() => {
            document.getElementById('character-choices')?.scrollIntoView({
                behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block:'start'});
        }""")
        next_button.click(next_character, inputs=[phrase,selected], outputs=focus_outputs)
        back_to_phrase.click(show_phrase, outputs=focus_outputs)
        whole_back.click(show_phrase, outputs=focus_outputs)
        whole_button.click(whole_practice, outputs=focus_outputs)
        try_button.click(lambda:gr.update(visible=True), outputs=recording_view)
        check_button.click(_assess_and_track, inputs=[recording,phrase,selected,use_asr,active_saved], outputs=[feedback,chart,transcript])
        retry_button.click(lambda:(None,'Ready when you are. Record one clear syllable.',None,''), outputs=[recording,feedback,chart,transcript])
        review_button.click(review_whole, inputs=[whole_recording,use_asr], outputs=whole_feedback)
        finish_button.click(complete, outputs=focus_outputs)
        done_button.click(show_phrase, outputs=focus_outputs)
        again_button.click(lambda text:focus(text,'0'), inputs=phrase, outputs=focus_outputs)
        translate_button.click(translate, inputs=[phrase,meaning], outputs=[meaning,meaning_note,notice])
        word_choice.input(lambda word:meaning_for(word or ''), inputs=word_choice, outputs=word_meaning)
        save_word.click(keep_word, inputs=[phrase,word_choice,word_meaning], outputs=save_outputs)
        star_character.click(keep_character, inputs=[phrase,selected], outputs=save_outputs)
        for button in (save_phrase,complete_save):
            button.click(lambda text,gloss:save_item('sentence',text,gloss), inputs=[phrase,meaning], outputs=save_outputs)
        opening_events.append(reopen_button.click(reopen, inputs=saved_choice, outputs=lesson_outputs))
        remove_button.click(remove, inputs=saved_choice, outputs=save_outputs)
        demo.load(_library_view, outputs=[saved_choice,saved_cards,saved_total])
        for button, text in ((listen_phrase,phrase),(listen_character,current_speech),(listen_whole,phrase)):
            event = button.click(listen, inputs=[text,voice,speed,mode], outputs=[reference_audio,voice_status,fallback_text])
            event.then(fn=None, inputs=[fallback_text,speed,voice_status], outputs=voice_status, js=BROWSER_SPEECH)
        for event in opening_events:
            event.then(fn=None, inputs=None, outputs=None, js="""() => {
                const lesson = document.getElementById('lesson');
                if (lesson && lesson.getClientRects().length) lesson.scrollIntoView({
                    behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block:'start'});
            }""")
    return demo


def launch_app():
    """Local by default. Remote mode must retain authentication for shared SQLite data."""
    share = os.environ.get('HANPI_SHARE','0') == '1'
    host = os.environ.get('HANPI_HOST','127.0.0.1')
    remote = share or host not in ('127.0.0.1','localhost')
    username, password = os.environ.get('HANPI_DEMO_USER'), os.environ.get('HANPI_DEMO_PASSWORD')
    if remote and (not username or not password or len(password) < 10):
        raise RuntimeError('Remote mode shares one local Starred library. Set HANPI_DEMO_USER and HANPI_DEMO_PASSWORD (at least 10 characters) before enabling it.')
    return build_app().launch(server_name=host, server_port=int(os.environ.get('PORT','7860')), share=share,
                              auth=(username,password) if remote else None, inbrowser=not share, show_error=True,
                              theme=gr.themes.Soft(primary_hue='orange', secondary_hue='stone', neutral_hue='stone',
                                                   font=['Inter','ui-sans-serif','system-ui']).set(
                                  color_accent='#dc644c', color_accent_soft='#f9e6db',
                                  body_background_fill='#faf7f2', block_background_fill='#fffdfa',
                                  input_background_fill='#fffdfa', block_label_background_fill='#fffdfa',
                                  block_label_text_color='#78675a'), css=CSS)


if __name__ == '__main__':
    launch_app()
