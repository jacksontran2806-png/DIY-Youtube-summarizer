import re
import json
import time
from flask import Flask, request, jsonify, render_template
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

import app_config

app = Flask(__name__)

MAX_VISUAL_MOMENTS = 4


def get_gemini_client():
    key = app_config.get_api_key()
    if not key:
        return None
    return genai.Client(api_key=key)


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


def get_transcript_with_timestamps(video_id: str) -> str:
    snippets = YouTubeTranscriptApi().fetch(video_id)
    lines = []
    for s in snippets:
        mm, ss = divmod(int(s.start), 60)
        lines.append(f"[{mm:02d}:{ss:02d}] {s.text}")
    return "\n".join(lines)


def format_mmss(seconds: int) -> str:
    mm, ss = divmod(max(int(seconds), 0), 60)
    return f"{mm:02d}:{ss:02d}"


def analyze(transcript_with_ts: str) -> tuple[dict, list[dict]]:
    client = get_gemini_client()
    if client is None:
        raise RuntimeError("No Gemini API key set yet. Add one above first.")

    prompt = (
        "You're given a YouTube transcript where each line is stamped [MM:SS].\n"
        "Return ONLY valid JSON (no markdown fences, no commentary) shaped exactly like:\n"
        '{"overview": "...", "sections": [{"heading": "...", "type": "bullets", "items": ["...", "..."]}], '
        '"visual_moments": [{"seconds": 125, "reason": "..."}]}\n\n'
        "overview: 1-2 plain-text sentences naming the video's main topic. No markdown.\n\n"
        "sections: break the content into logical, well-labeled sections — however many actually fit "
        "the video, not a fixed template. Pick headings that describe what's actually in each one "
        "(e.g. \"Key Points\", \"Why It Matters\", \"Tools Used\", \"Takeaways\") rather than generic "
        "labels. Use type \"steps\" ONLY for a section that is a genuine ordered sequence the viewer "
        "would follow in order (a tutorial, a recipe, a setup process) — everything else use type "
        "\"bullets\". Each item is one plain-text sentence or phrase, no markdown, no asterisks.\n\n"
        f"visual_moments: up to {MAX_VISUAL_MOMENTS} timestamps (as total seconds, integer) "
        "where something shown on screen — a chart, graph, diagram, code, table, or demo — would "
        "land better as an image than a text description. Only flag moments where the transcript "
        "itself signals something is being shown (phrases like \"as you can see\", \"this chart\", "
        "\"look at this\", \"here's the graph\"). Return an empty list if nothing like that happens.\n\n"
        f"Transcript:\n{transcript_with_ts[:14000]}"
    )

    last_error = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.7-flash",
                contents=prompt,
            )
            text = response.text.strip()
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
            data = json.loads(text)
            moments = data.get("visual_moments", [])[:MAX_VISUAL_MOMENTS]
            notes = {
                "overview": data.get("overview", ""),
                "sections": data.get("sections", []),
            }
            return notes, moments
        except Exception as e:
            last_error = e
            print(f"Gemini attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 * (attempt + 1))  # wait 2s, then 4s, before retrying

    raise RuntimeError(f"Gemini couldn't summarize this one after 3 tries: {last_error}")


def format_moments(moments: list[dict]) -> list[dict]:
    formatted = []
    for moment in moments:
        seconds = int(moment.get("seconds", 0))
        formatted.append({
            "time": format_mmss(seconds),
            "seconds": seconds,
            "reason": moment.get("reason", ""),
        })
    return formatted


@app.route("/")
def index():
    return render_template("index.html", has_key=bool(app_config.get_api_key()))


@app.route("/set-key", methods=["POST"])
def set_key_route():
    data = request.get_json() or {}
    key = data.get("key", "").strip()
    if not key:
        return jsonify({"error": "Key can't be empty."}), 400
    app_config.set_api_key(key)
    return jsonify({"ok": True})


@app.route("/summarize", methods=["POST"])
def summarize_route():
    data = request.get_json() or {}
    url = (data.get("url") or "").strip()

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "That doesn't look like a valid YouTube URL."}), 400

    try:
        transcript = get_transcript_with_timestamps(video_id)
    except Exception as e:
        return jsonify({"error": f"Couldn't fetch a transcript for this video: {e}"}), 400

    try:
        notes, moments = analyze(transcript)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    visual_moments = format_moments(moments)

    return jsonify({"notes": notes, "visual_moments": visual_moments, "video_id": video_id})


if __name__ == "__main__":
    app.run(debug=True, port=5000)