"""Shell command execution tool."""

import subprocess
import shlex


DEFINITION = {
    "type": "function",
    "function": {
        "name": "run_shell",
        "description": (
            "Run a shell command and return stdout + stderr. "
            "Use for file system operations, git, package managers, running scripts, etc."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute.",
                },
                "working_dir": {
                    "type": "string",
                    "description": "Optional working directory to run the command in.",
                },
            },
            "required": ["command"],
        },
    },
}


def run(command: str, working_dir: str | None = None) -> str:
    """Execute a shell command and return its output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=working_dir,
            timeout=60,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += result.stderr
        if not output:
            output = f"(exit code {result.returncode})"
        return output.strip()
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 60 seconds."
    except Exception as e:
        return f"Error running command: {e}"
