# Hanpi — Visual identity refresh

A small design-language update on top of the working mobile-first UI. The app's flow and backend are unchanged.

## Visual reference
- [PathPilot Figma design and style guide](https://www.figma.com/design/mIhSWi1AfxqrE7zMvdnftS/pathpilot?node-id=0-1) supplied by the Hanpi creator.
- The style guide's **Plus Jakarta Sans** and strong orange, teal, and navy informed the typography and tokens.
- PathPilot itself is a structured, professional design. Hanpi adapts the discipline while becoming warmer and more playful for language learning.
- Duolingo-like **friendliness and tactile affordances** are a general inspiration, not copied artwork or interface assets.

## Typography
- Display/brand: **Fredoka** (rounded, cheerful, friendly at mobile sizes).
- UI/body: **Plus Jakarta Sans** (from the PathPilot Figma style guide).
- Hanzi: system Chinese fonts (Noto Sans SC, Microsoft YaHei, PingFang SC fallback) so Chinese characters remain clear.
- Google Fonts provides the Latin families online; local system fallbacks keep the app readable offline. No font files are committed.

## Palette and behaviour
- Ink: deep navy \`#17364C\`, echoing the Prussian blue in PathPilot.
- Warm action: \`#FF950A\` and sun-yellow \`#FFC85F\`.
- Teal signal: \`#05A8AA\`.
- Coral/red for accent and errors; soft cream canvas and white cards.
- Round corners, light two-tone surfaces, simple tactile 2px/4px borders and grounded button press interactions, **no big generic gradients**.
- Tone colours still come from the existing audio/pinyin presentation palette; don't overwrite the correct tone-to-colour mapping.

## Original mascots and artwork
- Brand-mark: an original hand-feeling '汉' tile with a pinyin tone accent, built in CSS.
- Scan-page companion: original CSS speech-bubble character with face and a little 'nǐ hǎo!' speech bubble. This is not from Duolingo and is not a copyrighted mascot copy.
- Both use HTML/CSS, so they remain lightweight, sharp on high-density phones and do not need additional files.

## UI and accessibility
- Single screen with stable Scan / Type / Speak / Saved navigation.
- Lesson shows readable aligned Hanzi/pinyin; Spotlight dims nonactive chips only during practice.
- Visible keyboard focus, large tap targets, reduced-motion support, readable Chinese-font fallbacks.
- The implementation changes *appearance only*. No simulated pronunciation accuracy, fake confetti, or unverified sentence-level grading.

## Review before merging PR #2
- [ ] Confirm the new type and mascot render correctly at 390px and desktop widths.
- [ ] Check buttons have enough contrast and bottom navigation is visible on Safari.
- [ ] Verify OCR → Results → Spotlight → Recording → Feedback → Saved flow still works.
- [ ] If Google Fonts cannot be reached, verify fallback fonts still look acceptable.
- [ ] Keep the original real-device limitations in the QA report; existing screenshots predate the style update.
