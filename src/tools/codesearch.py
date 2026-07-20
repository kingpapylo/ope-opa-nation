"""Code search tool — grep-based text and pattern search across files."""

import os
import re
import fnmatch
from pathlib import Path


DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_code",
        "description": (
            "Search for a text pattern or regex across files in a directory. "
            "Returns matching lines with file paths and line numbers."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Text or regex pattern to search for.",
                },
                "path": {
                    "type": "string",
                    "description": "Directory or file to search in. Defaults to current directory.",
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Glob pattern to filter files, e.g. '*.py', '*.ts'. Defaults to all files.",
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Whether search is case-sensitive. Defaults to false.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of matching lines to return. Defaults to 50.",
                },
            },
            "required": ["pattern"],
        },
    },
}

IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".cache", "target", ".mypy_cache", ".pytest_cache",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".pdf",
    ".zip", ".tar", ".gz", ".bin", ".exe", ".dll", ".so",
    ".pyc", ".pyo", ".whl",
}


def search(
    pattern: str,
    path: str = ".",
    file_pattern: str | None = None,
    case_sensitive: bool = False,
    max_results: int = 50,
) -> str:
    """Search for a pattern across files."""
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"Invalid regex pattern: {e}"

    search_path = Path(path)
    if not search_path.exists():
        return f"Error: path not found: {path}"

    results = []
    files_searched = 0

    if search_path.is_file():
        file_list = [search_path]
    else:
        file_list = _walk_files(search_path, file_pattern)

    for filepath in file_list:
        if len(results) >= max_results:
            break
        matches = _search_file(filepath, regex, max_results - len(results))
        if matches:
            results.extend(matches)
        files_searched += 1

    if not results:
        return f"No matches found for '{pattern}' in {path}"

    header = f"Found {len(results)} match(es) across {files_searched} file(s):\n"
    return header + "\n".join(results)


def _walk_files(root: Path, file_pattern: str | None):
    """Walk directory recursively, yielding files to search."""
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip ignored directories in-place
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        for filename in sorted(filenames):
            if Path(filename).suffix.lower() in BINARY_EXTENSIONS:
                continue
            if file_pattern and not fnmatch.fnmatch(filename, file_pattern):
                continue
            yield Path(dirpath) / filename


def _search_file(filepath: Path, regex: re.Pattern, limit: int) -> list[str]:
    """Search a single file for pattern matches."""
    matches = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for lineno, line in enumerate(f, 1):
                if regex.search(line):
                    clean = line.rstrip()
                    matches.append(f"  {filepath}:{lineno}: {clean}")
                    if len(matches) >= limit:
                        break
    except OSError:
        pass
    return matches
