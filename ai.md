# AI use disclosure · Hanpi

**Voice-first feature:** Image of Hanzi → readings → user speaks into microphone → audio pitch assessment and pronunciation coaching. Voice is integral because reading pinyin cannot demonstrate one's ability to reproduce a tone.

## Runtime

- **RapidOCR:** pretrained ONNX Chinese OCR models, local processing. Tesseract fallback.
- **PyPinyin:** dictionary/rules for reading and basic tone sandhi, not a generative model.
- **CC-CEDICT via pycccedict:** installed offline Chinese-English dictionary (CC BY-SA 4.0; CC-CEDICT contributors/MDBG credited). Longer phrases are segmented into word glosses, not fluent translation.
- **Sentence translation:** lesson creation can request Google Translate/MyMemory for full English; common phrase/menu translations are cached offline. Legacy English online search uses deep-translator. Only selected text is sent; recordings stay local.
- **Praat/Parselmouth:** signal-processing pitch measurement (F0); we wrote a simple contour heuristic which can abstain. This is not a trained Mandarin tone model and should not be presented as one.
- **SpeechSynthesis:** browser/platform TTS for pronunciation examples.
- **sherpa-onnx / Mandarin Zipformer:** default local Mandarin sentence transcription using a compact Apache-2.0 model from the official sherpa-onnx GitHub release. An explicit one-time download (~75 MB) is SHA-256 checked; recordings stay local.
- **Faster-Whisper:** optional alternative transcription backend with an explicit model preparation step. Neither backend measures lexical tone accuracy.
- **OpenCC + difflib:** Simplified/Traditional normalization for text comparison and character edit alignment; this is not acoustic forced alignment or phoneme detection.

## Development tools

OpenAI ChatGPT (GPT-6) assisted with GitHub research, architecture, initial implementation, tests, and documentation. External repositories were used as references, not as copy-pasted application source. Dependency/model licences are owned by their maintainers.

## Evaluation and safeguards

Initial tests cover only artificially generated pitch contours and text rules; a generated Hanzi image was OCR-smoke-tested with Tesseract. Human recording accuracy, real-photo OCR, and the user's Windows install remain to be tested before submission. Pitch contour ≠ complete pronunciation; low or unclear tone 3 may be unclassified. This is educational feedback, not a validated language-assessment or medical product.

Default OCR, dictionary lookup and audio grading run locally; microphone recordings are not sent to an LLM. Online translation only sends text after an explicit click. Browser speech-synthesis services may depend on the host platform.


## Natural Mandarin voice and mobile access

An optional online neural voice feature uses [edge-tts](https://github.com/rany2/edge-tts), a third-party LGPLv3 Python client for Microsoft Edge's speech service. It offers Mandarin voices Xiaoxiao/Yunxi/Xiaoyi at configurable speeds, and sends the selected Chinese text online **only when the user taps Listen with natural voice selected**. It requires an external network service and may be unavailable or subject to provider restrictions. The existing browser speech-synthesis option remains as fallback. No voice recording is sent to this TTS provider.

Temporary remote access uses a password-protected Gradio HTTPS share link. This is a single-user prototype: all signed-in visitors use the same SQLite Starred library on the hosting computer, not isolated cloud accounts. See docs/PHONE_DEMO.md.


## v1 mobile redesign

The interface now uses a shared Results view for OCR, typed/search text, optional speech input and saved items. Native Gradio character/pinyin controls open Spotlight practice. Natural speech is the default only after an explicit Listen action; browser fallback remains available in Settings. English common-word lookup and pinyin candidates now use offline CC-CEDICT indexes; online translation remains explicitly opt-in. No phoneme detector or whole-sentence tone scorer was introduced.

Regression checks cover source/meaning state, sandhi speech context, voice-service failures, optional ASR absence and saved practice counters. Browser QA uses generated Chinese text images and synthetic pitch audio. A browser speech callback check verifies wiring, not audible speech quality. Real recordings, native-speaker judgement, iPhone HTTPS camera/mic behavior and production hosting remain unverified. See docs/REDESIGN_QA.md.


## Release reliability fixes

The dictionary loader now explicitly decodes UTF-8 instead of hiding an upstream locale-dependent UnicodeDecodeError. Tests use the installed 122,143-entry dataset, including a real CP1252 failure reproduction and a fresh Linux install with UTF-8 mode disabled. This simulates the decoding issue, not a Windows hardware test.

Sentence practice transcribes real audio locally and compares the resulting text with the target. Highlighted words are **possible text differences**: the learner can correct ASR mistakes and open a flagged target character in Spotlight. A matching transcript does not prove correct pronunciation. No numeric pronunciation grade, per-syllable tone diagnosis or consonant-error detector was added.

Actual model validation used three public human Mandarin WAV files from the official model release, plus browser upload/transcription/comparison with matching and mismatching target sentences. This is functional integration evidence, not a measured ASR accuracy study or a test of the user's microphone. The small-red and clean OCR PNGs committed under tests/fixtures are generated fixtures; they are explicitly not the user's inline menu images. Exact-image benchmarking remains pending access to the original file. Phone camera/microphone and audible device TTS remain manual checks.


## Final phone feedback pass

Whole-phrase English is now the primary Results content: a small explicit offline phrase/menu map covers common examples, and Google Translate/MyMemory are attempted for other sentences with bounded timeouts. If unavailable, approximate dictionary glosses are labelled rather than represented as fluent translation. The user explicitly requested direct sentence translation; lesson creation may send Chinese text online. Recordings remain local.

Phone dark-mode contrast and staged Back navigation were checked in a browser configured with a dark OS preference. Technical setup/transcript-edit panels were removed from the learner flow. The tone coach now accepts a broader voiced range and quieter/shorter input; homophone ASR spellings are advisory. No inaccurate pronunciation percentage or whole-sentence tone score was added. The user's real recordings were not available for a measured false-rejection-rate study.


## Final voice feedback

Character practice now runs the existing local Mandarin ASR as well as the isolated F0 coach. **You said** and its pinyin come from the actual recognized spelling; the model never receives the target as a recognition prompt. Word matches and pitch-shape matches are separate evidence. A word match permits Continue and is not a pronunciation certificate. Missing recognition/model setup is logged and never becomes an invented transcript or success.

Whole-sentence comparison retains aligned target/recognized segments for Spotlight, including missing words, sound-alike spellings and unequal-length replacements. Transcript pinyin gives the dictionary reading of the spelling, not an acoustically measured lexical tone. There is still no sentence tone, phoneme or consonant detector.

Validation used actual public human recordings from the official model release: a short 对 crop and a full sentence, through the browser upload controls. Matched and mismatched targets, per-word heard breakdown and nested Back navigation passed. This is functional evidence for those recordings, not an accuracy study or a real phone microphone test. UI text was shortened; no Figma or new mascot artwork was used in this final pass.
