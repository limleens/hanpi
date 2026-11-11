# Hanpi · Release checklist

## Implemented
- [x] Dedicated Hanpi repository (moved from the experimental WELP branch).
- [x] Image input: paste, drag and drop, upload, webcam.
- [x] RapidOCR (with optional Tesseract fallback) for Chinese images.
- [x] Remove 24-Hanzi truncation: retain all detected Hanzi and all text typed by the user.
- [x] Produce pinyin and basic spoken tone sandhi via PyPinyin.
- [x] Render colour-coded tone cards in a scrollable area.
- [x] Use CC-CEDICT offline definitions for words, with clearly labelled dictionary glosses for longer text.
- [x] Provide opt-in online translation for full-sentence meaning (limit per external API: 2,500 Hanzi).
- [x] Browser Mandarin speech playback for a selected syllable or the full phrase.
- [x] Record microphone audio and analyse isolated-syllable pitch using Parselmouth/Praat.
- [x] Show experimental tone-pattern feedback and chart.
- [x] Local SQLite Starred collection with save, delete, replay and practice counts.
- [x] Add unit tests and GitHub Actions CI.
- [x] Document external library licences and AI assistance in README/ai.md.

## Verify on the user's Windows laptop before submission
- [ ] Clone repo and pip install requirements into Python 3.11 venv.
- [ ] Open localhost:7860, paste and drag in a real Chinese photo.
- [ ] Test a **longer screenshot of at least 50 Hanzi** and confirm nothing disappears.
- [ ] Check CC-CEDICT word definition for 咖啡 and proper handling of unknown entries.
- [ ] Check online translation only triggers when clicked.
- [ ] Listen to Chinese TTS in Edge/Chrome, confirm a Mandarin voice is installed.
- [ ] Record 4 examples: 妈 / 麻 / 马 / 骂 and inspect pitch labels.
- [ ] Star 中国, restart, practise again, verify SQLite persistence.
- [ ] Record a short demo that includes a non-你好 example.
- [ ] Complete Hiya's one-page write-up and ai.md check.

## Future enhancements (not claimed as working)
- [ ] Robust full-sentence ASR with forced syllable alignment.
- [ ] Detect phoneme/consonant differences, not only tone contours.
- [ ] Word-by-word speech playback highlighting.
- [ ] More natural reference TTS with timed pronunciation tracking.
- [ ] Tongue and mouth-shape visual diagrams for zh/ch/sh and retroflex sounds.
- [ ] Dedicated iPhone experience and optional cloud sync for starred cards.

**Scope:** Hanpi can read longer Chinese text, but scoring is deliberately one syllable at a time. Do not claim verified full-sentence pronunciation grading or clinical accuracy.


## Mobile and natural reference speech update
- [x] Responsive Gradio adjustments for narrow mobile screens.
- [x] Mobile photo input with camera, upload and clipboard sources.
- [x] Optional online Mandarin neural voices (Xiaoxiao/Yunxi/Xiaoyi) with adjustable rate, plus browser TTS fallback.
- [x] Password-protected temporary HTTPS share mode to test iPhone Safari.
- [x] Added mock neural-voice and remote-auth automated tests.
- [ ] Confirm the neural TTS service connects and returns human-sounding audio using a real Internet connection.
- [ ] Test iPhone camera capture and microphone permissions over HTTPS.
- [ ] Launch a permanent phone-accessible website using per-user saved vocabulary storage.
