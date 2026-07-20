"""File read and write tools."""

import os
from pathlib import Path


READ_DEFINITION = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a file. Returns the file content as a string.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read.",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Optional 1-indexed line to start reading from.",
                },
                "end_line": {
                    "type": "integer",
                    "description": "Optional 1-indexed line to stop reading at (inclusive).",
                },
            },
            "required": ["path"],
        },
    },
}

WRITE_DEFINITION = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write or overwrite a file with the given content. Creates parent directories if needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write.",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file.",
                },
            },
            "required": ["path", "content"],
        },
    },
}

LIST_DEFINITION = {
    "type": "function",
    "function": {
        "name": "list_directory",
        "description": "List files and directories at a given path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list. Defaults to current directory.",
                },
            },
            "required": [],
        },
    },
}


def read_file(path: str, start_line: int | None = None, end_line: int | None = None) -> str:
    """Read file contents, optionally slicing by line range."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        if start_line is not None or end_line is not None:
            start = (start_line - 1) if start_line else 0
            end = end_line if end_line else len(lines)
            lines = lines[start:end]

        return "".join(lines)
    except FileNotFoundError:
        return f"Error: file not found: {path}"
    except IsADirectoryError:
        return f"Error: {path} is a directory, not a file."
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent dirs if needed."""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        lines = content.count("\n") + 1
        return f"Written {lines} lines to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


def list_directory(path: str = ".") -> str:
    """List directory contents."""
    try:
        entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
        lines = []
        for entry in entries:
            if entry.is_dir():
                lines.append(f"  📁 {entry.name}/")
            else:
                size = entry.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size / 1024:.1f} KB"
                lines.append(f"  📄 {entry.name}  ({size_str})")
        return f"{path}:\n" + "\n".join(lines) if lines else f"{path}: (empty)"
    except FileNotFoundError:
        return f"Error: directory not found: {path}"
    except Exception as e:
        return f"Error listing directory: {e}"
