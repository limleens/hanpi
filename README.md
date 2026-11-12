# Hanpi · 汉拼

**snap, translate, learn!**

Hanpi turns Chinese text around you into a short speaking lesson. Scan a menu, upload a photo, or type a phrase; see its pinyin and English meaning, listen to Mandarin, then try saying it yourself.

Built for the **Hiya Voice AI Challenge · Real-Time Assistance** track, using Python and Gradio. It is for Mandarin learners who want to understand real-world text and practise saying it before using it in conversation.

**Why voice?** Looking up a translation helps you understand a word. Hearing it and speaking it are different skills. A keyboard cannot capture a learner's spoken attempt: Hanpi uses audio to show what speech recognition heard and to offer experimental pitch coaching for individual syllables.

## Live demo

**[Open Hanpi on your phone or laptop](https://194438d21ac5106fd4.gradio.live)** — no installation needed.

- **Username:** `hanpi-demo`
- **Password:** `hanzipinyin`

Sign in with this shared demo account and allow microphone/camera access when prompted. Start with **Type → 我喜欢咖啡 → Learn this phrase**, or scan a photo of Chinese text.

This temporary demo is available while the host computer and app are running. If the link is unavailable, follow the local setup below. Restarting the hosted session can change its URL.

## Get the submission version

The submission is on **`feat/mobile-first-redesign`**; `main` may contain an older version. PR #2 remains open for review.

```bash
git clone --branch feat/mobile-first-redesign --single-branch https://github.com/limleens/hanpi.git
cd hanpi
```

If you received a ZIP, extract it and open a terminal in the folder containing `app.py` and `requirements.txt`; skip the clone commands. Reviewers can use either the repository checkout or the source ZIP.

## Setup and run

Use **Python 3.11**. The default setup needs no API key, GPU, Node.js build, or separate Tesseract installation. Internet is needed to install packages and download the recommended SenseVoice speech model once (about 163 MB). The small speech detector is bundled. Initial setup takes longer than later launches.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/prepare_asr.py
.\.venv\Scripts\python.exe scripts/check_environment.py --strict --asr
.\.venv\Scripts\python.exe app.py
```

### macOS / Linux

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/prepare_asr.py
.venv/bin/python scripts/check_environment.py --strict --asr
.venv/bin/python app.py
```

Open **http://127.0.0.1:7860** on the computer running Hanpi. These commands use the virtual environment's Python explicitly, so activation is optional and packages are installed in the same interpreter that runs the app.

For later launches, just run the last command. To update an existing checkout on the submission branch, stop Hanpi with Ctrl+C, run `git pull --ff-only origin feat/mobile-first-redesign`, then start it again.

## Try the prototype

1. Choose **Type**, enter `我喜欢咖啡`, and tap **Learn this phrase**. You should see the characters, tone-coloured pinyin, and **“I like coffee.”**
2. Tap a character to open **Spotlight**. Tap **Listen**, then **Try it** and say that syllable. Stopping the microphone checks the recording; uploaded WAV files use **Check my voice**. Recording pauses reference/tutor playback to reduce self-echo.
3. Read **You said** beside the target. Hanpi shows the actual recognized text and its pinyin, with separate measured pitch guidance. Matching words get **Words match!** and **Continue →**. Homophones such as 蒜/算 (both suàn) get **Sounds match!**; a different recognized character alone does not fail speaking practice. For single-syllable drills, one short ending such as le/er is tolerated and labelled as ignored. The base syllable and acoustic pitch are checked separately; the full recognized transcript stays visible. You can retry or go back.
4. Return to the phrase and choose **Try the whole phrase**. Listen, record, and compare the target with the transcript. Possible missing or changed words are highlighted. Tap a word for its target-versus-heard breakdown and practise it in Spotlight.
5. Try **Scan** with a photo of Chinese text. Check the proposed OCR text, then tap **Use verified text**. Save a phrase or word with the star and reopen it under **Saved**.

The top search supports **Chinese → English**, **English → Chinese**, and **Pinyin lookup**. Try English `eat`, or pinyin `ma`, `ma3`, and `mǎ`. Common English/pinyin lookup uses the offline dictionary; `ma` returns candidates grouped by tone. **Speak** can also turn a Mandarin recording into a lesson.

**Hǔ, your speaking buddy**, guides practice with short spoken responses. After each try, choose **Continue →**, **Try phrase**, or retry. Corrective guidance describes the observed pitch and can play a Mandarin example. **Spoken tips** mutes automatic narration; **Hear tip** replays it. English tips and their Mandarin examples use browser/device voices; if autoplay is blocked, tap Hear tip. This is a guided dialogue, not open-ended voice chat. [See the tutor layout](docs/images/tutor-practice.png).

**Voice & speed** on the Results page offers Female/Male reference voices, playback speed, and browser speech as a fallback. Natural Mandarin playback requires an online service and is generated only when you tap Listen.

## Open it on a phone

Phone camera and microphone access need **HTTPS**. Follow [phone setup](docs/PHONE_DEMO.md) to create a temporary, password-protected Gradio share link. The host computer and app must stay running.

The current reviewer login is listed under **Live demo** above; no account registration is needed. For your own deployment, configure `HANPI_DEMO_USER` and `HANPI_DEMO_PASSWORD`. The browser normally stays signed in after refreshing. Restarting a share session prints a new URL; update the demo link above if it changes.

The sign-in page and app use the same bundled Fredoka and Plus Jakarta Sans fonts, rounded cards, and readable light palette, including on devices set to dark mode.

## How it works

| Stage | Implementation |
| --- | --- |
| Read a photo | RapidOCR with local ONNX models; preprocessing for small/coloured text and editable confirmation |
| Explain the text | PyPinyin readings and basic tone sandhi; UTF-8 CC-CEDICT lookup and word segmentation |
| Translate a phrase | Small offline phrase/menu cache, then bounded online translation; labelled dictionary fallback |
| Play Mandarin | Online edge-tts reference audio, with browser speech fallback |
| Filter recording noise | Bundled Silero VAD, conservative endpoint padding, and rejection of silence/DC and obvious steady electronic tones |
| Hear the learner | Local SenseVoice via sherpa-onnx; the original compact Zipformer remains a compatibility option. The target is never supplied as a recognition prompt |
| Guide practice | Evidence-led tutor dialogue with browser English/Mandarin speech and an original SVG tiger |
| Compare an attempt | OpenCC normalizes script variants; character alignment identifies possible transcript differences |
| Coach one syllable | Praat/Parselmouth measures pitch; an experimental rule-based classifier describes the contour |
| Save vocabulary | SQLite on the host computer |

`app.py` wires the Gradio screens and callbacks. `hanpi_core/` contains OCR, dictionary/search, translation, speech recognition, pitch analysis, comparison and storage. `hanpi_ui/` contains presentation and branding. Tests live in `tests/`.

## Scope and limitations

- **Speech recognition is fallible.** A matching transcript means the recognized words match; it does not certify pronunciation. Pinyin beside a transcript is the reading of its recognized spelling, not an acoustically measured tone.
- **Pitch coaching is experimental and isolated-syllable only.** It can be uncertain, especially for short recordings and third/neutral tones. Hanpi does not grade every tone in a sentence or detect consonant/phoneme errors.
- **General translation and natural TTS need external services.** Common cached phrases and dictionary lookup work offline after installation. If general translation is unavailable, Hanpi labels approximate word meanings rather than presenting them as fluent English.
- **OCR needs checking.** Small, stylized or low-resolution text may be wrong. Original Traditional characters are retained; the learner confirms the detected text before starting a lesson.
- **This is a shared demo.** Saved items live in `data/hanpi_library.sqlite3` and survive restarts. Everyone authenticated to that app instance shares the same library; there is no per-user cloud sync or permanent hosting.

## Tests and troubleshooting

Using the same virtual environment as above, on Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/check_environment.py --strict --asr
```

On macOS/Linux, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.

**Latest validation: 172 tests passed** on Python 3.11/Linux, plus server startup and browser walkthroughs at phone and desktop widths. Browser checks include actual local speech recognition of public human Mandarin recordings, matching/mismatching transcripts, Spotlight, OCR, saved data, and authenticated sign-in. The user also reported successful phone launch and OCR of their actual menu. A Chromium fake microphone fed a public human WAV exercised actual capture, automatic checking, single-word recognition and playback suppression. Speech-output calls were stubbed to check language/queuing/mute behavior. Physical-phone microphone accuracy and audible playback have not been independently measured; this is not a native-speaker accuracy study. See [QA evidence](docs/REDESIGN_QA.md).

If dictionary or speech setup fails, run the diagnostic command above. Startup prints the Python executable and dictionary status. Reinstall dependencies and prepare the model with **that same interpreter**. The recommended SenseVoice model downloads from the official sherpa-onnx GitHub release and is checksum-checked. Existing installations automatically use SenseVoice once it is prepared, or retain their compact model. Run `scripts/prepare_asr.py` once after updating to install SenseVoice; `--profile compact` installs the smaller original model. `HANPI_ASR_PROFILE=accurate` or `compact` explicitly selects a profile; the default `auto` prefers prepared SenseVoice. The diagnostic reports the selected profile and speech detector. Optional Faster-Whisper setup is separate; it is not required for the submitted default path.

If online playback fails, choose **Browser voice** under Voice & speed. If the microphone is unavailable on a phone, check HTTPS and browser permission; a WAV upload can also exercise the speech path.

## Data, AI use and credits

OCR, speech recognition and pitch analysis run on the computer hosting Hanpi. Recordings are processed there, not sent to an LLM or the translation/TTS services. When accessed through a share link, phone recordings travel to that host over HTTPS. Gradio may temporarily cache uploaded media; this prototype does not implement a production retention policy.

Creating a lesson may send selected Chinese text to Google Translate/MyMemory for translation. Listening with natural voice sends the selected text to the Edge speech service. Browser speech may use platform services. The app disables Gradio analytics. The source ZIP excludes the local database, personal recordings/credentials, virtual environment and large downloaded recognition models. The small MIT-licensed speech detector is included. The shared reviewer demo login is intentionally provided in this README.

See [ai.md](ai.md) for AI tools, models, development assistance and limitations. CC-CEDICT content is credited to its contributors/MDBG under **CC BY-SA 4.0** and installed through pycccedict. SenseVoice/FunASR recognition weights have [separate upstream model terms](https://github.com/modelscope/FunASR/blob/main/MODEL_LICENSE); the original compact Zipformer release is **Apache-2.0**. Silero VAD is **MIT** (notice included with the bundled detector); edge-tts is **LGPLv3**. Bundled brand fonts include their **SIL Open Font** licences in [hanpi_ui/fonts](hanpi_ui/fonts). Other libraries retain their upstream licences.


## Speech research and focused regression

The new speech-filtered SenseVoice pipeline matched all **14 focused cases**, compared with 11 for the old pipeline: one public human word crop, quieter/noisy/padded variants, a genuine repeated attempt, and synthetic non-speech. Raw SenseVoice alone hallucinated words on several noise cases, which is why speech detection runs first. This is a small engineering regression set, **not 100% general ASR accuracy**. Transcripts are never silently deduplicated; actual repeated speech remains visible. See [research, model choices and results](docs/VOICE_RESEARCH.md) and [QA evidence](docs/REDESIGN_QA.md).
