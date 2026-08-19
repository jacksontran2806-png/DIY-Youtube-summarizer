import re
import os
from flask import Flask, request, jsonify, render_template
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

if not os.environ.get("GEMINI_API_KEY"):
    raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

gemini_client = genai.Client()
app = Flask(__name__)


def extract_video_id(url: str) -> str | None:
    # handles both youtube.com/watch?v=... and the youtu.be/... short links
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11})",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_transcript(video_id: str) -> str:
    transcript = YouTubeTranscriptApi().fetch(video_id)
    return " ".join(snippet.text for snippet in transcript)


import time
import re

def strip_markdown(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)   # **bold** -> bold
    text = re.sub(r"\*(.*?)\*", r"\1", text)        # *italic* -> italic
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)  # remove # ## ### headers
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)     # remove --- dividers
    text = re.sub(r"^[\*\-]\s+", "• ", text, flags=re.MULTILINE)  # * bullets -> •
    return text.strip()

def summarize(transcript: str) -> str:
    prompt = (
        "Summarize this YouTube video transcript. "
    "Include the main topic, key points, and takeaways. "
    "Write in plain text only — no Markdown, no asterisks, no pound signs, no headers.\n\n"
    f"Transcript:\n{transcript[:12000]}"
    )

    last_error = None
    for attempt in range(3):
        try:
            response = gemini_client.models.generate_content(
                model="gemini-3.7-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            last_error = e
            print(f"Gemini attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 * (attempt + 1))  # wait 2s, then 4s, before retrying

    raise RuntimeError(f"Gemini couldn't summarize this one after 3 tries: {last_error}")

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/summarize", methods=["POST"])
def summarize_route():
    data = request.get_json() or {}
    url = data.get("url", "")

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "That doesn't look like a valid YouTube URL."}), 400

    try:
        transcript = get_transcript(video_id)
    except Exception as e:
        return jsonify({"error": f"Couldn't fetch a transcript for this video: {e}"}), 400

    try:
        summary = summarize(transcript)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"summary": summary})


if __name__ == "__main__":
    app.run(debug=True, port=5000)