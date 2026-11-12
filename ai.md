# AI use disclosure · Hanpi

Hanpi uses speech and text tools to help Mandarin learners move from understanding a written phrase to trying it aloud. Voice is central to the practice loop: the learner hears a reference, speaks, and sees what the system recognized. Keyboard input alone cannot capture that spoken attempt.

## Development assistance

OpenAI ChatGPT/Codex (GPT-6 family) assisted with product and UI iteration, Python/Gradio implementation, dependency diagnosis, tests, browser checks and documentation. The workflow combined user feedback from the Windows/phone prototype with automated checks in a Linux development environment. AI assistance does not establish model accuracy; the evidence and limits below describe what was actually checked.

Libraries were integrated through their APIs. No runtime LLM generates pronunciation grades or invents heard words. No AI-generated mascot or Figma artwork is included. Fredoka and Plus Jakarta Sans fonts are bundled from Fontsource 5.3.0 with their original SIL Open Font licences.

## Runtime tools and models

| Tool | Role and limits |
| --- | --- |
| RapidOCR / ONNX | Pretrained Chinese OCR, processed on the host. Preprocessing helps small/coloured images, but the learner must confirm the proposed text. Tesseract is an optional fallback. |
| PyPinyin | Dictionary/rule-based written pinyin and basic tone sandhi; context and polyphonic characters can still need review. |
| CC-CEDICT via pycccedict | Offline dictionary, segmentation, English reverse lookup and pinyin lookup. Definitions are not a general sentence translator. Content credited to CC-CEDICT contributors/MDBG, CC BY-SA 4.0. |
| Offline phrase cache + Google Translate/MyMemory | Cached translations cover a small set of common phrases/menu items. Other lessons may request an online translation; failures retain a labelled approximate dictionary gloss. Legacy optional English translation uses deep-translator. |
| sherpa-onnx / Mandarin Zipformer | Default local Mandarin speech recognition using the compact 14M model from the official sherpa-onnx release. One-time download of about 75 MB, SHA-256 checked; model release is Apache-2.0. The target sentence is never supplied as a recognition prompt. |
| Faster-Whisper | Optional alternative ASR backend with separate installation/model preparation. Not needed for the default submission. |
| OpenCC + difflib | Normalize Simplified/Traditional variants for comparison and align target/transcript characters. Unequal replacements are shown as segments. This is text alignment, not acoustic forced alignment. |
| Praat/Parselmouth | Measures fundamental frequency (F0). A rule-based heuristic describes an isolated syllable as roughly level, rising, dipping or falling, or abstains. This is experimental signal processing, not a validated Mandarin assessment model. |
| edge-tts / browser SpeechSynthesis | Mandarin reference speech. Natural playback sends selected text to the external Edge speech service only on Listen; browser speech is the fallback and depends on installed/platform voices. edge-tts is an LGPLv3 client. |

## What feedback means

**You said** contains actual ASR output. Its pinyin is the dictionary reading of that recognized spelling; it is not measured lexical-tone recognition. Word matches and experimental pitch matches are separate signals. Exact pinyin matches identify homophones such as 算/蒜. Single-syllable practice additionally compares the base syllable without treating ASR spelling as tone measurement. One short trailing le/er or common conversational particle is tolerated and explicitly labelled as ignored for that drill, so 算了/算儿 can count as a suan attempt. The transcript is never shortened or replaced. Matching the experimental acoustic pitch remains a separate requirement for the saved practice count. Arbitrary extra words, longer utterances and different base syllables are not accepted by this rule; sentence comparison retains all its words. Contextual sandhi and selected polyphonic readings are retained. This remains text-derived evidence, not acoustic phoneme detection. **Words match!** allows the learner to continue, but is not a certificate of correct pronunciation.

Sentence differences highlight possible missing or changed text. ASR can mishear, including sound-alike spellings; the learner can inspect the aligned target/heard breakdown and practise a selected syllable. Hanpi does not provide full-sentence tone grades, consonant/phoneme diagnoses, arbitrary percentages or invented successful transcripts. Missing model/setup errors are logged rather than silently converted to success.

## Data flow

OCR, ASR and pitch analysis run on the host computer. In a phone demo, images/audio are uploaded over HTTPS to that host; they are not necessarily processed on the phone itself. Recordings are not sent to an LLM, translation provider or TTS provider. Gradio can cache uploaded media temporarily, and this prototype does not promise production-grade retention controls.

Lesson creation may send selected Chinese text to an online translation provider; natural Listen sends selected text to the TTS service. Browser speech may use device/platform services. Gradio analytics are disabled. Saved vocabulary uses a host-local SQLite database shared by authenticated demo visitors, not independent user accounts. Credentials, local recordings, saved vocabulary and model downloads are excluded from the source archive.

## Evaluation

- **148 automated tests passed** in Python 3.11/Linux, covering dictionary initialization, real packaged dictionary/OCR, offline lookup, translation fallback, audio handling, synthetic pitch contours, transcript comparison, saved data and auth guard behavior.
- Actual local ASR transcribed public human Mandarin WAV files from the official model release. Browser tests exercised an isolated 对 crop, matching and mismatching sentences, heard-versus-target Spotlight, Continue and Back navigation. These were real model calls, not mocked transcripts.
- Phone-width and desktop browser checks covered OCR, reading/pinyin, voice callbacks, practice stages, saved-data persistence, dark-mode contrast and authentication. Real authentication tests rejected incorrect passwords and retained a valid session after refresh; bundled fonts were verified to load.
- Some provider responses and failure paths are mocked in unit tests; live external translation/TTS availability is not guaranteed. Browser speech callback tests verify wiring, not audible quality.
- The user reported successful Windows/phone launch and OCR on the actual menu. The committed tiny-red/clean OCR fixtures are generated examples, not the user's original photos. There is no independent native-speaker study, representative ASR error rate, validated tone accuracy, or new physical-phone microphone/playback measurement.

See [docs/REDESIGN_QA.md](docs/REDESIGN_QA.md) for detailed test history and [README.md](README.md) for setup and current limitations.
