"""Core agent loop — handles model calls and tool execution."""

import json
from typing import Callable

from openai import OpenAI

from .config import load_config, get_api_key
from .tools import shell, files, search, codesearch
from .tools import memory, phone, devtools, webtools, utils
from .tools import android, navigator

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
    # Android UI navigation
    *android.ALL_DEFINITIONS,
    # Terminal/filesystem navigation
    *navigator.ALL_DEFINITIONS,
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

    # ── Android UI navigation ─────────────────────────────────────────────────
    elif name == "android_open_app":
        return android.open_app(args["app"])
    elif name == "android_tap":
        return android.tap(args["x"], args["y"])
    elif name == "android_long_press":
        return android.long_press(args["x"], args["y"], args.get("duration_ms", 1000))
    elif name == "android_swipe":
        return android.swipe(args["x1"], args["y1"], args["x2"], args["y2"], args.get("duration_ms", 300))
    elif name == "android_key":
        return android.key(args["key"])
    elif name == "android_screenshot":
        return android.screenshot(args.get("output_path", "/sdcard/screenshot.png"))
    elif name == "android_clipboard_read":
        return android.clipboard_read()
    elif name == "android_clipboard_write":
        return android.clipboard_write(args["text"])
    elif name == "android_type_text":
        return android.type_text(args["text"])
    elif name == "android_screen_info":
        return android.screen_info()
    elif name == "android_torch":
        return android.torch(args["on"])
    elif name == "android_vibrate":
        return android.vibrate(args.get("duration_ms", 500))
    elif name == "android_speak":
        return android.speak(args["text"], args.get("rate", 1.0))
    elif name == "android_list_apps":
        return android.list_apps(args.get("filter", ""))

    # ── Terminal/filesystem navigation ────────────────────────────────────────
    elif name == "nav_cd":
        return navigator.cd(args["path"])
    elif name == "nav_pwd":
        return navigator.pwd()
    elif name == "nav_ls":
        return navigator.ls(args.get("path", ""), args.get("show_hidden", False))
    elif name == "nav_tree":
        return navigator.tree(args.get("path", ""), args.get("depth", 3))
    elif name == "nav_find":
        return navigator.find(
            args["pattern"], args.get("path", ""),
            args.get("type", "any"), args.get("max_results", 30),
        )
    elif name == "nav_bookmark":
        return navigator.bookmark(args["action"], args.get("name", ""), args.get("path", ""))
    elif name == "nav_history":
        return navigator.history()
    elif name == "nav_disk_usage":
        return navigator.disk_usage(args.get("path", ""), args.get("depth", 1))

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


# ── Provider registry ────────────────────────────────────────────────────────
# Each entry: base_url, default_model, env_var, signup_url
PROVIDERS = {
    "groq": {
        "base_url":      "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "env_var":       "GROQ_API_KEY",
        "signup_url":    "https://console.groq.com/keys",
        "label":         "Groq (FREE ⚡ fast)",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ],
    },
    "openai": {
        "base_url":      None,
        "default_model": "gpt-4o",
        "env_var":       "OPENAI_API_KEY",
        "signup_url":    "https://platform.openai.com/api-keys",
        "label":         "OpenAI (GPT-4o)",
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ],
    },
    "anthropic": {
        "base_url":      "https://api.anthropic.com/v1",
        "default_model": "claude-3-5-sonnet-20241022",
        "env_var":       "ANTHROPIC_API_KEY",
        "signup_url":    "https://console.anthropic.com/",
        "label":         "Anthropic (Claude)",
        "models": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
        ],
    },
    "together": {
        "base_url":      "https://api.together.xyz/v1",
        "default_model": "meta-llama/Llama-3-70b-chat-hf",
        "env_var":       "TOGETHER_API_KEY",
        "signup_url":    "https://api.together.ai/",
        "label":         "Together AI (FREE trial)",
        "models": [
            "meta-llama/Llama-3-70b-chat-hf",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "google/gemma-2-27b-it",
        ],
    },
    "openrouter": {
        "base_url":      "https://openrouter.ai/api/v1",
        "default_model": "mistralai/mistral-7b-instruct:free",
        "env_var":       "OPENROUTER_API_KEY",
        "signup_url":    "https://openrouter.ai/keys",
        "label":         "OpenRouter (FREE models available)",
        "models": [
            "mistralai/mistral-7b-instruct:free",
            "google/gemma-2-9b-it:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "microsoft/phi-3-mini-128k-instruct:free",
            "qwen/qwen-2-7b-instruct:free",
        ],
    },
    "ollama": {
        "base_url":      "http://localhost:11434/v1",
        "default_model": "llama3",
        "env_var":       None,
        "signup_url":    "https://ollama.com",
        "label":         "Ollama (LOCAL — runs on your device)",
        "models": [
            "llama3",
            "mistral",
            "phi3",
            "gemma2",
            "codellama",
        ],
    },
}


def get_provider_info(provider: str) -> dict:
    return PROVIDERS.get(provider, PROVIDERS["groq"])


class Agent:
    """
    Stateful AI agent with tool-use loop.
    Supports: Groq, OpenAI, Anthropic, Together, OpenRouter, Ollama.
    """

    def __init__(self, on_tool_call: Callable[[str, dict], None] | None = None):
        self.config = load_config()
        self.on_tool_call = on_tool_call
        provider = self.config["provider"]
        info = get_provider_info(provider)

        # Ollama doesn't need an API key
        if info["env_var"] is None:
            api_key = "ollama"
        else:
            api_key = get_api_key(provider)
            if not api_key:
                raise ValueError(
                    f"No API key found for provider '{provider}'.\n"
                    f"Get a free key at: {info['signup_url']}\n"
                    f"Then run: ope-opa-nation config set-key <your-key> --provider {provider}"
                )

        self.client = OpenAI(
            api_key=api_key,
            base_url=info["base_url"],
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
