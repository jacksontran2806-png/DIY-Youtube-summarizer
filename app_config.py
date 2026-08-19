import json
import os

_CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "TranscriptDeck")
_CONFIG_PATH = os.path.join(_CONFIG_DIR, "config.json")


def get_api_key() -> str | None:
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key:
        return env_key

    if not os.path.exists(_CONFIG_PATH):
        return None

    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("gemini_api_key")


def set_api_key(key: str) -> None:
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"gemini_api_key": key}, f)
