"""Rich CLI interface for OPE-OPA-NATION AI agent."""

import sys
import argparse
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
from rich import print as rprint

from .agent import Agent
from .config import load_config, save_config, set_api_key, get_api_key

console = Console()

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
            "  [cyan]/help[/cyan]          Show this help message\n"
            "  [cyan]/clear[/cyan]         Clear conversation history\n"
            "  [cyan]/model <name>[/cyan]  Switch model (e.g. gpt-4o, gpt-4-turbo)\n"
            "  [cyan]/quit[/cyan]          Exit the agent\n\n"
            "[dim]Just type naturally to chat with the agent.[/dim]",
            title=title,
            border_style="yellow",
            padding=(1, 2),
        )
    )


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
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "/quit" or cmd == "/exit":
        console.print("[dim]Goodbye![/dim]")
        sys.exit(0)

    elif cmd == "/clear":
        agent.reset()
        console.clear()
        print_welcome()
        console.print("[dim]Conversation cleared.[/dim]\n")
    elif cmd == "/help":
        print_help()

    elif cmd == "/model":
        if not arg:
            console.print(f"[dim]Current model: {agent.config['model']}[/dim]")
        else:
            agent.config["model"] = arg
            save_config(agent.config)
            console.print(f"[green]Model switched to:[/green] {arg}")

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
    key_parser.add_argument("key", help="Your OpenAI API key (sk-...)")
    key_parser.add_argument(
        "--provider", default="openai", choices=["openai", "anthropic"],
        help="Provider to set key for (default: openai)"
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

    # Initialize agent
    try:
        agent = Agent()
    except ValueError as e:
        console.print(f"[red]Setup error:[/red] {e}")
        sys.exit(1)

    if args.command == "run":
        # One-shot mode
        query = " ".join(args.query)
        tool_calls_made: list[str] = []

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
