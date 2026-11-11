# AI use disclosure · Hanpi

**Voice-first feature:** Image of Hanzi → readings → user speaks into microphone → audio pitch assessment and pronunciation coaching. Voice is integral because reading pinyin cannot demonstrate one's ability to reproduce a tone.

## Runtime

- **RapidOCR:** pretrained ONNX Chinese OCR models, local processing. Tesseract fallback.
- **PyPinyin:** dictionary/rules for reading and basic tone sandhi, not a generative model.
- **CC-CEDICT via pycccedict:** installed offline Chinese-English dictionary (CC BY-SA 4.0; CC-CEDICT contributors/MDBG credited). Longer phrases are segmented into word glosses, not fluent translation.
- **deep-translator:** optional online translation when explicitly clicked; sends selected Chinese text to an external provider. Not part of the offline default flow.
- **Praat/Parselmouth:** signal-processing pitch measurement (F0); we wrote a simple contour heuristic which can abstain. This is not a trained Mandarin tone model and should not be presented as one.
- **SpeechSynthesis:** browser/platform TTS for pronunciation examples.
- **Faster-Whisper:** optional local text transcript; downloads a model only when installed/used. ASR text is NOT the measured spoken tone.

## Development tools

OpenAI ChatGPT (GPT-6) assisted with GitHub research, architecture, initial implementation, tests, and documentation. External repositories were used as references, not as copy-pasted application source. Dependency/model licences are owned by their maintainers.

## Evaluation and safeguards

Initial tests cover only artificially generated pitch contours and text rules; a generated Hanzi image was OCR-smoke-tested with Tesseract. Human recording accuracy, real-photo OCR, and the user's Windows install remain to be tested before submission. Pitch contour ≠ complete pronunciation; low or unclear tone 3 may be unclassified. This is educational feedback, not a validated language-assessment or medical product.

Default OCR, dictionary lookup and audio grading run locally; microphone recordings are not sent to an LLM. Online translation only sends text after an explicit click. Browser speech-synthesis services may depend on the host platform.


## Natural Mandarin voice and mobile access

An optional online neural voice feature uses [edge-tts](https://github.com/rany2/edge-tts), a third-party LGPLv3 Python client for Microsoft Edge's speech service. It offers Mandarin voices Xiaoxiao/Yunxi/Xiaoyi at configurable speeds, and sends the selected Chinese text online **only when the user clicks a neural speech button**. It requires an external network service and may be unavailable or subject to provider restrictions. The existing browser speech-synthesis option remains as fallback. No voice recording is sent to this TTS provider.

Temporary remote access uses a password-protected Gradio HTTPS share link. This is a single-user prototype: all signed-in visitors use the same SQLite Starred library on the hosting computer, not isolated cloud accounts. See docs/PHONE_DEMO.md.
