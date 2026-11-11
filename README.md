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
| Full phrase translation | Offline phrase cache + bounded online providers | Full English in Results; approximate dictionary fallback labelled |
| Online translation | Google Translate/MyMemory on lesson creation | Depends on external service; sends selected text only |
| Browser Mandarin reference speech | Web Speech API | Implemented; voice quality varies by browser/device |
| Microphone → pitch contour → tone feedback | Praat via Parselmouth | Experimental **one syllable at a time**, not a validated score |
| Mandarin sentence transcription | Local sherpa-onnx Mandarin model; optional Faster-Whisper backend | One-time model preparation; text comparison, NOT tone grading |
| English → Chinese and pinyin lookup | Offline CC-CEDICT reverse/pinyin indexes | eat → 吃; ma / ma3 / mǎ candidates grouped by written tone |
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
python scripts/check_environment.py --strict
python scripts/prepare_asr.py
python app.py
```

On macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/check_environment.py --strict
python scripts/prepare_asr.py
python app.py
```

Open http://127.0.0.1:7860 in the browser. The UI uses Gradio 6; no Node build or GPU is needed. Phone camera/microphone access requires HTTPS, not your computer's localhost URL.

## Scan → Results → Spotlight → Practice

- **Scan**: upload, paste, drop an image, or select the rear-camera source. Tap **Recognize characters**, inspect/edit **Verify detected Chinese before learning**, then tap **Use verified text**. Recognition is a proposal, not a guarantee. Small crops are upscaled and contrast/red-text variants are tried. Original Traditional characters are preserved. Results can still be edited afterward.
- **Type**: enter Chinese and tap **Learn this phrase**. The search bar has **Chinese → English**, **English → Chinese**, and **Pinyin lookup** modes. English `eat` returns selectable 吃 · chī offline. `ma` shows all written tones; `ma3` and `mǎ` select tone 3. **More matches** pages through remaining candidates. Unmarked/multi-syllable pinyin is not forced to one arbitrary reading. Online translation is an explicit optional enhancement; failures retain offline matches.
- **Results**: explore aligned, tone-coloured Hanzi/pinyin, an editable meaning and key vocabulary. Offline meanings are clearly labelled dictionary definitions or approximate word glosses. Full English translation appears directly: common phrases/menu items use the offline phrase cache, and other sentences try online providers. Any word-gloss fallback is clearly labelled.
- **Spotlight**: tap a character or its pinyin (keyboard selection also works). Other characters dim. **Listen** uses natural Mandarin by default and falls back to browser speech if the service fails. Sandhi examples retain phrase context.
- **Try it**: say one syllable. Stopping the microphone checks it automatically; uploads use **Check my voice**. **You said** shows the actual transcript and its pinyin beside the target. A matching word gets **Words match!** and **Continue →**; measured tone shape appears separately. Retry whenever you like.
- **Try the whole phrase**: listen, record, then see the target and **You said**. Uploads use **Check my words**. Possible missing or changed words are highlighted. Tap any word for its target-versus-heard Spotlight breakdown, then listen or practise it alone. **Back** returns to the sentence feedback without re-transcribing. Matching text gets **Words match. Nice work!** Speech recognition checks words, not sentence tones, and can mishear.
- **Speak**: the same local Mandarin model produces Chinese that opens Results. Prepare it once with `python scripts/prepare_asr.py` before launching the demo. After preparation, recognition needs no network, GPU or paid API. If unavailable, playback and manual Spotlight remain usable with an actionable error.
- **Saved**: reopen a saved item for practice or remove its star. You can also keep a word or a selected character.

**Voice & speed** is a small inline section on the Results page, with Female/Male, 0.75×/1×/1.25× and browser fallback. There is no separate Settings screen or transcript-edit/setup panel. Settings persist while navigating within the current session. Whole-sentence Review checks words automatically. Results, Spotlight, recording and feedback are separate stages; Back returns one stage and scrolls to its top. Nothing generates online speech before you tap Listen.

The bottom navigation stays accessible on phones; desktop uses the same calm, centred layout. Animations respect reduced-motion preferences.

## Dictionary and speech setup diagnostics

Use the **same Python interpreter** for installation, checks and `app.py`. At startup Hanpi prints that executable and CC-CEDICT status. `scripts/check_environment.py --strict` checks required packages and verifies real dictionary segmentation of 我 / 喜欢 / 咖啡. Add `--asr` after preparing the model to verify the actual speech engine.

CC-CEDICT 1.2.0 bundles its dataset, but its upstream loader omits UTF-8 encoding. Hanpi now explicitly reads it as UTF-8, fixing CP1252/ASCII-locale decoding failures. Initialization errors are logged with their actual cause and shown in Settings; a limited starter dictionary remains available instead of pretending the full dataset loaded.

The default speech engine is a compact **14M-parameter Mandarin Zipformer via sherpa-onnx**, downloaded from its official GitHub release (about 75 MB) with a pinned SHA-256 check. It runs on CPU and never receives the target sentence as a prompt. Model files stay in the user cache (`HANPI_ASR_CACHE` overrides it). The model/release is Apache-2.0; see [source and model](https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models).

Faster-Whisper remains an alternative: install `requirements-asr.txt`, set `HANPI_ASR_BACKEND=faster-whisper`, then run `python scripts/prepare_asr.py --model base`. That path needs Hugging Face access for its one-time download; the default Mandarin model does not. No ASR text comparison is a pronunciation score.

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
- **sherpa-onnx / Mandarin Zipformer**: local CPU sentence transcription; **OpenCC** normalizes script variants only for comparison. Faster-Whisper remains optional.
- **Gradio**: mobile-first shared Results/Spotlight UI, accessible character controls and microphone capture.
- **SQLite**: persistent private starred library.

The code uses packages through their documented APIs, instead of pasting in other projects' implementation code. Design and architecture were informed by [Tone.me](https://github.com/tone-me/tone-me) (MIT), [Mandarin Speech Coach](https://github.com/anton-dergunov/mandarin-speech-coach), [PyPinyin](https://github.com/mozillazg/python-pinyin), [RapidOCR](https://github.com/RapidAI/RapidOCR), and [pycccedict](https://github.com/patrickpei/pycccedict).

**CC-CEDICT content is CC BY-SA 4.0**, credited to the CC-CEDICT contributors and MDBG. The dataset is installed separately through pycccedict; it is not copied into this repository. See third-party dependency repositories for their code licences. See [ai.md](ai.md) for AI usage and [TASKS.md](TASKS.md) for the project checklist.

## Privacy

OCR, pitch analysis and Mandarin recognition run locally. Creating a lesson may send the selected Chinese text to Google Translate or MyMemory for a full English translation; common phrases/menu items use an offline phrase cache. Providers can be unavailable, in which case approximate word meanings are explicitly labelled. Browser speech synthesis may use device or platform services. No user accounts or telemetry are part of this prototype.


## Phone camera and natural Mandarin voice

The Gradio app is now phone-responsive and already accepts webcam/camera images, image uploads, and pasted photos. See [iPhone HTTPS setup](docs/PHONE_DEMO.md) to launch a **temporary password-protected https://*.gradio.live** testing link from your Windows laptop. A publicly hosted/permanent website is not yet deployed.

There are now **two reference voice choices**:
- Natural voice (default): online [edge-tts](https://github.com/rany2/edge-tts) with Xiaoxiao (Female) or Yunxi (Male), configurable speed and an audio player. **Generated only when you tap Listen.** Selected text goes to a third-party service, which can fail or be unavailable.
- Browser voice: choose it under Voice & speed for device/platform Mandarin speech. It also serves as the fallback after a neural-service failure. Available Mandarin voices and audible playback depend on the device.

Neural speech synthesis is not the same as speech transcription or automatic grading. Current pronunciation assessment still covers one isolated syllable at a time.

**Mobile access isn't automatically active after installing Hanpi.** You must start the host server and open its HTTPS URL on your phone. For a permanent production site, add a hosted backend and independent user storage; the existing SQLite collection is shared by anyone authenticated to the same temporary demo.


## Final phone-readability pass

The app uses one readable light palette even when the phone requests dark mode. Recording and feedback are separate, compact stages; Back returns to the previous stage. Technical pitch charts, model-download controls and transcript editing are absent from the normal learning flow. Voice options remain inline.

Full English translation appears directly in Results. For example, 蒜香爆燒肉 → “Stir-fried roast pork with garlic.” Common phrases/menu items work offline; other sentences try bounded online providers, then clearly label any word-gloss fallback. This does not imply an offline translation model for arbitrary sentences.

Tone coaching accepts quieter/shorter recordings and a broader pitch range, fixes stereo PCM normalization, and uses encouraging feedback. Sound-alike ASR spellings are advisory, not definite word errors. These changes do not establish human pronunciation accuracy or turn uncertain audio into a successful grade.


## Demo welcome screen

The shared HTTPS link opens a Hanpi-branded sign-in card. Visitors use your configured demo username/password, then continue into Scan; no account registration is needed. The two brand fonts are bundled under their SIL Open Font licences for reliable styling before and after login. See [phone setup](docs/PHONE_DEMO.md) for credentials and sharing.
