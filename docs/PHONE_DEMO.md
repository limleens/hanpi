# Try Hanpi on an iPhone (temporary HTTPS demo)

Hanpi is a **responsive Gradio website**; you do not need a native iOS application.

## 1. Launch locally on Windows

Install Python 3.11 and follow the repository README to install dependencies.

In **PowerShell**, from the Hanpi project directory:

```powershell
$env:HANPI_SHARE = "1"
$env:HANPI_DEMO_USER = "hanpi-demo"
$env:HANPI_DEMO_PASSWORD = "choose-a-private-password-at-least-10-characters"
python app.py
```

The running Gradio server should print a temporary **https://...gradio.live** URL (if the external Gradio share service is available). **Never commit your password.** Only share both the URL and the credentials with someone you trust.

- Keep the terminal open; the link disappears when the desktop app stops.
- Open the HTTPS link in iPhone Safari.
- Sign in, then use the **Camera** source on the photo card to take a picture of Hanzi. Alternatively choose Upload to select a photo from your library.
- Allow camera/microphone permissions in Safari when prompted.
- Tap **Find Hanzi in photo**; review and correct the detected text.
- Play a browser voice or choose the optional online natural voice, record an isolated syllable, and review the experimental pitch feedback.

**Important:** Browser camera/microphone access requires a secure HTTPS origin outside localhost. Browser/speech behavior may vary across iOS versions.

## 2. What runs where?

Your phone captures the image and voice in the browser, but the Python OCR and tone-analysis models run on the **Windows computer hosting the app**. Your computer and its Internet connection must remain available. This is not a standalone iPhone app.

The optional natural Mandarin voices use Edge's online neural TTS service through the `edge-tts` package (LGPLv3, see upstream license). Chinese text goes to that third-party provider only when the user taps a natural voice button. The existing browser voice buttons remain available as a fallback.

## 3. Security and saved vocabulary

This is a **single-user prototype**. The Starred library is stored on the hosting computer in `data/hanpi_library.sqlite3`. It is **not** isolated by account and does **not** automatically sync to each visitor's phone. Remote mode refuses to start without a username and password, because anyone who can log in would otherwise share the same Starred collection. Do not use a common demo password publicly or expose personal data.

A permanent public deployment needs:
- A web host providing HTTPS and a running Python process.
- Per-user sessions and separated/persistent storage (or disable Starred in public demos).
- Abuse prevention / authentication for OCR and neural TTS endpoints.
- Mobile Safari testing with real camera and microphone recordings.

For an eventual permanent hosted Gradio app, a [Hugging Face Space](https://huggingface.co/docs/hub/spaces) or a container-capable cloud host is possible, but **this repository has not been deployed** to a permanent public website.

## 4. Testing checklist

- [ ] Temporary HTTPS URL opens in iPhone Safari.
- [ ] Camera permission granted, photo captured, OCR extracts visible Hanzi.
- [ ] Mobile cards and buttons fit the screen without clipping.
- [ ] Microphone recording returns an audio sample.
- [ ] Browser Chinese TTS plays on iPhone.
- [ ] Natural voice selector generates and plays audio when connected.
- [ ] Star a word, restart Windows app, and verify the entry remains saved.
- [ ] No public exposure of shared vocabulary or passwords.
