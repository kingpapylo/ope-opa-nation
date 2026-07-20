"""Core agent loop — handles model calls and tool execution."""

import json
from typing import Callable

from openai import OpenAI

from .config import load_config, get_api_key
from .tools import shell, files, search, codesearch

# All available tool definitions
TOOL_DEFINITIONS = [
    shell.DEFINITION,
    files.READ_DEFINITION,
    files.WRITE_DEFINITION,
    files.LIST_DEFINITION,
    search.DEFINITION,
    codesearch.DEFINITION,
]


def dispatch_tool(name: str, args: dict) -> str:
    """Route a tool call to the correct implementation."""
    if name == "run_shell":
        return shell.run(args["command"], args.get("working_dir"))

    elif name == "read_file":
        return files.read_file(
            args["path"],
            args.get("start_line"),
            args.get("end_line"),
        )

    elif name == "write_file":
        return files.write_file(args["path"], args["content"])

    elif name == "list_directory":
        return files.list_directory(args.get("path", "."))

    elif name == "web_search":
        return search.search(args["query"], args.get("max_results", 5))

    elif name == "search_code":
        return codesearch.search(
            args["pattern"],
            args.get("path", "."),
            args.get("file_pattern"),
            args.get("case_sensitive", False),
            args.get("max_results", 50),
        )

    else:
        return f"Unknown tool: {name}"


class Agent:
    """
    Stateful AI agent with tool-use loop.

    Usage:
        agent = Agent()
        reply = agent.chat("List files in the current directory")
    """

    def __init__(self, on_tool_call: Callable[[str, dict], None] | None = None):
        """
        Args:
            on_tool_call: Optional callback invoked before each tool executes.
                          Receives (tool_name, tool_args).
        """
        self.config = load_config()
        self.on_tool_call = on_tool_call

        api_key = get_api_key(self.config["provider"])
        if not api_key:
            raise ValueError(
                f"No API key found for provider '{self.config['provider']}'. "
                "Set OPENAI_API_KEY (or ANTHROPIC_API_KEY) in your environment, "
                "or run: cli-agent config set-key <your-key>"
            )

        self.client = OpenAI(api_key=api_key)
        self.messages: list[dict] = [
            {"role": "system", "content": self.config["system_prompt"]}
        ]

    def chat(self, user_message: str) -> str:
        """Send a user message and return the agent's final response."""
        self.messages.append({"role": "user", "content": user_message})
        return self._run_loop()

    def _run_loop(self) -> str:
        """Run the model + tool loop until the model stops calling tools."""
        while True:
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=self.messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                max_tokens=self.config["max_tokens"],
            )

            msg = response.choices[0].message

            # Append assistant message (may include tool_calls)
            self.messages.append(msg)

            # No tool calls → final text response
            if not msg.tool_calls:
                return msg.content or ""

            # Execute each tool call and collect results
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    tool_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                # Notify caller (used by CLI to show progress)
                if self.on_tool_call:
                    self.on_tool_call(tool_name, tool_args)

                result = dispatch_tool(tool_name, tool_args)

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

    def reset(self) -> None:
        """Clear conversation history (keeps system prompt)."""
        self.messages = [self.messages[0]]
