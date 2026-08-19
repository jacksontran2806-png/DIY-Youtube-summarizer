# DIY YouTube Summarizer

Paste a YouTube link, get plain-text notes back. Pulls the video's transcript and hands it to Gemini for a summary — no markdown, no fluff.

## How it works

1. Drop in a YouTube URL
2. The server fetches the transcript (needs captions on)
3. Gemini reads it and writes a short summary

## Run it locally

```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

Set your Gemini key (get one at [aistudio.google.com](https://aistudio.google.com/apikey)):

```bash
setx GEMINI_API_KEY "your-key-here"   # Windows, new shell needed after
# or: export GEMINI_API_KEY="your-key-here"   # macOS/Linux
```

Then start the app:

```bash
python main.py
```

Open `http://localhost:5000`.

## Stack

- Flask backend
- `youtube-transcript-api` for transcripts
- Gemini (`google-genai`) for summarization
- Plain HTML/CSS/JS frontend, no build step

## Notes

- Only works on videos with captions available.
- `GEMINI_API_KEY` must be set as an environment variable — never commit it.
