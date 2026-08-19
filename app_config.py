import json
import os

_CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "TranscriptDeck")
_CONFIG_PATH = os.path.join(_CONFIG_DIR, "config.json")

_FIELD = {
    "gemini": "gemini_api_key",
    "openai": "openai_api_key",
    "anthropic": "anthropic_api_key",
}
_ENV_VAR = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

PROVIDERS = tuple(_FIELD)


def _read_config() -> dict:
    if not os.path.exists(_CONFIG_PATH):
        return {}
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_config(data: dict) -> None:
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)


def get_key(provider: str) -> str | None:
    env_key = os.environ.get(_ENV_VAR[provider])
    if env_key:
        return env_key
    return _read_config().get(_FIELD[provider])


def set_key(provider: str, key: str) -> None:
    data = _read_config()
    data[_FIELD[provider]] = key
    _write_config(data)


def has_any_key() -> bool:
    return any(get_key(provider) for provider in PROVIDERS)
