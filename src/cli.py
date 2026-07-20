"""Rich CLI interface for OPE-OPA-NATION AI agent."""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import NoReturn

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.table import Table
from rich import print as rprint

from .agent import Agent
from .config import load_config, save_config, set_api_key, get_api_key
from .tools import memory as mem_tool

console = Console(force_terminal=True, force_interactive=True)

# History saved to ~/.ope-opa-nation/history/
HISTORY_DIR = Path.home() / ".ope-opa-nation" / "history"

# Rainbow color cycle for text
RAINBOW = ["red", "yellow", "green", "cyan", "blue", "magenta"]


def rainbow_text(text: str) -> Text:
    """Return a Rich Text object with each character in a cycling rainbow color."""
    rich_text = Text()
    color_idx = 0
    for ch in text:
        if ch != " ":
            rich_text.append(ch, style=f"bold {RAINBOW[color_idx % len(RAINBOW)]}")
            color_idx += 1
        else:
            rich_text.append(ch)
    return rich_text


def print_banner() -> None:
    """Print the OPE-OPA-NATION rainbow banner."""
    # Clean compact ASCII art
    ascii_art = [
        "  ██████╗ ██████╗ ███████╗      ██████╗ ██████╗  █████╗     ",
        "  ██╔══██╗██╔══██╗██╔════╝     ██╔═══██╗██╔══██╗██╔══██╗    ",
        "  ██║  ██║██████╔╝█████╗       ██║   ██║██████╔╝███████║    ",
        "  ██║  ██║██╔═══╝ ██╔══╝       ██║   ██║██╔═══╝ ██╔══██║    ",
        "  ██████╔╝██║     ███████╗     ╚██████╔╝██║     ██║  ██║    ",
        "  ╚═════╝ ╚═╝     ╚══════╝      ╚═════╝ ╚═╝     ╚═╝  ╚═╝    ",
        "",
        "  ███╗  ██╗ █████╗ ████████╗██╗ ██████╗ ███╗  ██╗           ",
        "  ████╗ ██║██╔══██╗╚══██╔══╝██║██╔═══██╗████╗ ██║           ",
        "  ██╔██╗██║███████║   ██║   ██║██║   ██║██╔██╗██║           ",
        "  ██║╚████║██╔══██║   ██║   ██║██║   ██║██║╚████║           ",
        "  ██║ ╚███║██║  ██║   ██║   ██║╚██████╔╝██║ ╚███║           ",
        "  ╚═╝  ╚══╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚══╝           ",
    ]

    rainbow_lines: list[Text] = []
    for line_idx, line in enumerate(ascii_art):
        colored = Text()
        color = RAINBOW[line_idx % len(RAINBOW)]
        colored.append(line, style=f"bold {color}")
        rainbow_lines.append(colored)

    # Subtitle line with per-character rainbow colors
    subtitle = rainbow_text("✦  Your  Rainbow  AI-Powered  Terminal  Assistant  ✦")

    # Stars decoration
    stars = Text()
    star_line = "★  " * 20
    for i, ch in enumerate(star_line):
        stars.append(ch, style=f"bold {RAINBOW[i % len(RAINBOW)]}")

    # Print everything centered
    console.print()
    console.print(stars, justify="center")
    console.print()
    for line in rainbow_lines:
        console.print(line, justify="center")
    console.print()
    console.print(subtitle, justify="center")
    console.print()
    console.print(stars, justify="center")
    console.print()

# Tool name → human-friendly label + icon
TOOL_LABELS = {
    "run_shell":       ("🔧", "Running shell command"),
    "read_file":       ("📖", "Reading file"),
    "write_file":      ("✏️ ", "Writing file"),
    "list_directory":  ("📁", "Listing directory"),
    "web_search":      ("🌐", "Searching the web"),
    "search_code":     ("🔍", "Searching code"),
}


def format_tool_call(name: str, args: dict) -> str:
    """Format a tool call into a short human-readable description."""
    icon, label = TOOL_LABELS.get(name, ("⚙️ ", name))
    detail = ""
    if name == "run_shell":
        detail = f": [bold]{args.get('command', '')}[/bold]"
    elif name in ("read_file", "write_file"):
        detail = f": [cyan]{args.get('path', '')}[/cyan]"
    elif name == "list_directory":
        detail = f": [cyan]{args.get('path', '.')}[/cyan]"
    elif name == "web_search":
        detail = f": [italic]{args.get('query', '')}[/italic]"
    elif name == "search_code":
        detail = f": [bold]{args.get('pattern', '')}[/bold]"
    return f"{icon} {label}{detail}"


def print_welcome() -> None:
    print_banner()

    # Info panel with rainbow border cycling
    tip = Text()
    tip.append("  Type ", style="dim")
    tip.append("/help", style="bold cyan")
    tip.append(" for commands  •  ", style="dim")
    tip.append("/quit", style="bold cyan")
    tip.append(" to exit  •  ", style="dim")
    tip.append("/clear", style="bold cyan")
    tip.append(" to reset chat  ", style="dim")

    console.print(
        Panel(
            Align.center(tip),
            border_style="magenta",
            padding=(0, 2),
        )
    )
    console.print()


def print_help() -> None:
    title = rainbow_text("❓  OPE-OPA-NATION  Help  ❓")
    console.print(
        Panel(
            "[bold]Commands:[/bold]\n\n"
            "  [cyan]/help[/cyan]                Show this help message\n"
            "  [cyan]/clear[/cyan]               Clear conversation history\n"
            "  [cyan]/model <name>[/cyan]         Switch AI model\n"
            "  [cyan]/provider <name>[/cyan]      Switch AI provider\n"
            "  [cyan]/providers[/cyan]            List all available providers & models\n"
            "  [cyan]/memory[/cyan]               Show all remembered facts\n"
            "  [cyan]/memory <key>[/cyan]         Look up a specific memory\n"
            "  [cyan]/forget <key>[/cyan]         Delete a memory\n"
            "  [cyan]/history[/cyan]              Show this session's chat history\n"
            "  [cyan]/export[/cyan]               Export chat as markdown file\n"
            "  [cyan]/quit[/cyan]                 Exit the agent\n\n"
            "[dim]Just type naturally to chat with the agent.[/dim]",
            title=title,
            border_style="yellow",
            padding=(1, 2),
        )
    )


def print_providers() -> None:
    """Print all available providers and their models."""
    from .agent import PROVIDERS
    title = rainbow_text("🌐  Available Providers  🌐")
    lines = ""
    for name, info in PROVIDERS.items():
        models = "  |  ".join(info["models"][:3])
        lines += f"\n  [bold cyan]{name}[/bold cyan]  —  {info['label']}\n"
        lines += f"  [dim]Models: {models}[/dim]\n"
        lines += f"  [dim]Key: {info['signup_url']}[/dim]\n"
    console.print(Panel(lines.strip(), title=title, border_style="cyan", padding=(1, 2)))


def save_history(agent: Agent) -> Path:
    """Save current session chat history to ~/.ope-opa-nation/history/<timestamp>.json"""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = HISTORY_DIR / f"chat_{ts}.json"
    history = agent.get_history()
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"saved_at": datetime.now().isoformat(), "messages": history}, f, indent=2, default=str)
    return path


def export_markdown(agent: Agent) -> Path:
    """Export current session chat history as a markdown file."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = HISTORY_DIR / f"chat_{ts}.md"
    history = agent.get_history()

    lines = [
        "# OPE-OPA-NATION Chat Export",
        f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
    ]
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if not content or role == "tool":
            continue
        if role == "user":
            lines += [f"## 🧑 You", "", str(content), ""]
        elif role == "assistant":
            lines += [f"## 🌈 OPE-OPA-NATION", "", str(content), ""]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def show_history(agent: Agent) -> None:
    """Print a summary of the current session's conversation."""
    history = agent.get_history()
    msgs = [m for m in history if isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content")]
    if not msgs:
        console.print("[dim]No conversation history yet.[/dim]")
        return
    console.print(f"\n[bold]Session history[/bold]  [dim]({len(msgs)} messages)[/dim]\n")
    for i, msg in enumerate(msgs, 1):
        role = msg["role"]
        content = str(msg["content"])[:120].replace("\n", " ")
        if role == "user":
            console.print(f"  [green]{i}. 🧑 You:[/green] {content}")
        else:
            console.print(f"  [blue]{i}. 🌈 OPE:[/blue] {content}")
    console.print()


def run_chat(agent: Agent) -> None:
    """Main interactive chat loop."""
    print_welcome()

    while True:
        try:
            user_input = Prompt.ask("[bold green]🧑 You[/bold green]")
        except (KeyboardInterrupt, EOFError):
            bye = rainbow_text("✦  Goodbye from OPE-OPA-NATION!  ✦")
            console.print()
            console.print(bye, justify="center")
            console.print()
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        # Built-in slash commands
        if user_input.startswith("/"):
            _handle_command(user_input, agent)
            continue

        # Send to agent with live spinner during tool calls
        tool_calls_made: list[str] = []

        def on_tool_call(name: str, args: dict) -> None:
            msg = format_tool_call(name, args)
            tool_calls_made.append(msg)
            console.print(f"  {msg}", highlight=False)

        agent.on_tool_call = on_tool_call

        console.print()
        reply = None
        with Live(
            Spinner("dots2", text="[bold magenta]OPE-OPA-NATION is thinking…[/bold magenta]"),
            console=console,
            transient=True,
        ):
            try:
                reply = agent.chat(user_input)
            except Exception as e:
                reply = None
                console.print(f"[red]Error:[/red] {e}")

        if reply:
            # Rainbow rule separator
            rule_text = rainbow_text("─── OPE-OPA-NATION ───")
            console.print()
            console.print(rule_text, justify="center")
            console.print()
            console.print(Markdown(reply))
            console.print()


def _handle_command(command: str, agent: Agent) -> None:
    """Handle a /slash command."""
    parts = command.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd in ("/quit", "/exit"):
        history = agent.get_history()
        if any(m.get("role") == "user" for m in history if isinstance(m, dict)):
            path = save_history(agent)
            console.print(f"[dim]Chat saved to {path}[/dim]")
        bye = rainbow_text("✦  Goodbye from OPE-OPA-NATION!  ✦")
        console.print()
        console.print(bye, justify="center")
        console.print()
        sys.exit(0)

    elif cmd == "/clear":
        history = agent.get_history()
        if any(m.get("role") == "user" for m in history if isinstance(m, dict)):
            path = save_history(agent)
            console.print(f"[dim]Chat saved to {path}[/dim]")
        agent.reset()
        console.clear()
        print_welcome()
        console.print("[dim]Conversation cleared.[/dim]\n")

    elif cmd == "/help":
        print_help()

    elif cmd == "/model":
        if not arg:
            console.print(f"[dim]Current model: {agent.config['model']}  |  provider: {agent.config['provider']}[/dim]")
        else:
            agent.config["model"] = arg
            save_config(agent.config)
            console.print(f"[green]Model switched to:[/green] {arg}")

    elif cmd == "/providers":
        print_providers()

    elif cmd == "/provider":
        from .agent import PROVIDERS, get_provider_info
        if not arg:
            current = agent.config["provider"]
            info = get_provider_info(current)
            console.print(f"[dim]Current provider: [bold]{current}[/bold] — {info['label']}[/dim]")
            console.print(f"[dim]Current model: {agent.config['model']}[/dim]")
            console.print("[dim]Use /providers to see all options[/dim]")
        elif arg not in PROVIDERS:
            console.print(f"[red]Unknown provider:[/red] {arg}")
            console.print(f"[dim]Available: {', '.join(PROVIDERS.keys())}[/dim]")
        else:
            info = get_provider_info(arg)
            agent.config["provider"] = arg
            agent.config["model"] = info["default_model"]
            save_config(agent.config)
            console.print(f"[green]Switched to:[/green] [bold]{arg}[/bold] — {info['label']}")
            console.print(f"[green]Default model:[/green] {info['default_model']}")
            if info["env_var"]:
                from .config import get_api_key
                if not get_api_key(arg):
                    console.print(f"\n[yellow]⚠️  No API key set for {arg}[/yellow]")
                    console.print(f"[dim]Get one at: {info['signup_url']}[/dim]")
                    console.print(f"[dim]Then run: /quit  →  opa config set-key <key> --provider {arg}[/dim]")
            # Reinitialize agent with new provider
            try:
                new_agent = Agent(on_tool_call=agent.on_tool_call)
                agent.messages = new_agent.messages
                agent.client = new_agent.client
                console.print(f"[green]✓ Agent restarted with {arg}[/green]")
            except ValueError as e:
                console.print(f"[red]{e}[/red]")

    elif cmd == "/memory":
        result = mem_tool.recall(arg)
        console.print(Panel(result, title=rainbow_text("🧠 Memory"), border_style="cyan"))

    elif cmd == "/forget":
        if not arg:
            console.print("[red]Usage:[/red] /forget <key>")
        else:
            result = mem_tool.forget(arg)
            console.print(f"[dim]{result}[/dim]")

    elif cmd == "/history":
        show_history(agent)

    elif cmd == "/export":
        path = export_markdown(agent)
        console.print(f"[green]Chat exported to:[/green] {path}")

    else:
        console.print(f"[red]Unknown command:[/red] {cmd}  (type [cyan]/help[/cyan] for help)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli-agent",
        description="A Kiro-like CLI AI agent",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Default: no subcommand → run chat
    subparsers.add_parser("chat", help="Start interactive chat (default)")

    # One-shot query
    run_parser = subparsers.add_parser("run", help="Run a single query and exit")
    run_parser.add_argument("query", nargs="+", help="Query to send to the agent")

    # Config management
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_sub = config_parser.add_subparsers(dest="config_command")

    config_sub.add_parser("show", help="Show current config")

    key_parser = config_sub.add_parser("set-key", help="Set API key")
    key_parser.add_argument("key", help="Your Groq API key (gsk_...)")
    key_parser.add_argument(
        "--provider", default="groq", choices=["groq", "openai", "anthropic"],
        help="Provider to set key for (default: groq)"
    )

    model_parser = config_sub.add_parser("set-model", help="Set default model")
    model_parser.add_argument("model", help="Model name, e.g. gpt-4o")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "config":
        _handle_config_command(args)
        return

    # Initialize agent — with setup wizard if no API key found
    try:
        agent = Agent()
    except ValueError:
        # No API key — run setup wizard
        from .agent import PROVIDERS
        console.print()
        console.print(Panel(
            "[bold yellow]No API key found![/bold yellow]\n\n"
            "Choose a provider and get a free key:\n\n"
            "  [bold cyan]1. Groq[/bold cyan]        [green](FREE + fastest)[/green]  →  console.groq.com/keys\n"
            "  [bold cyan]2. OpenRouter[/bold cyan]  [green](FREE models)[/green]    →  openrouter.ai/keys\n"
            "  [bold cyan]3. Together[/bold cyan]    [green](FREE trial)[/green]     →  api.together.ai\n"
            "  [bold cyan]4. OpenAI[/bold cyan]      (paid)            →  platform.openai.com/api-keys\n"
            "  [bold cyan]5. Ollama[/bold cyan]      [green](LOCAL/offline)[/green]  →  ollama.com\n\n"
            "[dim]Recommended: Groq — free, no card needed, very fast[/dim]",
            title=rainbow_text("🔑  First Time Setup"),
            border_style="yellow",
            padding=(1, 2),
        ))
        console.print()
        try:
            provider_choice = Prompt.ask(
                "[bold yellow]Which provider?[/bold yellow]",
                choices=["groq", "openrouter", "together", "openai", "anthropic", "ollama"],
                default="groq",
            )

            if provider_choice == "ollama":
                # Ollama needs no key
                agent.config["provider"] = "ollama"
                agent.config["model"] = PROVIDERS["ollama"]["default_model"]
                save_config(agent.config)
                console.print("[green]✓ Ollama selected![/green] Make sure Ollama is running: [cyan]ollama serve[/cyan]")
                agent = Agent()
            else:
                info = PROVIDERS[provider_choice]
                key = Prompt.ask(f"[bold yellow]Paste your {provider_choice} API key[/bold yellow]")
                key = key.strip()
                if not key:
                    console.print("[red]No key entered.[/red]")
                    sys.exit(1)
                from .config import set_api_key
                set_api_key(provider_choice, key)
                agent.config["provider"] = provider_choice
                agent.config["model"] = info["default_model"]
                save_config(agent.config)
                console.print(f"[green]✓ {provider_choice} key saved![/green] Starting OPE-OPA-NATION...\n")
                agent = Agent()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Cancelled.[/dim]")
            sys.exit(0)

    if args.command == "run":
        # One-shot mode
        query = " ".join(args.query)

        def on_tool_call(name: str, args_: dict) -> None:
            console.print(f"  {format_tool_call(name, args_)}", highlight=False)

        agent.on_tool_call = on_tool_call
        with Live(
            Spinner("dots2", text="[bold magenta]OPE-OPA-NATION is thinking…[/bold magenta]"),
            console=console,
            transient=True,
        ):
            reply = agent.chat(query)
        console.print(Markdown(reply))
    else:
        # Interactive chat (default)
        run_chat(agent)


def _handle_config_command(args) -> None:
    if args.config_command == "show":
        config = load_config()
        console.print("[bold]Current configuration:[/bold]")
        for k, v in config.items():
            if "key" in k:
                v = "***" if v else "(not set)"
            console.print(f"  [cyan]{k}[/cyan] = {v}")

    elif args.config_command == "set-key":
        set_api_key(args.provider, args.key)
        console.print(f"[green]API key saved for provider:[/green] {args.provider}")

    elif args.config_command == "set-model":
        config = load_config()
        config["model"] = args.model
        save_config(config)
        console.print(f"[green]Default model set to:[/green] {args.model}")

    else:
        console.print("[red]Unknown config command.[/red] Use: show | set-key | set-model")
