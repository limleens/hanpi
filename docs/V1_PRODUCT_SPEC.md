# Hanpi v1 — submission-night product specification

## Purpose and non-negotiables
Hiya Voice AI Challenge · Real-Time Assistance. A mobile-first Mandarin learning flow: snap Chinese text, understand it, listen, speak an isolated syllable, receive evidence-based pitch coaching, and save the phrase. Tagline: **snap, translate, learn!**

Deadline: submit by **11 Nov 2026, 23:59 GMT** as reported by the applicant. The pasted assignment also mentions 2 Nov; confirm the active portal deadline. Do not spend all available time on new features: allow at least 60–90 minutes for submission checks, one-page write-up, and demo.

Technology constraint: **retain the existing Python + Gradio application**, OCR, pypinyin, CC-CEDICT, online optional translator, Parselmouth F0, neural TTS, and SQLite. Do not rewrite in React/Next.js tonight. Introduce CSS/UI modules if useful, but keep app.py runnable and preserve current tests.

## Design system
- Look: warm, confident, delightful, professionally minimal. Cream background, warm coral accent, dark brown typography, subtle outlines, restrained elevation. Avoid scattered sliders, permanently visible debug charts, stacked step-number boxes, and excessive emojis.
- Brand: **Hanpi** / 汉拼. The name refers to 汉 (Chinese) and 拼 (pīn, as in 拼音/pinyin), but 'Hanpi' is a short brand name rather than the full pinyin spelling. Tagline: **snap, translate, learn!**
- Mobile-first at 390px wide; desktop centered max width ~920–1000px. Minimum 44px touch targets, responsive card widths, keyboard-accessible selections, focus states, readable text contrast.
- Use the already generated splash/brand artwork as visual inspiration; only integrate an actual asset if it exists locally or the user saves it into the repository. Do not invent file paths. A simple CSS/icon-based logo is an acceptable temporary implementation.
- Each result uses a consistent tone palette: T1 blue, T2 green, T3 purple, T4 coral/red, neutral gray. Muted nonactive items during practice, but remain readable.
- Animation: gentle 150–250ms transitions, no blocking splash animation. Reduced-motion preference must be respected. Confetti is optional, only after an honest, high-confidence tone-contour match (not a claim of perfect pronunciation).

## Navigation and screens

### 0. Branded arrival
Small Hanpi logo/wordmark and tagline near top; compact welcome state, not a second screen to dismiss. Primary action: **Scan Chinese**. Secondary: **Type a phrase**. A search bar lives near the top.

### 1. Home / search
Top search field: Chinese or English. Chinese input may use offline dictionary / pinyin. English input can use opt-in online translation; label clearly when external service is used. Pressing search opens the same results surface, not a separate unrelated interface.
Bottom mobile navigation: **Scan**, **Type**, **Speak**, **Saved**. Desktop navigation can be top tabs but follow same routing and state. Speak as input may require optional ASR; show a clear installation/unavailable state if missing. The application must not block the core Scan/Type experience.

### 2. Capture / input
Scan: rear camera (when browser supports it), upload, paste, drag/drop. Explain HTTPS required on mobile for camera. One primary button **Recognize characters**; show spinner while processing; allow editing OCR errors. On successful OCR, automatically open Results.
Type: multi-line editable Chinese input plus **Learn this phrase**; skip OCR and open Results. No fixed 24-character cutoff. Long passages may be slower; avoid silently truncating.
Speak: record phrase, attempt optional transcription if installed and give **Use this text** to open Results; otherwise show a clear status and direct to Type/Scan. Do not mislabel untested ASR as reliable word-level grading.

### 3. Results — shared learning surface
Header: editable original Hanzi text, written/spoken pinyin chips aligned with characters, fluent translation if available (otherwise clearly labelled dictionary gloss), key-word meanings, Speak whole phrase button, star action.
One tap on an individual character or aligned pinyin selects it and enters Focus mode. If Gradio HTML cannot faithfully implement tap events, use accessible selectable character chips with real callbacks; do not render dead clickable-looking elements.
Active text display should be the visual hero. Hide raw debug outputs by default in a collapsed 'How Hanpi works' / 'Pitch detail' area.

### 4. Focus / practice
Spotlight: selected character/pinyin full colour; all other tokens visually dimmed but visible. Card shows target Hanzi, pinyin, written vs spoken pronunciation when tone sandhi applies, **Listen**, **Try it**, **Next**, and **Back to phrase**.
Listen: default to natural Mandarin voice; allow browser-voice fallback if online neural synthesis fails. Use concise playback controls, not multiple separate neural voice buttons exposed alongside an ordinary voice button.
Settings are collapsible or a gear: gender Female/Male; speed 0.75×, 1×, 1.25×. Preserve settings across the current session. TTS must run only after user action.
Try it: browser mic recording, then acoustic F0 analysis, compare target tone to actual contour. Never claim consonant/vowel detection from F0. Show **Your tone shape looks close** if contour matches, **Let's work on the tone** when clearly different, or **Not enough audio to judge** when uncertain.
Pronunciation helper: tone contour tip and written/spoken sandhi rule (e.g., nǐ hǎo → ní hǎo). Optional visually accurate articulation illustration for zh/ch/sh/r only when relevant; present it as a teaching reference, not as detected pronunciation error.
On confirmed matching contour, use a subtle celebration if implemented; then offer **Next character** / **Back to phrase**.

### 5. Whole phrase review
**Listen to full phrase**, **Record my attempt**. Optional Whisper transcription comparison can show text differences, but without forced alignment it must NOT assert which syllables have incorrect tones. Allow manual selection of any token to practice again. A completion card says **Nice practice session!** with **Save phrase**, **Practice again**, **Done**.

### 6. Saved / Starred
Cards show Hanzi, pinyin, English meaning, practice count. Actions: **Practice again**, **Remove star**. Retain the existing offline SQLite database, local-device warning, no cross-user sync claim. A temporary shared Gradio URL uses the same account/database; keep auth required for remote demos.

## Product microcopy
- Hero tagline: 'snap, translate, learn!'
- Supporting line: 'See Chinese. Hear it. Say it with confidence.'
- Search placeholder: 'Search a Chinese word or enter English…'
- Camera card: 'Point your camera at Chinese text, or drop an image here.'
- OCR result toast: 'Found Chinese characters. Check the text before you practise.'
- Type CTA: 'Learn this phrase'
- Voice CTA: 'Use what I said'
- Main results header: 'Let's learn this phrase'
- Selected card: 'Listen, then give it a try.'
- Play action: 'Listen'
- Record action: 'Try it'
- Close-match feedback: 'Nice tone contour! Try it once more to build confidence.'
- Mismatch feedback: 'Let's shape that tone. Listen and try again.'
- Uncertain feedback: 'Couldn't judge that recording. Try a quieter, clearer attempt.'
- Sandhi hint: 'Tone tip: 你好 is written nǐ hǎo, but usually spoken ní hǎo.'
- Whole phrase: 'Try the whole phrase'
- Finish: 'Nice practice session! Want to save this phrase?'
- Empty saved: 'Your saved phrases will appear here.'

## Honest limitations
- Existing F0 contour classifier is heuristic; it does not independently identify consonants, vowels, zh vs sh, or correct whole sentences. Don't present specific phoneme errors without a trained model and validation.
- Full sentence ASR + forced alignment is a later milestone. A transcription mismatch is not the same as a detected tone error.
- Online TTS and translation may be unavailable; show a graceful fallback, never silently swallow errors.
- Camera/microphone from iPhone requires an HTTPS origin; local 127.0.0.1 on Windows is not a public phone link.

## Acceptance criteria for v1
1. Launch from a fresh checkout with documented Python install; Gradio UI starts and HTTP responds 200.
2. On desktop at 1280px and phone-like width 390px, navigate Scan/Type/Speak/Saved without clipping or dead elements.
3. Upload or paste a Chinese image, OCR output is editable, continue to the same Result screen as typed text.
4. Enter 我喜欢咖啡 and see pinyin chips, a meaning or clearly qualified dictionary gloss, and a working whole-phrase speaker.
5. Select one character; nonactive chips dim; Listen / Try it / Back work without losing phrase.
6. Run an isolated-syllable microphone recording and show honest pitch contour feedback or a meaningful uncertainty/error message.
7. Star a phrase; restart application; verify it persists and can be reopened.
8. Network failure in natural TTS does not crash UI; browser speech fallback available.
9. Mobile HTTPS camera use is tested where possible; if not tested, describe it as unverified.
10. All Python tests and startup smoke tests pass. Save screenshots or a 2–3 min walkthrough video.

## Two-hour build sequence (from starting Codex in VS Code)
- 0–15 min: Create git feature branch, read code/tests, run baseline, identify callbacks to preserve. Sketch state transitions.
- 15–45 min: Refactor navigation to one flow; mobile responsive shell, search/home, Scan/Type entry, shared Results. No backend rewrite.
- 45–85 min: Implement selectable aligned pinyin chips, spotlight Focus state, Listen / Try / Back flow; move voice gender and speed into Settings.
- 85–105 min: Wire Saved tab and whole-phrase Listen/Record/Finish to existing functions, label experimental areas, add friendly empty/loading/error states.
- 105–120 min: Run tests, smoke-launch, manually click through OCR and focus; fix regressions. Do not merge until stable.

## Codex implementation rules
- Read this spec, current README, app.py and tests before editing; preserve existing working backend modules and safety checks.
- Work on a new feature branch rather than committing a risky UI rewrite directly to main.
- Prefer scoped components/utility functions over a giant app.py if manageable, but prioritize shipping.
- Do not invent an AI phoneme grader, sentence-alignment model or online deployment.
- Don't remove user data, overwrite the SQLite library, commit credentials, or disable HTTPS authentication.
- Add small tests where feasible; run pytest and launch smoke test; report actual pass/fail counts and clearly state what requires real iPhone/mic testing.
- The main deliverable is a cohesive mobile-first experience that works for real user actions, not a static design mockup.