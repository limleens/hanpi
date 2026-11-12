`silero_vad_v5.onnx` is the small Silero voice-activity detector, bundled so
existing installations gain speech filtering without another model download.

- Source: https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad_v5.onnx
- Upstream: https://github.com/snakers4/silero-vad
- SHA-256: `6b99cbfd39246b6706f98ec13c7c50c6b299181f2474fa05cbc8046acc274396`
- Licence: MIT; full original notice in `silero-LICENSE.txt`.

It estimates speech activity, not speaker identity or pronunciation quality.
Large speech-recognition weights are downloaded separately by `prepare_asr.py`.
