# Hanpi · 汉拼

**See it. Say it. Learn it.** A desktop-first Mandarin pronunciation studio built for the Hiya Voice AI Challenge.

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
.venvScriptsActivate.ps1
python -m pip install -r requirements.txt
python app.py
```

On macOS/Linux, create a Python 3.11 virtual environment and run the same install/app commands. Open http://127.0.0.1:7860 in the browser. Microphone permission is needed for voice recording.

Pasting or dropping images works in the photo input. Correct any OCR mistakes in the editable Hanzi field before practising. The home screen starts with 你好 solely as a sample.

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

Choose **★ Star word** or **★ Star sentence** to save Hanzi, written pinyin, spoken pinyin and a meaning. Visit the **Starred** tab to view vocabulary cards, reopen an entry for practice, or remove it. Successful practice attempts on saved items increase their counter.

Storage: `data/hanpi_library.sqlite3`. The database survives restarts but is not synced across devices and is excluded from Git. To back up your collection, copy this file.

## Tests

```bash
python -m pip install pytest
python -m pytest -q
```

Local testing covers dictionary logic, basic tone rules, SQLite memory and synthetic pitch contours. **Testing with actual Windows microphones, real Chinese photos, Mandarin voices, and native speakers remains necessary.** GitHub Actions includes tests and UI import smoke checks.

## Technical architecture and licensing

- **RapidOCR**: Chinese text recognition using local ONNX models.
- **PyPinyin**: written pinyin and basic context/tone sandhi.
- **pycccedict**: CC-CEDICT Mandarin-English vocabulary.
- **Parselmouth/Praat**: acoustic pitch extraction and shape-based tone coaching.
- **deep-translator**: optional, explicit online translation.
- **Gradio**: desktop-first web UI and microphone capture.
- **SQLite**: persistent private starred library.

The code uses packages through their documented APIs, instead of pasting in other projects' implementation code. Design and architecture were informed by [Tone.me](https://github.com/tone-me/tone-me) (MIT), [Mandarin Speech Coach](https://github.com/anton-dergunov/mandarin-speech-coach), [PyPinyin](https://github.com/mozillazg/python-pinyin), [RapidOCR](https://github.com/RapidAI/RapidOCR), and [pycccedict](https://github.com/patrickpei/pycccedict).

**CC-CEDICT content is CC BY-SA 4.0**, credited to the CC-CEDICT contributors and MDBG. The dataset is installed separately through pycccedict; it is not copied into this repository. See third-party dependency repositories for their code licences. See [ai.md](ai.md) for AI usage and [TASKS.md](TASKS.md) for the project checklist.

## Privacy

OCR and pitch analysis run locally. The optional online translation button shares the selected Chinese text with a third-party translation provider only when clicked. Browser speech synthesis may use device or platform services. No user accounts or telemetry are part of this prototype.


## Phone camera and natural Mandarin voice

The Gradio app is now phone-responsive and already accepts webcam/camera images, image uploads, and pasted photos. See [iPhone HTTPS setup](docs/PHONE_DEMO.md) to launch a **temporary password-protected https://*.gradio.live** testing link from your Windows laptop. A publicly hosted/permanent website is not yet deployed.

There are now **two reference voice choices**:
- Browser voice: device/platform Mandarin speech, no extra setup; naturalness depends on device.
- Optional neural voice: online service via [edge-tts](https://github.com/rany2/edge-tts) using Mandarin voices Xiaoxiao, Yunxi and Xiaoyi, with adjustable playback speed and an audio player. **Only generated when you click a neural voice button.** Neural output sends the requested text to a third-party speech service and can fail when offline; the browser voice stays available.

Neural speech synthesis is not the same as speech transcription or automatic grading. Current pronunciation assessment still covers one isolated syllable at a time.

**Mobile access isn't automatically active after installing Hanpi.** You must start the host server and open its HTTPS URL on your phone. For a permanent production site, add a hosted backend and independent user storage; the existing SQLite collection is shared by anyone authenticated to the same temporary demo.
