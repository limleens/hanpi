# Hanpi · 汉拼

**snap, translate, learn!** A mobile-first Mandarin learning app built with Python and Gradio for the Hiya Voice AI Challenge.

Take or paste an image of Chinese writing, extract the Hanzi with local OCR, read colour-coded pinyin, hear reference speech, practice an isolated syllable through the microphone, and save vocabulary to your offline ★ Starred collection.

## What works and what is experimental

| Feature | Implementation | Status |
| --- | --- | --- |
| Paste, drag/drop, upload a Chinese image | Gradio image input + RapidOCR ONNX (local) | Implemented; verify OCR result |
| Arbitrary-length recognised Hanzi | No 24-character truncation | Implemented; very long input may be slower |
| Mandarin pinyin and basic third-tone sandhi | PyPinyin phrase dictionary | Implemented; polyphonic words require review |
| English word meanings | CC-CEDICT via pycccedict | Implemented; dictionary definitions are contextual approximations |
| Longer text meanings | Word-by-word dictionary gloss | Implemented; **not** fluent sentence translation |
| Online translation | deep-translator, opt-in button | Implemented; depends on external service |
| Browser Mandarin reference speech | Web Speech API | Implemented; voice quality varies by browser/device |
| Microphone → pitch contour → tone feedback | Praat via Parselmouth | Experimental **one syllable at a time**, not a validated score |
| Optional transcription | Faster-Whisper | Additional install; NOT used to grade tone |
| Starred words/sentences | SQLite persisted locally | Implemented |

**Important:** Hanpi does not accurately grade whole spoken paragraphs or detect consonant/vowel mistakes yet. Mandarin sounds are context-dependent and no automatic tone score should be treated as definitive.

## Run it locally

Python **3.11** recommended. On Windows PowerShell:

```powershell
git clone https://github.com/limleens/hanpi.git
cd hanpi
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

On macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:7860 in the browser. The UI uses Gradio 6; no Node build or GPU is needed. Phone camera/microphone access requires HTTPS, not your computer's localhost URL.

## Scan → Results → Spotlight → Practice

- **Scan**: upload, paste, drop an image, or select the rear-camera source. Tap **Recognize characters** to open Results. Use **Edit text & translate** to correct the OCR and **Update phrase** to apply it.
- **Type**: enter Chinese and tap **Learn this phrase**, or use the search bar. English search offers an explicit **Translate English online** action; typing/searching alone sends no translation request.
- **Results**: explore aligned, tone-coloured Hanzi/pinyin, an editable meaning and key vocabulary. Offline meanings are clearly labelled dictionary definitions or approximate word glosses. Fluent online translation is opt-in under **Edit text & translate**.
- **Spotlight**: tap a character or its pinyin (keyboard selection also works). Other characters dim. **Listen** uses natural Mandarin by default and falls back to browser speech if the service fails. Sandhi examples retain phrase context.
- **Try it**: record/upload one isolated syllable, then **Check my tone**. Retry, advance to the next character, or return to the phrase. The pitch chart stays inside **Pitch detail**.
- **Try the whole phrase**: record and play your own attempt back. Optional transcription can show recognised text; it does not grade sentence tones. Finish with **Save phrase**, **Practice again**, or **Done**.
- **Speak**: optional Whisper transcription produces editable Chinese that opens the same Results view. Without Whisper, use Type or Scan. Install `requirements-asr.txt` and allow the initial model download to enable it.
- **Saved**: reopen a saved item for practice or remove its star. You can also keep a word or a selected character.

**Settings** groups Female/Male neural voices, 0.75×/1×/1.25× speed, browser-voice preference, and optional practice transcription. Settings persist while navigating within the current session. Nothing generates online speech before you tap Listen.

The bottom navigation stays accessible on phones; desktop uses the same calm, centred layout. Animations respect reduced-motion preferences.

## Try something other than 你好

Test phrases such as:

- 北京大学 — Beijing University (word-by-word dictionary gloss may show the two parts)
- 我喜欢咖啡 — I like coffee
- 图书馆在哪里 — Where is the library?
- 今天的天气很好 — The weather is nice today

Full OCR and pinyin output are no longer limited to 24 characters. A long recognised passage is displayed in a scrollable tone-colour panel. The character selector still scores **one spoken syllable** at a time, so choose one target rather than recording a paragraph.

For longer text, CC-CEDICT's greedy word matching creates a labelled **gloss**, not a confident fluent translation. You can explicitly click the online translation button to request more natural English, then edit the result. Online translation supports up to 2,500 Hanzi per request; it raises an error rather than silently dropping characters. OCR/pinyin do not have this translation-service limit.

For pronunciation, compare 妈 (mā), 麻 (má), 马 (mǎ), and 骂 (mà) as isolated single-character tests. Remember that 你好 is written nǐ hǎo but pronounced ní hǎo with third-tone sandhi.

## Starred collection

Choose **Save phrase**, **Keep a word → Save word**, or **Save this character** to store Hanzi, written/spoken pinyin and an editable meaning. Visit **Saved** to reopen an entry or remove it. A matching isolated-syllable pitch contour increases the active saved phrase’s practice counter; uncertain/mismatching attempts do not. Historical counts remain intact. This counter is not a validated pronunciation score.

Storage: `data/hanpi_library.sqlite3`. The database survives restarts but is not synced across devices and is excluded from Git. To back up your collection, copy this file.

## Tests

```bash
python -m pip install pytest
python -m pytest -q
```

Automated tests cover dictionary logic, tone rules, SQLite memory, synthetic pitch contours and redesign state/error paths. See [redesign QA](docs/REDESIGN_QA.md) for the browser walkthrough, screenshots and remaining checks. **Testing with actual Windows microphones, real Chinese photos, Mandarin voices, and native speakers remains necessary.** GitHub Actions includes tests and UI import smoke checks.

## Technical architecture and licensing

- **RapidOCR**: Chinese text recognition using local ONNX models.
- **PyPinyin**: written pinyin and basic context/tone sandhi.
- **pycccedict**: CC-CEDICT Mandarin-English vocabulary.
- **Parselmouth/Praat**: acoustic pitch extraction and shape-based tone coaching.
- **deep-translator**: optional, explicit online translation.
- **Gradio**: mobile-first shared Results/Spotlight UI, accessible character controls and microphone capture.
- **SQLite**: persistent private starred library.

The code uses packages through their documented APIs, instead of pasting in other projects' implementation code. Design and architecture were informed by [Tone.me](https://github.com/tone-me/tone-me) (MIT), [Mandarin Speech Coach](https://github.com/anton-dergunov/mandarin-speech-coach), [PyPinyin](https://github.com/mozillazg/python-pinyin), [RapidOCR](https://github.com/RapidAI/RapidOCR), and [pycccedict](https://github.com/patrickpei/pycccedict).

**CC-CEDICT content is CC BY-SA 4.0**, credited to the CC-CEDICT contributors and MDBG. The dataset is installed separately through pycccedict; it is not copied into this repository. See third-party dependency repositories for their code licences. See [ai.md](ai.md) for AI usage and [TASKS.md](TASKS.md) for the project checklist.

## Privacy

OCR and pitch analysis run locally. The optional online translation button shares the selected Chinese text with a third-party translation provider only when clicked. Browser speech synthesis may use device or platform services. No user accounts or telemetry are part of this prototype.


## Phone camera and natural Mandarin voice

The Gradio app is now phone-responsive and already accepts webcam/camera images, image uploads, and pasted photos. See [iPhone HTTPS setup](docs/PHONE_DEMO.md) to launch a **temporary password-protected https://*.gradio.live** testing link from your Windows laptop. A publicly hosted/permanent website is not yet deployed.

There are now **two reference voice choices**:
- Natural voice (default): online [edge-tts](https://github.com/rany2/edge-tts) with Xiaoxiao (Female) or Yunxi (Male), configurable speed and an audio player. **Generated only when you tap Listen.** Selected text goes to a third-party service, which can fail or be unavailable.
- Browser voice: choose it in Settings for device/platform Mandarin speech. It also serves as the fallback after a neural-service failure. Available Mandarin voices and audible playback depend on the device.

Neural speech synthesis is not the same as speech transcription or automatic grading. Current pronunciation assessment still covers one isolated syllable at a time.

**Mobile access isn't automatically active after installing Hanpi.** You must start the host server and open its HTTPS URL on your phone. For a permanent production site, add a hosted backend and independent user storage; the existing SQLite collection is shared by anyone authenticated to the same temporary demo.
