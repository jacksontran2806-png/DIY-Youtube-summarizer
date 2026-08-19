import re
import json
import time
from flask import Flask, request, jsonify, render_template
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
import openai
import anthropic

import app_config

app = Flask(__name__)

MAX_VISUAL_MOMENTS = 4

# Tried in order — first configured provider wins, next one only runs if the
# previous fails (rate limit, outage, missing key). This is what gives the
# app "no problem running at all" even when one provider is down.
PROVIDER_CHAIN = ("gemini", "openai", "anthropic")


def get_gemini_client():
    key = app_config.get_key("gemini")
    return genai.Client(api_key=key) if key else None


def get_openai_client():
    key = app_config.get_key("openai")
    return openai.OpenAI(api_key=key) if key else None


def get_anthropic_client():
    key = app_config.get_key("anthropic")
    return anthropic.Anthropic(api_key=key) if key else None


def call_gemini(client, prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-3.7-flash",
        contents=prompt,
    )
    return response.text


def call_openai(client, prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def call_anthropic(client, prompt: str) -> str:
    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return next((block.text for block in response.content if block.type == "text"), "")


PROVIDERS = {
    "gemini": (get_gemini_client, call_gemini),
    "openai": (get_openai_client, call_openai),
    "anthropic": (get_anthropic_client, call_anthropic),
}


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

    configured = [p for p in PROVIDER_CHAIN if PROVIDERS[p][0]() is not None]
    if not configured:
        raise RuntimeError("No API key set yet for any provider. Add one above first.")

    errors = []
    for provider in configured:
        get_client, call = PROVIDERS[provider]
        client = get_client()

        for attempt in range(2):
            try:
                text = call(client, prompt).strip()
                text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
                data = json.loads(text)
                moments = data.get("visual_moments", [])[:MAX_VISUAL_MOMENTS]
                notes = {
                    "overview": data.get("overview", ""),
                    "sections": data.get("sections", []),
                }
                return notes, moments
            except Exception as e:
                print(f"{provider} attempt {attempt + 1} failed: {e}")
                if attempt == 0:
                    time.sleep(2)
                else:
                    errors.append(f"{provider}: {e}")

    raise RuntimeError("Every configured provider failed — " + "; ".join(errors))


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
    return render_template("index.html", has_key=app_config.has_any_key())


@app.route("/set-key", methods=["POST"])
def set_key_route():
    data = request.get_json() or {}
    provider = data.get("provider", "")
    key = (data.get("key") or "").strip()

    if provider not in app_config.PROVIDERS:
        return jsonify({"error": "Unknown provider."}), 400
    if not key:
        return jsonify({"error": "Key can't be empty."}), 400

    app_config.set_key(provider, key)
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