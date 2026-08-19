# DIY YouTube Summarizer

Paste a YouTube link, get structured notes back — headings, bullet sections, and step lists when the video is actually a tutorial. Pulls the transcript and hands it to an AI model for the writeup, with automatic fallback across providers so one outage doesn't take the app down.

## How it works

1. Drop in a YouTube URL
2. The server fetches the transcript (needs captions on)
3. Gemini (or OpenAI, or Anthropic — whichever is configured) reads it and breaks it into an overview, labeled sections, and a real numbered steps list if the video is a genuine walkthrough — not one flat paragraph. It also flags moments where something on screen (a chart, diagram, demo) is worth watching rather than reading, as clickable timestamp links straight to that point in the video
4. Every heading, bullet, and step is normal page text — select and copy just the part you want, or hit "Copy all" for the whole thing at once

## Provider fallback

Add a key for Gemini, OpenAI, and/or Anthropic via "manage API keys" on the page. Only one is required — add more than one and the app tries them in order (Gemini → OpenAI → Anthropic), moving to the next automatically if one is down, rate-limited, or out of quota. Each provider gets 2 tries before the app moves on.

## Desktop app (Windows)

A standalone window app, no browser tab, no terminal. Double-click `TranscriptDeck.exe` to open it — same as any other app, nothing to install. First run asks for at least one API key and saves it to `%APPDATA%\TranscriptDeck\config.json` — enter it once, every run after that opens straight to the input box.

Build it yourself:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt pyinstaller
pyinstaller --name "TranscriptDeck" --onefile --windowed --icon "app_icon.ico" --add-data "templates;templates" --add-data "static;static" desktop.py
```

The finished app lands at `dist\TranscriptDeck.exe` — copy it anywhere and double-click to run.

## Run in browser instead

```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python main.py
```

Open `http://localhost:5000`. Keys can also be set via `GEMINI_API_KEY`, `OPENAI_API_KEY`, and/or `ANTHROPIC_API_KEY` env vars instead of the in-app prompt — env vars always win over a saved key for that provider.

## Stack

- Flask backend
- `youtube-transcript-api` for transcripts
- `google-genai`, `openai`, and `anthropic` — whichever are configured, tried in that order
- Plain HTML/CSS/JS frontend, no build step

## Notes

- Only works on videos with captions available.
- API keys are stored locally (`%APPDATA%\TranscriptDeck\config.json` or the matching env var) — never commit them.
- Notes only ever show text and links back to YouTube — no video frames are downloaded or embedded. YouTube's anti-bot protections (PO tokens) block that path without adding a heavy, fragile Node.js dependency, so it's not worth it.
<img width="870" height="927" alt="image" src="https://github.com/user-attachments/assets/0d3dc5c0-1816-4b0d-973e-03dd20d258fe" />
