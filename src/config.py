"""
Configuration and API key management.
Auto-detects Termux vs Linux and sets correct storage paths.
"""

import os
import json
from pathlib import Path


# ─── Environment detection ──────────────────────────────────────────────────

def is_termux() -> bool:
    """Return True if running inside Termux on Android."""
    return (
        os.environ.get("TERMUX_VERSION") is not None
        or os.path.isdir("/data/data/com.termux")
        or os.environ.get("PREFIX", "").startswith("/data/data/com.termux")
    )


def get_storage_root() -> Path:
    """
    Return the best storage path for saving project files.

    - Termux: /sdcard/OPE-OPA-NATION  (phone internal storage, visible in Files app)
    - Linux:  ~/OPE-OPA-NATION
    """
    if is_termux():
        # /sdcard is a symlink to /storage/emulated/0 — the main phone storage
        sdcard = Path("/sdcard/OPE-OPA-NATION")
        # Fallback to Termux home if /sdcard isn't accessible yet
        if sdcard.parent.exists():
            return sdcard
        return Path.home() / "OPE-OPA-NATION"
    return Path.home() / "OPE-OPA-NATION"


def get_config_dir() -> Path:
    """Return the config directory (always inside Termux/Linux home, not sdcard)."""
    if is_termux():
        return Path.home() / ".ope-opa-nation"
    return Path.home() / ".ope-opa-nation"


# ─── Config schema ───────────────────────────────────────────────────────────

CONFIG_DIR  = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS: dict = {
    "model": "gpt-4o",
    "provider": "openai",       # openai | anthropic
    "max_tokens": 4096,
    "storage_root": str(get_storage_root()),
    "system_prompt": (
        "You are OPE-OPA-NATION, a rainbow AI-powered terminal assistant. "
        "You can run shell commands, read and write files, search the web, "
        "and help with coding tasks. Be concise and direct. "
        "When you run commands or edit files, always show what you are doing."
    ),
}


# ─── Load / save ─────────────────────────────────────────────────────────────

def load_config() -> dict:
    """Load config from file, falling back to defaults."""
    config = DEFAULTS.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                saved = json.load(f)
            config.update(saved)
        except (json.JSONDecodeError, OSError):
            pass
    return config


def save_config(config: dict) -> None:
    """Persist config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


# ─── API key helpers ─────────────────────────────────────────────────────────

def get_api_key(provider: str) -> str | None:
    """Get API key from env var first, then config file."""
    env_vars = {
        "openai":    "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    env_key = env_vars.get(provider)
    if env_key:
        value = os.environ.get(env_key)
        if value:
            return value
    config = load_config()
    return config.get(f"{provider}_api_key")


def set_api_key(provider: str, key: str) -> None:
    """Save API key to config file."""
    config = load_config()
    config[f"{provider}_api_key"] = key
    save_config(config)


# ─── Storage helpers ─────────────────────────────────────────────────────────

def ensure_storage() -> Path:
    """
    Create the storage root directory and return its path.
    On Termux this is /sdcard/OPE-OPA-NATION (phone storage).
    """
    root = Path(load_config()["storage_root"])
    root.mkdir(parents=True, exist_ok=True)
    return root
