# Speech accuracy and guided tutor · 12 November 2026

## Problem and approach

Users reported an isolated syllable gaining particles or being repeated in the
transcript. The original 14M streaming Zipformer is useful for a lightweight
prototype, but its endpoint/language guesses can be poor on very short clips.
Merely relaxing text comparison does not fix those guesses.

This change adds speech detection before decoding, offers a stronger offline
recognizer, and pauses app playback when recording begins. Recognized text is
never overwritten with the target or silently deduplicated. Genuine repeated
speech must remain visible (including legitimate words such as 妈妈).

## Sources reviewed

- [Silero VAD](https://github.com/snakers4/silero-vad): pretrained speech-activity
  detection, CPU/ONNX usage, supported rates and published evaluation links.
  Its [MIT licence](https://github.com/snakers4/silero-vad/blob/master/LICENSE)
  accompanies the bundled 2.3 MB model.
- [SenseVoice](https://github.com/FunAudioLLM/SenseVoice): released-model scope,
  Chinese recognition, non-autoregressive inference and VAD integration.
  Its linked [FunAudioLLM paper](https://arxiv.org/abs/2407.04051) is background;
  the implementation decisions here use the accessible project/API docs and
  our measured cases, not a claim of independently reproducing its paper.
- [Official sherpa-onnx SenseVoice example](https://github.com/k2-fsa/sherpa-onnx/blob/master/python-api-examples/offline-sense-voice-ctc-decode-files.py)
  and [VAD example](https://github.com/k2-fsa/sherpa-onnx/blob/master/python-api-examples/vad-remove-non-speech-segments.py):
  local ONNX inference without downloading/executing remote Python model code.
- [Official model release](https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models)
  and [FunASR model terms](https://github.com/modelscope/FunASR/blob/main/MODEL_LICENSE).
  Model weights have separate terms from inference-library code. Source/model
  names are retained and large recognition weights are not redistributed here.

No Figma tools were available. The small Hǔ tiger is original SVG code, retaining
Hanpi's existing palette/fonts; no PathPilot or Duolingo asset was copied.

## Engineering choices

- **SenseVoice Small int8** is recommended: approximately 163 MB download and
  239 MB model file. CPU inference uses the existing sherpa-onnx dependency.
  It is preferred automatically after preparation; existing compact installations
  continue to run. Explicit `accurate`/`compact` profiles remain available.
- **Speech detection runs first.** Silence/DC, obvious steady electronic tones,
  and clips without detected speech are rejected before recognition. A trained
  detector is not perfect and is not a human-identity or pronunciation detector.
- **Short syllables need conservative settings.** The default VAD minimum
  speech duration rejected our short human crop. A 64 ms minimum with a 0.35
  threshold retained that crop and its quiet version. Synthetic hiss/tap trials
  across 30 seeds each produced no accepted speech regions in this run.
- **Preserve initials and endings.** The offline model gets the envelope from
  first to last detected speech, with 320 ms pre-roll and 180 ms post-roll.
  Internal pauses and repeated speech are preserved. These regions are not
  word-level acoustic alignment.
- **Keep compact timing stable.** Trimming initially made the original streaming
  model worse on the focused cases. Its input is speech-gated but retains original
  timing; endpoint trimming is used for offline recognition.
- **Prevent self-echo.** Starting microphone capture cancels browser speech,
  pauses media, and blocks late playback while capture is active. Queued tutor
  examples have cancellation tokens. Check buttons are disabled while recording
  and automatic checking is pending.
- **No target priming.** The recognizer receives audio and a Mandarin language
  setting, never the target text. Existing homophone/short-ending tolerance is
  labelled explicitly and does not rewrite the transcript.

## Focused regression results

The source is the official Zipformer `test_wavs/0.wav`. Its first 0.42 seconds
are used as a short 对 crop, not a new independently recorded isolated-word
corpus. Eight speech cases cover clean/quiet speech, surrounding silence, taps,
breath-like noise, light hiss, and two actual copies of the word. Six non-speech
cases cover silence, hiss, a tap, breath-like noise, a steady tone, and DC offset.

| Pipeline | Matching cases out of 14 |
| --- | ---: |
| Original compact pipeline | 11 |
| Compact with speech gate, original timing | 11 |
| Raw SenseVoice | 9 |
| SenseVoice with speech filtering | 14 |

The old model returned 对吧 for a tap preceding the word and for two real word
copies. Filtered SenseVoice returned 对 and 对对 respectively. Raw SenseVoice
invented words on several noise-only cases; filtering stopped those inputs before
decoding. This is why the model upgrade alone is insufficient.

**These counts are not general ASR accuracy, a native-speaker study, or a claim
that the user's microphone/accent is fixed.** They are small, reproducible
engineering regressions. Exact per-case transcripts, latency and source hash
are in [speech-v2.json](benchmarks/speech-v2.json).
This set was used during development; it is not held-out validation.

After preparing both profiles, reproduce with:

```bash
python scripts/prepare_asr.py --profile compact
python scripts/prepare_asr.py --profile accurate
python scripts/benchmark_speech.py --reference-wav /path/to/official/test_wavs/0.wav --output speech-results.json
```

The compact release archive includes that public WAV. The evaluation does not
download models or audio implicitly. Model installation checks archive and
extracted-file hashes and repairs corrupted cached files.

## Guided voice tutor

Hǔ uses a small dialogue tree based on transcript/pitch evidence. It offers
encouragement, explains a measured rising/falling/steady shape, and invites the
next character or whole phrase. Browser speech reads English guidance and, for
a corrective example, queues the appropriate Mandarin text. Sandhi examples keep
phrase context. Spoken tips can be muted or replayed explicitly.

This is guided interaction through buttons, not a general conversational LLM.
There is no sentence-tone or consonant/phoneme grading. Unclear speech/pitch gets
a retry invitation, not a fabricated success or percentage.

Browser QA used a public human WAV as Chromium's fake microphone input, actual
capture/automatic local ASR, and a separate noise clip. It verified one word once,
mute/replay, English→Mandarin queuing and playback cancellation. Speech-output
calls were stubbed to inspect behavior; audible voices, real acoustics, iOS
autoplay and the user's actual microphone remain hardware checks.
