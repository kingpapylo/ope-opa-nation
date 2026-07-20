"""
Termux phone tools — SMS, battery, camera, contacts, notifications, location.
All tools use termux-api commands. On Linux they return a friendly error.
"""

import subprocess
import json
import os


def _is_termux() -> bool:
    return (
        os.environ.get("TERMUX_VERSION") is not None
        or os.path.isdir("/data/data/com.termux")
        or os.environ.get("PREFIX", "").startswith("/data/data/com.termux")
    )


def _run(cmd: str, timeout: int = 15) -> str:
    if not _is_termux():
        return "⚠️  This tool only works on Termux (Android). Not available on Linux."
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        out = (result.stdout + result.stderr).strip()
        return out if out else f"(exit code {result.returncode})"
    except subprocess.TimeoutExpired:
        return "Error: command timed out."
    except Exception as e:
        return f"Error: {e}"


# ── Definitions ──────────────────────────────────────────────────────────────

SMS_SEND_DEFINITION = {
    "type": "function",
    "function": {
        "name": "phone_sms_send",
        "description": "Send an SMS message to a phone number (Termux only).",
        "parameters": {
            "type": "object",
            "properties": {
                "number": {"type": "string", "description": "Phone number to send to."},
                "message": {"type": "string", "description": "Message text to send."},
            },
            "required": ["number", "message"],
        },
    },
}

SMS_LIST_DEFINITION = {
    "type": "function",
    "function": {
        "name": "phone_sms_list",
        "description": "List recent SMS messages (Termux only).",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max number of messages to return (default 10)."},
            },
            "required": [],
        },
    },
}

BATTERY_DEFINITION = {
    "type": "function",
    "function": {
        "name": "phone_battery",
        "description": "Get the current battery level and charging status (Termux only).",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}

CAMERA_DEFINITION = {
    "type": "function",
    "function": {
        "name": "phone_camera",
        "description": "Take a photo with the phone camera and save it to a file (Termux only).",
        "parameters": {
            "type": "object",
            "properties": {
                "output_path": {
                    "type": "string",
                    "description": "File path to save the photo, e.g. /sdcard/photo.jpg",
                },
                "camera_id": {
                    "type": "string",
                    "description": "Camera to use: '0' for back, '1' for front. Default '0'.",
                },
            },
            "required": ["output_path"],
        },
    },
}

CONTACTS_DEFINITION = {
    "type": "function",
    "function": {
        "name": "phone_contacts",
        "description": "List phone contacts (Termux only).",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}

NOTIFICATION_DEFINITION = {
    "type": "function",
    "function": {
        "name": "phone_notify",
        "description": "Send a notification to the phone's notification bar (Termux only).",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Notification title."},
                "message": {"type": "string", "description": "Notification body text."},
            },
            "required": ["title", "message"],
        },
    },
}

LOCATION_DEFINITION = {
    "type": "function",
    "function": {
        "name": "phone_location",
        "description": "Get the current GPS location of the phone (Termux only).",
        "parameters": {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Location provider: 'gps', 'network', or 'passive'. Default 'network'.",
                },
            },
            "required": [],
        },
    },
}

ALL_DEFINITIONS = [
    SMS_SEND_DEFINITION,
    SMS_LIST_DEFINITION,
    BATTERY_DEFINITION,
    CAMERA_DEFINITION,
    CONTACTS_DEFINITION,
    NOTIFICATION_DEFINITION,
    LOCATION_DEFINITION,
]


# ── Implementations ───────────────────────────────────────────────────────────

def sms_send(number: str, message: str) -> str:
    safe_msg = message.replace('"', '\\"')
    return _run(f'termux-sms-send -n "{number}" "{safe_msg}"')


def sms_list(limit: int = 10) -> str:
    raw = _run(f"termux-sms-list -l {limit}")
    try:
        msgs = json.loads(raw)
        lines = []
        for m in msgs:
            sender = m.get("address", "?")
            body = m.get("body", "")[:100]
            date = m.get("received", "")[:10]
            lines.append(f"  [{date}] {sender}: {body}")
        return "\n".join(lines) if lines else "No messages found."
    except Exception:
        return raw


def battery() -> str:
    raw = _run("termux-battery-status")
    try:
        data = json.loads(raw)
        pct = data.get("percentage", "?")
        status = data.get("status", "?")
        plugged = data.get("plugged", "?")
        return f"Battery: {pct}%  |  Status: {status}  |  Plugged: {plugged}"
    except Exception:
        return raw


def camera(output_path: str, camera_id: str = "0") -> str:
    return _run(f'termux-camera-photo -c {camera_id} "{output_path}"', timeout=30)


def contacts() -> str:
    raw = _run("termux-contact-list")
    try:
        data = json.loads(raw)
        lines = [f"  {c.get('name','?')}  —  {c.get('number','?')}" for c in data[:30]]
        total = len(data)
        result = "\n".join(lines)
        if total > 30:
            result += f"\n  ... and {total - 30} more"
        return result if lines else "No contacts found."
    except Exception:
        return raw


def notify(title: str, message: str) -> str:
    safe_t = title.replace('"', '\\"')
    safe_m = message.replace('"', '\\"')
    return _run(f'termux-notification --title "{safe_t}" --content "{safe_m}"')


def location(provider: str = "network") -> str:
    raw = _run(f"termux-location -p {provider} -r once", timeout=20)
    try:
        data = json.loads(raw)
        lat = data.get("latitude", "?")
        lon = data.get("longitude", "?")
        acc = data.get("accuracy", "?")
        return (
            f"Location: {lat}, {lon}\n"
            f"Accuracy: {acc}m\n"
            f"Google Maps: https://maps.google.com/?q={lat},{lon}"
        )
    except Exception:
        return raw
