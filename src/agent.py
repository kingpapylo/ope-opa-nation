"""Core agent loop — handles model calls and tool execution."""

import json
from typing import Callable

from openai import OpenAI

from .config import load_config, get_api_key
from .tools import shell, files, search, codesearch
from .tools import memory, phone, devtools, webtools, utils

# ── All tool definitions ──────────────────────────────────────────────────────
TOOL_DEFINITIONS = [
    # File & shell
    shell.DEFINITION,
    files.READ_DEFINITION,
    files.WRITE_DEFINITION,
    files.LIST_DEFINITION,
    # Search
    search.DEFINITION,
    codesearch.DEFINITION,
    # Memory
    memory.SAVE_DEFINITION,
    memory.RECALL_DEFINITION,
    memory.FORGET_DEFINITION,
    # Phone (Termux)
    *phone.ALL_DEFINITIONS,
    # Developer tools
    devtools.GIT_DEFINITION,
    devtools.SCRIPT_RUN_DEFINITION,
    devtools.TEST_GEN_DEFINITION,
    # Web & API
    *webtools.ALL_DEFINITIONS,
    # Utilities
    *utils.ALL_DEFINITIONS,
]


def dispatch_tool(name: str, args: dict) -> str:
    """Route a tool call by name to its implementation."""

    # ── File & shell ──────────────────────────────────────────────────────────
    if name == "run_shell":
        return shell.run(args["command"], args.get("working_dir"))
    elif name == "read_file":
        return files.read_file(args["path"], args.get("start_line"), args.get("end_line"))
    elif name == "write_file":
        return files.write_file(args["path"], args["content"])
    elif name == "list_directory":
        return files.list_directory(args.get("path", "."))

    # ── Search ────────────────────────────────────────────────────────────────
    elif name == "web_search":
        return search.search(args["query"], args.get("max_results", 5))
    elif name == "search_code":
        return codesearch.search(
            args["pattern"], args.get("path", "."),
            args.get("file_pattern"), args.get("case_sensitive", False),
            args.get("max_results", 50),
        )

    # ── Memory ────────────────────────────────────────────────────────────────
    elif name == "memory_save":
        return memory.save(args["key"], args["value"])
    elif name == "memory_recall":
        return memory.recall(args.get("key", ""))
    elif name == "memory_forget":
        return memory.forget(args["key"])

    # ── Phone ─────────────────────────────────────────────────────────────────
    elif name == "phone_sms_send":
        return phone.sms_send(args["number"], args["message"])
    elif name == "phone_sms_list":
        return phone.sms_list(args.get("limit", 10))
    elif name == "phone_battery":
        return phone.battery()
    elif name == "phone_camera":
        return phone.camera(args["output_path"], args.get("camera_id", "0"))
    elif name == "phone_contacts":
        return phone.contacts()
    elif name == "phone_notify":
        return phone.notify(args["title"], args["message"])
    elif name == "phone_location":
        return phone.location(args.get("provider", "network"))

    # ── Developer tools ───────────────────────────────────────────────────────
    elif name == "git_run":
        return devtools.git_run(args["command"], args.get("repo_path", "."))
    elif name == "script_run":
        return devtools.script_run(args["language"], args["code"])
    elif name == "test_generate":
        return devtools.test_generate(args["source_path"])

    # ── Web & API ─────────────────────────────────────────────────────────────
    elif name == "web_fetch":
        return webtools.web_fetch(args["url"], args.get("max_chars", 3000))
    elif name == "weather":
        return webtools.weather(args["location"])
    elif name == "wikipedia":
        return webtools.wikipedia(args["query"])
    elif name == "send_email":
        return webtools.send_email(args["to"], args["subject"], args["body"])
    elif name == "download_file":
        return webtools.download_file(args["url"], args["output_path"])

    # ── Utilities ─────────────────────────────────────────────────────────────
    elif name == "generate_password":
        return utils.generate_password(
            args.get("length", 20),
            args.get("include_symbols", True),
            args.get("count", 1),
        )
    elif name == "encrypt_file":
        return utils.encrypt_file(args["file_path"], args["password"])
    elif name == "decrypt_file":
        return utils.decrypt_file(args["file_path"], args["password"], args.get("output_path"))
    elif name == "system_monitor":
        return utils.system_monitor(args.get("detail", "all"))

    else:
        return f"Unknown tool: {name}"


class Agent:
    """
    Stateful AI agent with tool-use loop.

    Usage:
        agent = Agent()
        reply = agent.chat("What is my battery level?")
    """

    def __init__(self, on_tool_call: Callable[[str, dict], None] | None = None):
        self.config = load_config()
        self.on_tool_call = on_tool_call

        api_key = get_api_key(self.config["provider"])
        if not api_key:
            raise ValueError(
                f"No API key found for provider '{self.config['provider']}'. "
                "Set OPENAI_API_KEY in your environment, "
                "or run: ope-opa-nation config set-key <your-key>"
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1" if self.config["provider"] == "groq" else None,
        )

        # Inject saved memories into the system prompt
        saved = memory.load_all()
        mem_block = ""
        if saved:
            lines = "\n".join(f"  - {k}: {v['value']}" for k, v in saved.items())
            mem_block = f"\n\nThings you remember about the user:\n{lines}"

        self.messages: list[dict] = [
            {"role": "system", "content": self.config["system_prompt"] + mem_block}
        ]

    def chat(self, user_message: str) -> str:
        """Send a user message and return the agent's final text response."""
        self.messages.append({"role": "user", "content": user_message})
        return self._run_loop()

    def _run_loop(self) -> str:
        """Run the model + tool execution loop until the model returns text."""
        while True:
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=self.messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                max_tokens=self.config["max_tokens"],
            )

            msg = response.choices[0].message
            self.messages.append(msg)

            if not msg.tool_calls:
                return msg.content or ""

            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    tool_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

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

    def get_history(self) -> list[dict]:
        """Return conversation history (excluding system prompt)."""
        return [m for m in self.messages if isinstance(m, dict) and m.get("role") != "system"]
