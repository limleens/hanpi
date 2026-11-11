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
- Tap **Recognize characters**, verify/edit the proposed Chinese text, and tap **Use verified text** to open Results.
- Tap a character/pinyin to open Spotlight, then **Listen** and **Try it**. Record an isolated syllable and tap **Check my tone**. Settings selects Female/Male natural voice, speed, or browser speech; network failure falls back to browser speech where available.

**Important:** Browser camera/microphone access requires a secure HTTPS origin outside localhost. Browser/speech behavior may vary across iOS versions.

## 2. What runs where?

Your phone captures the image and voice in the browser, but the Python OCR and tone-analysis models run on the **Windows computer hosting the app**. Your computer and its Internet connection must remain available. This is not a standalone iPhone app.

The optional natural Mandarin voices use Edge's online neural TTS service through the `edge-tts` package (LGPLv3, see upstream license). Chinese text goes to that third-party provider only when the user taps Listen with natural voice selected. The browser voice preference in Settings and automatic browser fallback remain available.

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


## Five-minute release check on your real iPhone

Prepare dependencies/model on the computer before this check:

```powershell
.\.venv\Scripts\python.exe scripts/check_environment.py --strict
.\.venv\Scripts\python.exe scripts/prepare_asr.py
.\.venv\Scripts\python.exe scripts/check_environment.py --strict --asr
$env:HANPI_SHARE = "1"
$env:HANPI_DEMO_USER = "hanpi-demo"
$privatePassword = Read-Host "Private demo password (at least 10 characters)" -AsSecureString
$env:HANPI_DEMO_PASSWORD = [System.Net.NetworkCredential]::new("", $privatePassword).Password
.\.venv\Scripts\python.exe app.py
```

The share link is temporary and depends on Gradio's external tunnel service. Keep the computer running; do not post the password or link publicly. The password prompt above avoids putting its value into shell history.

1. Open the printed HTTPS share link in Safari; confirm login is required and sign in.
2. Select **English → Chinese**, search `eat`, choose 吃. Select **Pinyin lookup**, search `ma3`, then `mǎ`; verify the third-tone choices.
3. Scan your actual menu using the rear-camera control, allow permission, and verify/edit the proposed characters **before** pressing Use verified text. Try the original narrow red crop too.
4. Type 我喜欢咖啡. Tap Listen, then Try the whole phrase; record once correctly and once with a different word. Review recording, inspect/edit “I heard”, and tap a flagged target character. Text differences can be ASR mistakes; they are not measured tone errors. For isolated tone coaching, record only the selected syllable.
5. Test playback, save/reopen a phrase, and navigate all four tabs without sideways scrolling. If neural TTS is unavailable, choose Browser voice in Settings and check whether the device has a Mandarin voice.

This checklist is **not marked passed** by the automated desktop runs. Real camera/mic permissions, audible playback and Safari behavior require your phone. Avoid personal vocabulary in a shared demo; everyone authenticated to that instance uses the same host-local SQLite library.
