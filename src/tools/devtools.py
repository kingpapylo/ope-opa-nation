"""
Developer tools — git integration, script runner, test generator.
"""

import subprocess
import os
import tempfile
from pathlib import Path


# ── Git tools ────────────────────────────────────────────────────────────────

GIT_DEFINITION = {
    "type": "function",
    "function": {
        "name": "git_run",
        "description": (
            "Run a git command in a repository directory. "
            "Use for status, diff, add, commit, push, pull, log, branch, etc."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Git subcommand and args, e.g. 'status', 'log --oneline -10', 'diff HEAD'.",
                },
                "repo_path": {
                    "type": "string",
                    "description": "Path to the git repo. Defaults to current directory.",
                },
            },
            "required": ["command"],
        },
    },
}


def git_run(command: str, repo_path: str = ".") -> str:
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            f"git {command}",
            shell=True,
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=30,
        )
        out = (result.stdout + result.stderr).strip()
        return out if out else f"(exit code {result.returncode})"
    except subprocess.TimeoutExpired:
        return "Error: git command timed out."
    except Exception as e:
        return f"Error: {e}"


# ── Script runner ─────────────────────────────────────────────────────────────

SCRIPT_RUN_DEFINITION = {
    "type": "function",
    "function": {
        "name": "script_run",
        "description": (
            "Write a script to a temp file and execute it. "
            "Supports Python, Bash, Node.js, Ruby. "
            "Returns stdout + stderr."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "enum": ["python", "bash", "node", "ruby"],
                    "description": "Script language.",
                },
                "code": {
                    "type": "string",
                    "description": "The script code to run.",
                },
            },
            "required": ["language", "code"],
        },
    },
}

RUNNERS = {
    "python": ("python3", ".py"),
    "bash":   ("bash",    ".sh"),
    "node":   ("node",    ".js"),
    "ruby":   ("ruby",    ".rb"),
}


def script_run(language: str, code: str) -> str:
    """Write code to a temp file and execute it."""
    runner_cmd, ext = RUNNERS.get(language, ("python3", ".py"))

    # Check interpreter is available
    result = subprocess.run(f"command -v {runner_cmd}", shell=True, capture_output=True)
    if result.returncode != 0:
        return f"Error: '{runner_cmd}' is not installed."

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False) as f:
            f.write(code)
            tmp_path = f.name

        result = subprocess.run(
            f"{runner_cmd} {tmp_path}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        out = (result.stdout + result.stderr).strip()
        return out if out else f"(exit code {result.returncode}, no output)"
    except subprocess.TimeoutExpired:
        return "Error: script timed out after 30 seconds."
    except Exception as e:
        return f"Error running script: {e}"
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ── Test generator ────────────────────────────────────────────────────────────

TEST_GEN_DEFINITION = {
    "type": "function",
    "function": {
        "name": "test_generate",
        "description": (
            "Read a Python source file and generate a pytest test file for it. "
            "Saves the test file next to the source file."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "source_path": {
                    "type": "string",
                    "description": "Path to the Python source file to generate tests for.",
                },
            },
            "required": ["source_path"],
        },
    },
}


def test_generate(source_path: str) -> str:
    """
    Read a Python file, extract function/class names, and generate a
    pytest stub file. The AI agent will fill in the actual test logic
    by reading the source and calling this tool.
    """
    try:
        src = Path(source_path)
        if not src.exists():
            return f"Error: file not found: {source_path}"

        code = src.read_text(encoding="utf-8")

        # Extract top-level def and class names with simple regex
        import re
        functions = re.findall(r"^def (\w+)\s*\(", code, re.MULTILINE)
        classes   = re.findall(r"^class (\w+)\s*[\(:]", code, re.MULTILINE)

        module_name = src.stem
        lines = [
            f'"""Auto-generated tests for {src.name}"""',
            "import pytest",
            f"from {module_name} import " + (", ".join(functions[:10] + classes[:5]) or "*"),
            "",
        ]

        for fn in functions:
            if fn.startswith("_"):
                continue
            lines += [
                f"",
                f"def test_{fn}():",
                f'    """Test {fn}"""',
                f"    # TODO: implement test",
                f"    pass",
            ]

        for cls in classes:
            lines += [
                f"",
                f"class Test{cls}:",
                f'    """Tests for {cls}"""',
                f"",
                f"    def test_init(self):",
                f'        """Test {cls} initialization"""',
                f"        # TODO: implement test",
                f"        pass",
            ]

        test_content = "\n".join(lines) + "\n"
        test_path = src.parent / f"test_{src.name}"
        test_path.write_text(test_content, encoding="utf-8")

        return (
            f"Generated test file: {test_path}\n"
            f"Functions covered: {', '.join(functions) or 'none'}\n"
            f"Classes covered: {', '.join(classes) or 'none'}"
        )
    except Exception as e:
        return f"Error generating tests: {e}"
