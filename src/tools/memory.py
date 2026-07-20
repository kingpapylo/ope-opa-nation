"""
Memory tool — persist facts, notes, and preferences across sessions.
Stored at ~/.ope-opa-nation/memory.json
"""

import json
from pathlib import Path
from datetime import datetime

MEMORY_FILE = Path.home() / ".ope-opa-nation" / "memory.json"

SAVE_DEFINITION = {
    "type": "function",
    "function": {
        "name": "memory_save",
        "description": (
            "Save a fact, note, or preference to persistent memory. "
            "Use this to remember things the user tells you across sessions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Short label for this memory, e.g. 'user_name', 'favorite_language'.",
                },
                "value": {
                    "type": "string",
                    "description": "The value to remember.",
                },
            },
            "required": ["key", "value"],
        },
    },
}

RECALL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "memory_recall",
        "description": "Retrieve a specific memory by key, or list all saved memories.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The key to look up. Leave empty to list all memories.",
                },
            },
            "required": [],
        },
    },
}

FORGET_DEFINITION = {
    "type": "function",
    "function": {
        "name": "memory_forget",
        "description": "Delete a specific memory by key.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The key to delete.",
                },
            },
            "required": ["key"],
        },
    },
}


def _load() -> dict:
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save(data: dict) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def save(key: str, value: str) -> str:
    data = _load()
    data[key] = {"value": value, "saved_at": datetime.now().isoformat()}
    _save(data)
    return f"Remembered: {key} = {value}"


def recall(key: str = "") -> str:
    data = _load()
    if not data:
        return "Memory is empty."
    if key:
        entry = data.get(key)
        if not entry:
            return f"No memory found for key: {key}"
        return f"{key} = {entry['value']}  (saved {entry['saved_at'][:10]})"
    lines = [f"  • {k}: {v['value']}" for k, v in data.items()]
    return "All memories:\n" + "\n".join(lines)


def forget(key: str) -> str:
    data = _load()
    if key not in data:
        return f"No memory found for key: {key}"
    del data[key]
    _save(data)
    return f"Forgotten: {key}"


def load_all() -> dict:
    """Return raw memory dict — used to inject memories into system prompt."""
    return _load()
