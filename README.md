# DIY YouTube Summarizer

Paste a YouTube link, get plain-text notes back. Pulls the video's transcript and hands it to Gemini for a summary — no markdown, no fluff.

## How it works

1. Drop in a YouTube URL
2. The server fetches the transcript (needs captions on)
3. Gemini reads it and writes a short summary

## Desktop app (Windows)

A standalone window app, no browser tab, no terminal. First run asks for a Gemini key ([get one free](https://aistudio.google.com/apikey)) and saves it to `%APPDATA%\TranscriptDeck\config.json` — enter it once.

Build it yourself:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt pyinstaller
pyinstaller --name "TranscriptDeck" --onefile --windowed --add-data "templates;templates" --add-data "static;static" desktop.py
```

The finished app lands at `dist\TranscriptDeck.exe` — copy it anywhere and double-click to run.

## Run in browser instead

```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python main.py
```

Open `http://localhost:5000`. Key can also be set via `GEMINI_API_KEY` env var instead of the in-app prompt.

## Stack

- Flask backend
- `youtube-transcript-api` for transcripts
- Gemini (`google-genai`) for summarization
- Plain HTML/CSS/JS frontend, no build step

## Notes

- Only works on videos with captions available.
- `GEMINI_API_KEY` must be set as an environment variable — never commit it.
