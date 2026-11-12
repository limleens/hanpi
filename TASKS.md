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
- [x] Mobile-first Gradio web experience (hardware/iPhone field checks remain below).
- [ ] Optional per-user cloud sync for starred cards.

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


## Hanpi v1 mobile-first redesign · 11 November 2026

- [x] Cream/coral responsive shell, compact Hanpi wordmark/tagline, top search, Scan / Type / Speak / Saved bottom navigation.
- [x] One shared Results surface for camera/upload OCR, typed/search text, optional ASR and reopened saved items.
- [x] Editable OCR/text, aligned tone-coloured character/pinyin controls, honest dictionary provenance and key vocabulary.
- [x] Spotlight selection with dimmed neighbours, sandhi-aware Listen, Try it, retry, Next and Back to phrase.
- [x] Settings for Female/Male, 0.75×/1×/1.25× playback, browser fallback and optional Whisper; reduced-motion support.
- [x] Experimental isolated-syllable feedback; pitch charts collapsed; no phoneme detection or whole-sentence tone score.
- [x] Whole-phrase record/review/completion, SQLite word/character/phrase saving, reopening and removal.
- [x] Baseline 32 tests before refactor; final 47 tests pass, including state, provider failure and practice-count regressions.
- [x] CI-equivalent UI import/HTTP startup check and phone/desktop browser walkthrough; server-restart persistence checked with an isolated database.
- [ ] Confirm live neural TTS and audible Mandarin browser playback on the user's device.
- [ ] Test actual iPhone rear camera/mic over authenticated HTTPS and a real photo/voice recording.
- [ ] Complete native-speaker feedback, submission write-up and a short demo before the authoritative portal deadline.

See `docs/REDESIGN_QA.md` for exact automated results and browser evidence. The app remains a single-user, shared SQLite prototype; no permanent hosting or per-user cloud sync is claimed.


## Release reliability pass · 11 November 2026

- [x] Reproduced English-only search failure and the real upstream dictionary UnicodeDecodeError with CP1252 decoding; no silent initialization failure.
- [x] Explicit Chinese → English / English → Chinese / Pinyin modes; offline reverse lookup, tone groups, numbered/accented input, pagination and selectable lessons.
- [x] Real bundled CC-CEDICT loads as UTF-8; diagnostic command verifies app interpreter/packages and 我 / 喜欢 / 咖啡 segmentation. Limited fallback vocabulary is clearly labelled.
- [x] Bounded OCR upscale/contrast/sharpen/red-channel variants with model-score ranking; preserve Traditional output and require editable confirmation before lesson creation.
- [ ] Run OCR on the original user menu image: inline chat images are visible but no source file is exposed to Python. Generated 149×28 red Traditional and clean fixtures pass actual RapidOCR.
- [x] Default local Mandarin ASR with an explicit, checksum-verified ~75 MB model download; no paid API or Hugging Face dependency for the default path.
- [x] Whole-sentence expected/transcript comparison, possible word omissions/substitutions, editable transcript and highlighted-target Spotlight. No sentence tone/phoneme grading.
- [x] Real public Mandarin recordings transcribed; browser integration checks matching and mismatching targets. Isolated-syllable F0 coach remains independent.
- [x] Fresh Python 3.11 dependency install and non-UTF-8-locale dictionary check; full regression suite and both browser walkthroughs pass.
- [x] Local authentication smoke test: unauthenticated config is HTTP 401, valid login succeeds. No secrets committed.
- [ ] Actual Windows/iPhone hardware: authenticated HTTPS, rear camera, microphone, audible Mandarin speech. Follow the five-minute PHONE_DEMO check.
- [ ] User review of PR #2; do not merge automatically.

See docs/REDESIGN_QA.md for exact evidence and limitations. Bubbly styling and the existing navigation are preserved; this pass changes functionality, not visual design.


## Final phone feedback pass · 11 November

- [x] Reproduced the dark-OS/light-card mismatch; mirrored Gradio dark tokens and checked white audio cards/dark text in a dark-OS browser.
- [x] Full sentence/menu translation shown directly, offline phrase cache plus bounded online providers with honest fallback labels.
- [x] Inline voice options; removed visible Settings/model preparation/transcript-edit/pitch-debug controls.
- [x] Separate Results / Spotlight / Record / sentence feedback stages, one-stage Back and automatic scroll-to-stage.
- [x] More tolerant voiced-audio extraction, quieter/stereo recording regressions, gentle coaching, and cautious treatment of homophone ASR spellings without fake passes.
- [x] 92 tests pass; dark-OS 390px browser checks menu translation, staged recording, real Mandarin ASR, Back navigation and removal of technical controls.
- [ ] Recheck the updated build on the actual phone; the user confirmed phone launch and real-image OCR on the preceding build.


## Final voice feedback pass · 11 November

- [x] Enable actual local ASR for isolated-character practice; show the exact heard text, pinyin and target instead of pitch tips alone.
- [x] Separate word matching from measured experimental tone shape; show both observed and target tone labels. Keep Continue available, without unsupported perfect-pronunciation claims.
- [x] Check microphone recordings on stop; retain explicit check buttons for uploads/retries.
- [x] Whole-phrase word match confirmation, highlighted differences, and selectable target/heard Spotlight breakdown for every target character.
- [x] Back preserves sentence transcript feedback through word Spotlight and recording stages.
- [x] Shorter learner copy; no new logo/mascot project or dependency download before submission.
- [x] Real human single-word and sentence ASR exercised in a dark-OS phone-width browser; exact-match Continue, replacement breakdown and nested Back verified.
- [ ] Recheck the final voice feedback with the user's physical phone microphone; arbitrary-word ASR accuracy and full-sentence tone grading remain unvalidated/unsupported.
- [x] Final validation: 104 pytest cases; same-interpreter strict dictionary/ASR check; current server startup; real-recording phone browser and OCR/Saved/desktop walkthroughs.


## Demo welcome screen · 11 November

- [x] Match the protected sign-in page to Hanpi's cream/orange/navy cards and Fredoka/Plus Jakarta Sans typography.
- [x] Bundle the brand fonts with their SIL Open Font licences; no external font request needed before login.
- [x] Preserve configured username/password authentication and never expose credentials in landing HTML.
- [x] Real authenticated browser checks at 320/390/1280px, light/dark appearance, wrong-password rejection, protected config, successful login and refresh persistence.
- [x] Full Python suite: 105 tests passed; existing remote-auth guard remains tested.
- [ ] Confirm final sign-in appearance on the physical phone; browser checks use desktop Chromium with phone-sized viewports.

## Submission handoff · 11 November

- [x] Rewrite README around a reviewer-friendly quick start, the actual submission branch, a short voice-led walkthrough, architecture, limits and privacy.
- [x] Consolidate ai.md into an accurate account of development assistance, runtime models, real versus mocked validation and current limits.
- [x] Provide a submission checklist and prepare a tracked-source ZIP without credentials, local saved data, recordings, model downloads or virtual environments.
- [ ] Owner uploads the one-page write-up, demo/video and private reviewer access details to the challenge portal; PR #2 stays unmerged.


## Homophone feedback correction · 12 November

- [x] Reproduce the screenshot: 蒜 and ASR 算 both read suàn, but strict character equality prevented a successful attempt.
- [x] Accept identical full pinyin including tone, retaining the actual transcript and separate acoustic pitch requirement for practice counts.
- [x] Keep different tones, additional syllables and different sounds distinct; preserve contextual sandhi and selected dictionary readings.
- [x] Shorten successful feedback and avoid corrective pitch instructions when the observed contour already matches.
- [x] Sentence feedback explains same pronunciation/different characters without claiming text equality or measured sentence tones.
- [x] 122 tests pass; phone browser reproduces the screenshot using a declared ASR stub and actual Praat processing of synthetic falling pitch.
- [ ] Recheck on the user's real voice/phone; the screenshot did not include an audio file.
