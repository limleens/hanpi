# Hanpi — release-blocking bug bash (11 Nov 2026)

**Status:** Reported by the user after testing the playful mobile-first redesign. **Priority: functional MVP first, phone second, visual polish frozen.** The submission target is 23:59 GMT tonight. Keep the current UI structure and design.

Read `AGENTS.md`, `docs/V1_PRODUCT_SPEC.md`, `docs/VISUAL_DESIGN.md`, `README.md`, and this file before modifying code. This document is a user-reported failure list and an acceptance contract, **not** a claim that the issues have already been resolved.

## P0. Real-world functionality, not simulated QA

### 1) Search / translation / pinyin

**Reproduction:** In top search field, type English `eat`; click Search, then Translate English online. Current UI says **"Online translation is unavailable. Try Chinese text or Scan instead."** This means the visible search product path is broken for this user.

**Required UX:**
- Make direction explicit and easy to switch: **Chinese → English** | **English → Chinese** | **Pinyin lookup** (segmented control or equivalent, auto-detection is supplementary).
- For English `eat`, return one or more actual usable Chinese equivalents, e.g. **吃 (chī, to eat)**. Show pinyin, meaning and a tap-to-learn path.
- For `ma` or `ma1`, offer genuine **tone-grouped candidate meanings**, e.g. mā 妈 mother, má 麻 hemp, mǎ 马 horse, mà 骂 scold, ma 吗 question particle. Support diacritic/number/unmarked pinyin queries. Don't arbitrarily assign one reading to ambiguous input.
- For `我喜欢咖啡`, return pinyin and English. If the online translator works, show fluent English; if it fails, show labelled offline dictionary/gloss fallback rather than a blank/error-only panel.
- **Resilience:** Do not make common word lookup dependent on the external Google Translator endpoint. Prefer offline CC-CEDICT and a compact fallback/reverse index; external translation is enhancement, with clear network error and source label. Don't pretend a word-by-word gloss is a fluent sentence translation.
- Every result must be selectable to enter the already-working Results/Spotlight view. No fake or decorative option buttons.

**Likely code locations:** `app.py` top search callbacks, `hanpi_core/gloss.py` `translate_to_chinese`, `translate_online`, `lookup_meaning`; a new pinyin lookup helper is fine.

**Acceptance checks:** `eat`, `ma`, `ma3`, `妈`, `我喜欢咖啡`; online provider network failure with graceful offline fallback; no truncated silently ambiguous candidate lists (limit with a "more" state if needed).

### 2) Dictionary installation and useful vocabulary

**Reproduction:** In Results, sentence meaning shows **"unavailable · Install the requirements to enable the offline CC-CEDICT dictionary"**. "A few words to know" shows only 我 for `我喜欢咖啡`, leaving other common phrase words unrecognized.

**Root cause to investigate, do not guess:** `hanpi_core/gloss.py` has `_cedict()` which catches import/init errors and silently returns `None`. The curated `GLOSSES` map is small. Possible causes: dependency installed into a different Python interpreter, API initialization failure, missing dataset, or another exception. Reproduce with the same executable that starts app.py and log the underlying failure safely.

**Required:**
- Make `pycccedict` install and initialisation work in the documented Windows Python 3.11 venv. Verify on a **fresh install** and during app startup; provide an actionable installation diagnostic, not a misleading success state.
- Add fallback common vocabulary for `我喜欢咖啡` (including **喜欢**, **咖啡**) if needed, but don't rely on a handful of hardcoded demo entries as the entire product.
- Phrase segmentation must return meaningful words rather than only one-character matches. Keep Chinese character and pinyin display intact.
- Tests must use the real installed dictionary without always mocking its import/init. Do not silently ignore errors in test assertions.

**Acceptance:** `我喜欢咖啡` returns **我 / 喜欢 / 咖啡** with meanings and pinyin. `免治牛肉石頭飯` or another real menu phrase can show dictionary meanings for recognized subsets with clearly stated approximation. Running without optional online translation still works.

### 3) OCR of small printed Chinese, including traditional characters

**Reproduction:** A very narrow, low-resolution crop of dark-red Chinese menu text on a pale background (user attached it in the chat; upload the sample image in the Codex task as well). Current OCR missed or incorrectly recognized the phrase.

**Required:**
- Benchmark on the *actual user image*, not only big synthetic black-on-white fixtures.
- Inspect EXIF orientation, upscale 2–4x if the crop is small, contrast/sharpen, grayscale and/or appropriate colour channel isolation (red text), try preprocessing variants only when useful; rank candidates using OCR confidence and Chinese text quality when exposed by the API.
- Preserve potential Traditional Chinese reading; don't silently rewrite recognized characters into an incorrect canonical sequence. Make OCR result **editable** before building a lesson.
- Show "We found possible text — please verify" for uncertain OCR. If truly unreadable, give helpful "crop closer/use better light/retake" message rather than confidently hallucinating text.
- Avoid huge new heavyweight OCR models unless essential; keep CPU usable and Windows installation simple.

**Acceptance:** the user-supplied red-text sample produces a plausible, editable string, or a clear reason why the source is unreadable, plus regression tests for small red Chinese and ordinary clean text.

## P1. Whole-sentence speaking practice with honest feedback

**Reproduction:** "Try the whole phrase" currently records/plays audio but can't mark words to retry.

**Desired journey:**
1. User taps **Listen to full phrase** (working speech/audio).
2. User taps **Try the whole phrase** and records a whole sentence.
3. Speech-to-text transcribes Mandarin audio; show **"I heard: ..."** alongside original so users can inspect and correct transcription errors.
4. Align target text to recognized transcript at **character/word level** (e.g. Python `difflib` / segmentation), show correct tokens normally, highlight mismatches/omissions, and allow tapping a flagged character to open existing Spotlight, hear it, and redo an isolated tone.
5. If transcription is unavailable, don't show a fake grade: give a clear installation/network limitation and retain playback + manual Spotlight.

**Important truthful scope:** The existing Parselmouth F0 classifier only measures one isolated syllable's pitch contour. An ASR transcript comparison can indicate *possible word mismatches*, **not** automatically identify incorrect lexical tones or distinguish `zh/sh`. Never invent word-by-word tone grading, phoneme diagnoses or numeric confidence. If actual syllable-timed Mandarin tone evaluation can be implemented and validated within budget, label it **experimental** and back it with testable timings; otherwise do not claim tone mismatch detection in whole-sentence mode. User wants tone-specific feedback but accuracy and trust take priority over decorative red/green highlights.

**Installation:** `requirements-asr.txt` currently makes Faster-Whisper optional. Decide whether to make reliable sentence ASR part of default installation for reviewers or provide a one-click supported path with explicit model download/size and CPU latency. Test with real spoken Mandarin, including a correct and mismatched sentence; not only mocked transcript responses.

## P2. Real phone, only AFTER functionality passes

- Follow `docs/PHONE_DEMO.md` to launch a password-protected HTTPS Gradio link; never publish without auth or expose secrets.
- Test iPhone Safari camera permission, rear camera photo OCR, microphone permission and actual recording, speech playback, bottom nav and no horizontal overflow.
- Confirm settings and saved vocabulary work; remember SQLite is host-local/shared, not per-user sync.
- If a real phone is unavailable in Codex environment, report the limitation and give exact 5-minute user verification instructions; never mark the item green based only on desktop browser emulation.

## Test and release checklist

- [ ] Reproduce each reported failure **before** coding; save brief logs and fixture expectations. Do not suppress stack traces until the root cause is known.
- [ ] Fix dictionary initialization and functional Chinese/English lookup first.
- [ ] Pinyin `ma` mode returns tone variants and meanings.
- [ ] Fix small red Chinese text OCR and preserve editable results.
- [ ] Whole sentence can really transcribe and show comparison; highlight **only evidence-backed** possible word differences.
- [ ] Single-syllable tone coach still works independently.
- [ ] Tests cover actual dependencies and both online-available/offline modes.
- [ ] Run complete `pytest` and Gradio startup; automated browser testing at 390px and 1280px.
- [ ] Test the core flow on Windows and manually on iPhone when possible.
- [ ] Update documentation `README.md`, `TASKS.md`, `ai.md`, `docs/REDESIGN_QA.md` with truthfully verified feature status.
- [ ] Push commits to **`feat/mobile-first-redesign`**, which already has **PR #2**; don't create another PR unless necessary and **do not merge without user review**.
- [ ] Summarize what was fixed, what remains broken, what needs user's mic/phone testing, and the exact `git pull` / run commands.

## Scope discipline

No more visual redesign, mascot work, unrelated feature expansion, Next.js migration, user accounts, cloud sync or Docker work tonight. Use the existing playful styling and consistent shared Results view. A smaller app that handles genuine inputs reliably is a better engineering submission than a wider app containing dead or misleading controls.
