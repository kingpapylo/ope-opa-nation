# OPE-OPA-NATION 🌈

```
  ██████╗ ██████╗ ███████╗      ██████╗ ██████╗  █████╗
  ██╔══██╗██╔══██╗██╔════╝     ██╔═══██╗██╔══██╗██╔══██╗
  ██║  ██║██████╔╝█████╗       ██║   ██║██████╔╝███████║
  ██║  ██║██╔═══╝ ██╔══╝       ██║   ██║██╔═══╝ ██╔══██║
  ██████╔╝██║     ███████╗     ╚██████╔╝██║     ██║  ██║
  ╚═════╝ ╚═╝     ╚══════╝      ╚═════╝ ╚═╝     ╚═╝  ╚═╝

  ███╗  ██╗ █████╗ ████████╗██╗ ██████╗ ███╗  ██╗
  ████╗ ██║██╔══██╗╚══██╔══╝██║██╔═══██╗████╗ ██║
  ██╔██╗██║███████║   ██║   ██║██║   ██║██╔██╗██║
  ██║╚████║██╔══██║   ██║   ██║██║   ██║██║╚████║
  ██║ ╚███║██║  ██║   ██║   ██║╚██████╔╝██║ ╚███║
  ╚═╝  ╚══╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚══╝

  ✦  Rainbow AI-Powered Terminal Assistant  ✦
```

Your AI agent — runs on **Android (Termux)** and **Linux**.  
Chat naturally, run shell commands, read/write files, search the web, search your code.

---

## One-Line Install

### Android — Termux

Open Termux and paste:

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/ope-opa-nation/main/install.sh | bash
```

> If you haven't pushed to GitHub yet, copy the project folder to your phone and run:
> ```bash
> bash /sdcard/OPE-OPA-NATION/install.sh
> ```

### Linux

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/ope-opa-nation/main/install.sh | bash
```

Or if you already have the files:

```bash
bash install.sh
```

---

## What the installer does

| Step | Termux (Android) | Linux |
|------|-----------------|-------|
| Install system deps | `pkg install python git curl` | `apt / dnf / pacman` |
| Install Python packages | pip directly (no venv needed) | venv in `~/.local/share/ope-opa-nation/.venv` |
| Project location | `~/ope-opa-nation` | `~/.local/share/ope-opa-nation` |
| **Phone storage copy** | `/sdcard/OPE-OPA-NATION` ✅ | N/A |
| Command installed | `ope-opa-nation` + `oon` | `ope-opa-nation` + `oon` |

On Termux the project is **also saved to `/sdcard/OPE-OPA-NATION`** — visible in your Android Files app.

---

## Setup: API Key

After installing, set your OpenAI API key:

```bash
# Option A — environment variable (recommended)
export OPENAI_API_KEY="sk-..."
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc

# Option B — save to config file
ope-opa-nation config set-key sk-...
```

---

## Usage

### Interactive chat

```bash
ope-opa-nation
# or short alias:
oon
```

```
★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★

  [rainbow OPE-OPA-NATION banner]

★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★  ★

🧑 You: list all files in this folder
  📁 Listing directory: .
─── OPE-OPA-NATION ───
Here are the files: ...
```

### One-shot mode

```bash
ope-opa-nation run "what is my public IP?"
ope-opa-nation run "read README.md and summarize it"
ope-opa-nation run "write a hello world to /tmp/hello.py and run it"
```

### Config commands

```bash
ope-opa-nation config show           # show current config
ope-opa-nation config set-key sk-... # save API key
ope-opa-nation config set-model gpt-4-turbo
```

---

## Slash commands (in chat)

| Command | Description |
|---------|-------------|
| `/help` | Show help panel |
| `/clear` | Clear conversation history |
| `/model <name>` | Switch model (e.g. `gpt-4o`, `gpt-4-turbo`) |
| `/quit` | Exit |

---

## Available tools

| Tool | What it does |
|------|-------------|
| `run_shell` | Run any shell command |
| `read_file` | Read a file (optionally a line range) |
| `write_file` | Write or overwrite a file |
| `list_directory` | List directory contents |
| `web_search` | Search DuckDuckGo (no API key needed) |
| `search_code` | Regex search across files in a directory |

---

## File locations

| What | Termux | Linux |
|------|--------|-------|
| App files | `~/ope-opa-nation/` | `~/.local/share/ope-opa-nation/` |
| Phone storage copy | `/sdcard/OPE-OPA-NATION/` | — |
| Config + API key | `~/.ope-opa-nation/config.json` | `~/.ope-opa-nation/config.json` |
| Command | `$PREFIX/bin/ope-opa-nation` | `~/.local/bin/ope-opa-nation` |

---

## Project structure

```
ope-opa-nation/
├── src/
│   ├── agent.py        # Core agent loop + tool dispatch
│   ├── cli.py          # Rainbow CLI interface
│   ├── config.py       # Config, API key, Termux/Linux detection
│   └── tools/
│       ├── shell.py        # Shell command tool
│       ├── files.py        # File read/write/list tools
│       ├── search.py       # Web search (DuckDuckGo)
│       └── codesearch.py   # Code/text grep search
├── install.sh          # Smart cross-platform installer
├── pyproject.toml
└── README.md
```

---

## Termux first-time setup (if needed)

If you've never used Termux before:

```bash
# 1. Update packages
pkg update && pkg upgrade

# 2. Install basics
pkg install python git curl

# 3. Grant storage permission (needed to save to /sdcard)
termux-setup-storage

# 4. Run the installer
bash install.sh
```

---

## Extending with new tools

1. Create `src/tools/mytool.py` with a `DEFINITION` dict (OpenAI function schema) and an implementation function.
2. In `src/agent.py`, add `DEFINITION` to `TOOL_DEFINITIONS` and add a case in `dispatch_tool()`.

The agent loop handles the rest automatically.
