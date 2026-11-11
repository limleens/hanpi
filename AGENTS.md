# Hanpi — Codex working instructions

## Read first
Before any code changes, read:
1. `docs/V1_PRODUCT_SPEC.md` — the source of truth for product and UX decisions.
2. `README.md` — stack, setup, privacy, and current limitations.
3. `TASKS.md` and GitHub issue #1 — current implementation and validation tasks.
4. `app.py`, the modules under `hanpi_core/`, and the relevant tests.

## Goal
Ship an **elegant, mobile-first, working Mandarin learning app** for the Hiya Voice AI Challenge (Real-Time Assistance). Brand: **Hanpi (汉拼)**. Tagline: **snap, translate, learn!**

Keep the **simple, uncluttered UI concept** agreed with the user:
- Warm cream background, restrained coral/orange accent, readable dark typography, generous whitespace, refined rounded cards.
- Compact logo/wordmark, search bar at the top, and clear navigation: **Scan**, **Type**, **Speak**, **Saved**.
- Scan/Type/Speak should all lead into **one shared Results surface**: Chinese characters, aligned coloured pinyin, translation and key vocabulary.
- Tapping a character enters **Spotlight practice**: other characters dim; active character and pinyin stay vibrant; listen → speak → feedback → retry/back.
- Group advanced settings behind a gear/accordion; default natural Mandarin voice. Voice choices Female/Male and speeds 0.75×, 1×, 1.25×.
- Make genuine interactive controls work, with loading/error/success states. Avoid decorative/dead buttons, giant debug charts, or unrelated panels.

## Preserve existing stack and behavior
- Stay with Python + Gradio for this submission, not a Next.js rewrite.
- Keep RapidOCR/ONNX, PyPinyin, offline CC-CEDICT, optional online translation, Parselmouth pitch extraction, optional Whisper, edge-tts neural reference speech, and SQLite starred vocabulary.
- Preserve the working Scan → editable OCR → pinyin/meaning → selected syllable practice flow and local saved data. No silent truncation at 24 Hanzi.
- Keep `README.md`, `ai.md`, phone HTTPS authentication, setup instructions and tests accurate.
- Don't publish personal data or credentials. Don't disable remote auth. SQLite Starred data is shared across the temporary hosted session; never present it as per-user cloud sync.

## Accuracy / scope
- Acoustic F0 shape classification is **experimental** and evaluates one isolated syllable at a time. It does **not** identify consonant errors (zh/sh/ch), verify vocabulary pronunciation, or grade every tone of a recorded sentence.
- Never fake such detection, generate arbitrary percentage scores, or claim the user pronounced a full sentence correctly when unsupported.
- Tone-sandhi and articulation illustrations are teaching tips, not acoustic diagnoses.
- Natural TTS is online; keep browser-speech fallback and a meaningful offline/error state.
- Don't claim permanent iPhone hosting until actually deployed and field-tested.

## Implementation workflow
- **Create a feature branch** for a significant UI refactor. Do not overwrite `main` while work is untested.
- Prefer a cohesive experience over adding more features; use staged improvements and preserve existing callbacks.
- First run baseline tests. After changes run `python -m pytest -q`, a Gradio startup smoke test, and, when possible, a browser/phone-width walkthrough.
- Report exactly what was changed, test results, screenshots or observable behavior, and what still needs manual iPhone/microphone verification.
- Open a pull request for review and update `TASKS.md` and GitHub issue #1 with progress and remaining blockers.
- If an environment has no access to camera/microphone or external audio service, say so and DO NOT mark those tests complete.
- Do not allow UI polish to jeopardize the submission. The user is targeting **11 November 2026 at 23:59 GMT**, subject to the live Ashby portal's authoritative deadline.

## Visual identity update — user feedback on 11 Nov 2026
The user found the first redesign too generic. Do not revert to the serif/beige minimalist theme. Preserve the same simple UI structure but use a deliberate, friendly, bubbly, Duolingo-adjacent (not copied) learning-app personality:
- Reference the user's PathPilot Figma style guide: https://www.figma.com/design/mIhSWi1AfxqrE7zMvdnftS/pathpilot?node-id=0-1
- Headings/wordmark: Fredoka; body controls: Plus Jakarta Sans from Figma; readable Chinese font fallback. See hanpi_ui/style.css.
- Bright orange, teal and navy accents on warm cream; short tactile buttons, rounded flashcards, original CSS Hanzi mark and small speech-bubble mascot.
- Keep the interface airy, not cluttered: only the active task needs emphasis; avoid big gradients, random emoji piles, generic stock illustrations and fake feedback.
- See docs/VISUAL_DESIGN.md. Review on real phone widths before merging.
