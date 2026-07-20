"""
Terminal filesystem navigation.
Gives the agent awareness of the current directory and lets it
navigate, explore, search, and bookmark locations.

State (current directory + bookmarks) is persisted to
~/.ope-opa-nation/navigator.json
"""

import os
import json
import fnmatch
import subprocess
from pathlib import Path
from datetime import datetime

STATE_FILE = Path.home() / ".ope-opa-nation" / "navigator.json"

# ── State management ──────────────────────────────────────────────────────────

def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "cwd": str(Path.home()),
        "bookmarks": {
            "home":    str(Path.home()),
            "sdcard":  "/sdcard",
            "termux":  "/data/data/com.termux/files/home",
        },
        "history": [],
    }


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_cwd() -> str:
    return _load_state()["cwd"]


# ── Definitions ───────────────────────────────────────────────────────────────

CD_DEFINITION = {
    "type": "function",
    "function": {
        "name": "nav_cd",
        "description": "Change the current working directory. Supports ~, .., relative and absolute paths, and bookmark names.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory to change to. Use '~' for home, '..' for parent, or a bookmark name.",
                },
            },
            "required": ["path"],
        },
    },
}

PWD_DEFINITION = {
    "type": "function",
    "function": {
        "name": "nav_pwd",
        "description": "Print the current working directory.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}

LS_DEFINITION = {
    "type": "function",
    "function": {
        "name": "nav_ls",
        "description": "List files and directories in the current or specified directory with details.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory to list. Defaults to current directory.",
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files (starting with dot). Default false.",
                },
            },
            "required": [],
        },
    },
}

TREE_DEFINITION = {
    "type": "function",
    "function": {
        "name": "nav_tree",
        "description": "Show a directory tree structure.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Root path to show tree from. Defaults to current directory.",
                },
                "depth": {
                    "type": "integer",
                    "description": "Max depth to traverse. Default 3.",
                },
            },
            "required": [],
        },
    },
}

FIND_DEFINITION = {
    "type": "function",
    "function": {
        "name": "nav_find",
        "description": "Find files or directories matching a pattern.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Filename pattern to search for, e.g. '*.py', 'config*'.",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in. Defaults to current directory.",
                },
                "type": {
                    "type": "string",
                    "enum": ["file", "dir", "any"],
                    "description": "Filter by type. Default 'any'.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results to return. Default 30.",
                },
            },
            "required": ["pattern"],
        },
    },
}

BOOKMARK_DEFINITION = {
    "type": "function",
    "function": {
        "name": "nav_bookmark",
        "description": "Manage directory bookmarks. Save current or specified directory as a named bookmark, list all bookmarks, or go to a bookmark.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["save", "list", "go", "delete"],
                    "description": "Action to perform.",
                },
                "name": {
                    "type": "string",
                    "description": "Bookmark name.",
                },
                "path": {
                    "type": "string",
                    "description": "Path to bookmark (for save action). Defaults to current directory.",
                },
            },
            "required": ["action"],
        },
    },
}

HISTORY_DEFINITION = {
    "type": "function",
    "function": {
        "name": "nav_history",
        "description": "Show the navigation history of recently visited directories.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}

DISK_USAGE_DEFINITION = {
    "type": "function",
    "function": {
        "name": "nav_disk_usage",
        "description": "Show disk usage of a directory and its contents.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to check. Defaults to current directory.",
                },
                "depth": {
                    "type": "integer",
                    "description": "Depth of subdirectory summary. Default 1.",
                },
            },
            "required": [],
        },
    },
}

ALL_DEFINITIONS = [
    CD_DEFINITION,
    PWD_DEFINITION,
    LS_DEFINITION,
    TREE_DEFINITION,
    FIND_DEFINITION,
    BOOKMARK_DEFINITION,
    HISTORY_DEFINITION,
    DISK_USAGE_DEFINITION,
]

IGNORED_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".cache"}


# ── Implementations ───────────────────────────────────────────────────────────

def cd(path: str) -> str:
    state = _load_state()
    cwd = state["cwd"]

    # Resolve bookmark names
    if path in state["bookmarks"]:
        path = state["bookmarks"][path]

    # Expand ~ and resolve relative paths
    if path == "~":
        new_path = str(Path.home())
    elif path.startswith("~/"):
        new_path = str(Path.home() / path[2:])
    elif path.startswith("/"):
        new_path = path
    else:
        new_path = str(Path(cwd) / path)

    # Normalize
    try:
        new_path = str(Path(new_path).resolve())
    except Exception:
        pass

    if not os.path.isdir(new_path):
        return f"Error: directory not found: {new_path}"

    # Update history
    history = state.get("history", [])
    if cwd not in history or history[-1] != cwd:
        history.append(cwd)
    history = history[-20:]  # keep last 20

    state["cwd"] = new_path
    state["history"] = history
    _save_state(state)

    # Also change the actual process cwd
    try:
        os.chdir(new_path)
    except Exception:
        pass

    return f"📁 {new_path}"


def pwd() -> str:
    cwd = get_cwd()
    # Sync actual process cwd
    try:
        os.chdir(cwd)
    except Exception:
        pass
    return cwd


def ls(path: str = "", show_hidden: bool = False) -> str:
    cwd = get_cwd()
    target = path if path else cwd

    # Expand ~ 
    if target.startswith("~"):
        target = str(Path.home() / target[2:]) if target.startswith("~/") else str(Path.home())

    try:
        entries = sorted(os.scandir(target), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        return f"Error: permission denied: {target}"
    except FileNotFoundError:
        return f"Error: not found: {target}"

    lines = [f"📁 {target}/\n"]
    dirs_count = files_count = 0

    for e in entries:
        if not show_hidden and e.name.startswith("."):
            continue
        try:
            stat = e.stat()
            size = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        except Exception:
            size, mtime = 0, "?"

        if e.is_dir():
            lines.append(f"  📁 {e.name}/  [{mtime}]")
            dirs_count += 1
        else:
            size_str = (
                f"{size} B" if size < 1024
                else f"{size/1024:.1f} KB" if size < 1024**2
                else f"{size/1024**2:.1f} MB"
            )
            lines.append(f"  📄 {e.name}  {size_str}  [{mtime}]")
            files_count += 1

    lines.append(f"\n  {dirs_count} dirs, {files_count} files")
    return "\n".join(lines)


def tree(path: str = "", depth: int = 3) -> str:
    cwd = get_cwd()
    root = Path(path if path else cwd)

    if not root.exists():
        return f"Error: path not found: {root}"

    lines = [str(root)]

    def _walk(p: Path, prefix: str, current_depth: int):
        if current_depth > depth:
            return
        try:
            entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return

        entries = [e for e in entries if e.name not in IGNORED_DIRS and not e.name.startswith(".")]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            icon = "📁" if entry.is_dir() else "📄"
            lines.append(f"{prefix}{connector}{icon} {entry.name}")
            if entry.is_dir() and current_depth < depth:
                extension = "    " if is_last else "│   "
                _walk(entry, prefix + extension, current_depth + 1)

    _walk(root, "", 1)

    if len(lines) > 100:
        lines = lines[:100]
        lines.append("  ... (truncated)")

    return "\n".join(lines)


def find(pattern: str, path: str = "", type_filter: str = "any", max_results: int = 30) -> str:
    cwd = get_cwd()
    root = path if path else cwd

    matches = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip ignored dirs
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]

        if type_filter in ("any", "dir"):
            for d in dirnames:
                if fnmatch.fnmatch(d, pattern):
                    matches.append(f"  📁 {os.path.join(dirpath, d)}")

        if type_filter in ("any", "file"):
            for f in filenames:
                if fnmatch.fnmatch(f, pattern):
                    matches.append(f"  📄 {os.path.join(dirpath, f)}")

        if len(matches) >= max_results:
            break

    if not matches:
        return f"No matches found for '{pattern}' in {root}"

    result = f"Found {len(matches)} match(es) for '{pattern}':\n"
    result += "\n".join(matches[:max_results])
    if len(matches) >= max_results:
        result += f"\n  ... (showing first {max_results})"
    return result


def bookmark(action: str, name: str = "", path: str = "") -> str:
    state = _load_state()
    cwd = state["cwd"]

    if action == "list":
        if not state["bookmarks"]:
            return "No bookmarks saved."
        lines = ["Bookmarks:"]
        for k, v in state["bookmarks"].items():
            lines.append(f"  ⭐ {k}  →  {v}")
        return "\n".join(lines)

    elif action == "save":
        if not name:
            return "Error: provide a bookmark name, e.g. nav_bookmark save myproject"
        target = path if path else cwd
        state["bookmarks"][name] = target
        _save_state(state)
        return f"⭐ Bookmarked '{name}' → {target}"

    elif action == "go":
        if not name:
            return "Error: provide a bookmark name."
        if name not in state["bookmarks"]:
            return f"No bookmark named '{name}'. Use nav_bookmark list to see all."
        return cd(state["bookmarks"][name])

    elif action == "delete":
        if name not in state["bookmarks"]:
            return f"No bookmark named '{name}'."
        del state["bookmarks"][name]
        _save_state(state)
        return f"Deleted bookmark '{name}'"

    return f"Unknown action: {action}"


def history() -> str:
    state = _load_state()
    hist = state.get("history", [])
    if not hist:
        return "No navigation history yet."
    lines = ["Recent directories:"]
    for i, p in enumerate(reversed(hist[-15:]), 1):
        lines.append(f"  {i}. {p}")
    return "\n".join(lines)


def disk_usage(path: str = "", depth: int = 1) -> str:
    cwd = get_cwd()
    target = path if path else cwd

    try:
        result = subprocess.run(
            f"du -sh {target}/* 2>/dev/null | sort -rh | head -20",
            shell=True, capture_output=True, text=True, timeout=15,
        )
        out = result.stdout.strip()
        if not out:
            # Fallback
            st = os.statvfs(target)
            total = st.f_frsize * st.f_blocks
            free = st.f_frsize * st.f_bavail
            used = total - free
            return (
                f"Disk usage for {target}:\n"
                f"  Total: {total//1024//1024} MB\n"
                f"  Used:  {used//1024//1024} MB\n"
                f"  Free:  {free//1024//1024} MB"
            )
        return f"Disk usage in {target}:\n" + "\n".join(f"  {line}" for line in out.splitlines())
    except Exception as e:
        return f"Error: {e}"
