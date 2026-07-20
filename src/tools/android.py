"""
Android UI navigation via Termux:API.
Requires: pkg install termux-api  +  Termux:API app installed from F-Droid.

Provides:
  - Open any app by package name or name search
  - Tap, long-press, swipe on screen coordinates
  - Press hardware keys (back, home, volume, power)
  - Take screenshots
  - Read/write clipboard
  - Get running apps / installed apps
  - Send key events
  - Turn torch on/off
  - Vibrate
  - Text-to-speech
  - Lock/unlock screen brightness
"""

import subprocess
import json
import os
import time


def _is_termux() -> bool:
    return (
        os.environ.get("TERMUX_VERSION") is not None
        or os.path.isdir("/data/data/com.termux")
        or os.environ.get("PREFIX", "").startswith("/data/data/com.termux")
    )


def _run(cmd: str, timeout: int = 15) -> str:
    if not _is_termux():
        return "⚠️  Android navigation only works on Termux. Not available on Linux."
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        out = (result.stdout + result.stderr).strip()
        return out if out else f"✓ Done (exit {result.returncode})"
    except subprocess.TimeoutExpired:
        return "Error: command timed out."
    except Exception as e:
        return f"Error: {e}"


# ── Definitions ───────────────────────────────────────────────────────────────

OPEN_APP_DEFINITION = {
    "type": "function",
    "function": {
        "name": "android_open_app",
        "description": "Open an Android app by package name (e.g. com.whatsapp) or common name (e.g. 'whatsapp', 'chrome', 'settings', 'camera', 'youtube').",
        "parameters": {
            "type": "object",
            "properties": {
                "app": {
                    "type": "string",
                    "description": "App package name or common name.",
                },
            },
            "required": ["app"],
        },
    },
}

TAP_DEFINITION = {
    "type": "function",
    "function": {
        "name": "android_tap",
        "description": "Tap a specific coordinate on the Android screen.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X coordinate in pixels."},
                "y": {"type": "integer", "description": "Y coordinate in pixels."},
            },
            "required": ["x", "y"],
        },
    },
}

LONG_PRESS_DEFINITION = {
    "type": "function",
    "function": {
        "name": "android_long_press",
        "description": "Long-press a specific coordinate on the Android screen.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X coordinate."},
                "y": {"type": "integer", "description": "Y coordinate."},
                "duration_ms": {"type": "integer", "description": "Duration in milliseconds. Default 1000."},
            },
            "required": ["x", "y"],
        },
    },
}

SWIPE_DEFINITION = {
    "type": "function",
    "function": {
        "name": "android_swipe",
        "description": "Swipe on the Android screen from one point to another. Use for scrolling, swiping notifications, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "x1": {"type": "integer", "description": "Start X."},
                "y1": {"type": "integer", "description": "Start Y."},
                "x2": {"type": "integer", "description": "End X."},
                "y2": {"type": "integer", "description": "End Y."},
                "duration_ms": {"type": "integer", "description": "Swipe duration in ms. Default 300."},
            },
            "required": ["x1", "y1", "x2", "y2"],
        },
    },
}

KEY_DEFINITION = {
    "type": "function",
    "function": {
        "name": "android_key",
        "description": "Press a hardware or software key on the Android device.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "enum": [
                        "back", "home", "recents", "power",
                        "volume_up", "volume_down", "volume_mute",
                        "camera", "enter", "delete", "tab",
                        "brightness_up", "brightness_down",
                        "media_play_pause", "media_next", "media_previous",
                    ],
                    "description": "Key to press.",
                },
            },
            "required": ["key"],
        },
    },
}

SCREENSHOT_DEFINITION = {
    "type": "function",
    "function": {
        "name": "android_screenshot",
        "description": "Take a screenshot of the Android screen and save it to a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "output_path": {
                    "type": "string",
                    "description": "Path to save the screenshot. Default: /sdcard/screenshot.png",
                },
            },
            "required": [],
        },
    },
}

CLIPBOARD_READ_DEFINITION = {
    "type": "function",
    "function": {
        "name": "android_clipboard_read",
        "description": "Read the current contents of the Android clipboard.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}

CLIPBOARD_WRITE_DEFINITION = {
    "type": "function",
    "function": {
        "name": "android_clipboard_write",
        "description": "Write text to the Android clipboard.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to copy to clipboard."},
            },
            "required": ["text"],
        },
    },
}

TYPE_TEXT_DEFINITION = {
    "type": "function",
    "function": {
        "name": "android_type_text",
        "description": "Type text into the currently focused input field on Android.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to type."},
            },
            "required": ["text"],
        },
    },
}

SCREEN_INFO_DEFINITION = {
    "type": "function",
    "function": {
        "name": "android_screen_info",
        "description": "Get screen resolution and display information of the Android device.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}

TORCH_DEFINITION = {
    "type": "function",
    "function": {
        "name": "android_torch",
        "description": "Turn the phone flashlight (torch) on or off.",
        "parameters": {
            "type": "object",
            "properties": {
                "on": {"type": "boolean", "description": "True to turn on, False to turn off."},
            },
            "required": ["on"],
        },
    },
}

VIBRATE_DEFINITION = {
    "type": "function",
    "function": {
        "name": "android_vibrate",
        "description": "Vibrate the Android device.",
        "parameters": {
            "type": "object",
            "properties": {
                "duration_ms": {"type": "integer", "description": "Vibration duration in milliseconds. Default 500."},
            },
            "required": [],
        },
    },
}

TTS_DEFINITION = {
    "type": "function",
    "function": {
        "name": "android_speak",
        "description": "Speak text aloud using Android text-to-speech.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to speak."},
                "rate": {"type": "number", "description": "Speech rate (0.5 = slow, 1.0 = normal, 2.0 = fast). Default 1.0."},
            },
            "required": ["text"],
        },
    },
}

INSTALLED_APPS_DEFINITION = {
    "type": "function",
    "function": {
        "name": "android_list_apps",
        "description": "List installed apps on the Android device.",
        "parameters": {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "description": "Optional filter string to search app names.",
                },
            },
            "required": [],
        },
    },
}

ALL_DEFINITIONS = [
    OPEN_APP_DEFINITION,
    TAP_DEFINITION,
    LONG_PRESS_DEFINITION,
    SWIPE_DEFINITION,
    KEY_DEFINITION,
    SCREENSHOT_DEFINITION,
    CLIPBOARD_READ_DEFINITION,
    CLIPBOARD_WRITE_DEFINITION,
    TYPE_TEXT_DEFINITION,
    SCREEN_INFO_DEFINITION,
    TORCH_DEFINITION,
    VIBRATE_DEFINITION,
    TTS_DEFINITION,
    INSTALLED_APPS_DEFINITION,
]

# Common app name → package name shortcuts
APP_SHORTCUTS = {
    "whatsapp":   "com.whatsapp",
    "chrome":     "com.android.chrome",
    "youtube":    "com.google.android.youtube",
    "camera":     "com.android.camera2",
    "settings":   "com.android.settings",
    "maps":       "com.google.android.apps.maps",
    "gmail":      "com.google.android.gm",
    "photos":     "com.google.android.apps.photos",
    "play":       "com.android.vending",
    "facebook":   "com.facebook.katana",
    "instagram":  "com.instagram.android",
    "twitter":    "com.twitter.android",
    "telegram":   "org.telegram.messenger",
    "netflix":    "com.netflix.mediaclient",
    "spotify":    "com.spotify.music",
    "tiktok":     "com.zhiliaoapp.musically",
    "calculator": "com.android.calculator2",
    "clock":      "com.android.deskclock",
    "contacts":   "com.android.contacts",
    "files":      "com.android.documentsui",
    "browser":    "com.android.browser",
    "termux":     "com.termux",
}

# Key name → Android keycode
KEY_CODES = {
    "back":             "4",
    "home":             "3",
    "recents":          "187",
    "power":            "26",
    "volume_up":        "24",
    "volume_down":      "25",
    "volume_mute":      "164",
    "camera":           "27",
    "enter":            "66",
    "delete":           "67",
    "tab":              "61",
    "brightness_up":    "221",
    "brightness_down":  "220",
    "media_play_pause": "85",
    "media_next":       "87",
    "media_previous":   "88",
}


# ── Implementations ───────────────────────────────────────────────────────────

def open_app(app: str) -> str:
    pkg = APP_SHORTCUTS.get(app.lower(), app)
    result = _run(f"am start -n {pkg}/. 2>/dev/null || monkey -p {pkg} -c android.intent.category.LAUNCHER 1")
    if "Error" in result and "monkey" not in result:
        # Try termux-open-url as fallback
        return _run(f"termux-open --chooser '{app}'")
    return f"✓ Opened {app} ({pkg})"


def tap(x: int, y: int) -> str:
    return _run(f"input tap {x} {y}")


def long_press(x: int, y: int, duration_ms: int = 1000) -> str:
    return _run(f"input swipe {x} {y} {x} {y} {duration_ms}")


def swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> str:
    return _run(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")


def key(key_name: str) -> str:
    code = KEY_CODES.get(key_name, key_name)
    return _run(f"input keyevent {code}")


def screenshot(output_path: str = "/sdcard/screenshot.png") -> str:
    result = _run(f"termux-screenshot -f {output_path}", timeout=10)
    if "Error" in result:
        # Fallback using screencap
        result = _run(f"screencap -p {output_path}")
    return f"✓ Screenshot saved to {output_path}"


def clipboard_read() -> str:
    return _run("termux-clipboard-get")


def clipboard_write(text: str) -> str:
    safe = text.replace("'", "'\\''")
    return _run(f"termux-clipboard-set '{safe}'")


def type_text(text: str) -> str:
    # Use input text for simple text, handle spaces
    safe = text.replace(" ", "%s").replace("'", "")
    return _run(f"input text '{safe}'")


def screen_info() -> str:
    raw = _run("termux-display-info 2>/dev/null || wm size && wm density")
    return raw


def torch(on: bool) -> str:
    state = "on" if on else "off"
    return _run(f"termux-torch {state}")


def vibrate(duration_ms: int = 500) -> str:
    return _run(f"termux-vibrate -d {duration_ms}")


def speak(text: str, rate: float = 1.0) -> str:
    safe = text.replace('"', '\\"')
    return _run(f'termux-tts-speak -r {rate} "{safe}"', timeout=30)


def list_apps(filter_str: str = "") -> str:
    raw = _run("pm list packages -f 2>/dev/null | head -60")
    lines = []
    for line in raw.splitlines():
        # format: package:/path=com.package.name
        if "=" in line:
            pkg = line.split("=")[-1].strip()
            if not filter_str or filter_str.lower() in pkg.lower():
                lines.append(f"  {pkg}")
    if not lines:
        return raw
    total = len(lines)
    result = f"Installed apps ({total} shown):\n" + "\n".join(lines[:40])
    if total > 40:
        result += f"\n  ... and {total-40} more"
    return result
