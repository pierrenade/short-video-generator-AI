from __future__ import annotations

import subprocess
import random
import string
import argparse 
import sys 
from pathlib import Path
from src import fs

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt


fs.run_sync()

def _banner() -> Panel:
    return Panel.fit(
        f"[bold cyan]text-humanizer[/bold cyan] [dim]v{__version__}[/dim]\n"
        "[dim]Deepseek — type /help for commands, /exit to quit[/dim]",
        border_style="cyan",
    )


HELP_TEXT = """\
Available commands:
  /help           Show this help
  /reset          Clear the conversation history
  /history        Show number of messages in the current session
  /tools          List tools available to the agent
  /exit, /quit    Exit the CLI
Anything else is sent to the agent.
"""


def _repl(agent: Agent) -> None:
    console.print(_banner())
    while True:
        try:
            user_in = Prompt.ask("[bold green]you[/bold green]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye[/dim]")
            return

        if not user_in.strip():
            continue

        if user_in.startswith("/"):
            cmd = user_in.strip().lower()
            if cmd in ("/exit", "/quit"):
                console.print("[dim]bye[/dim]")
                return
            if cmd == "/help":
                console.print(HELP_TEXT)
                continue
            if cmd == "/reset":
                agent.reset()
                console.print("[dim]history cleared[/dim]")
                continue
            if cmd == "/history":
                console.print(f"[dim]{len(agent.history)} messages[/dim]")
                continue
            if cmd == "/tools":
                for t in agent.tools:
                    console.print(f"  [cyan]{t.name}[/cyan] — {t.description}")
                continue
            console.print(f"[yellow]unknown command: {cmd}[/yellow]")
            continue

        try:
            reply = agent.send(user_in)
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]error:[/red] {exc}")
            continue

        console.print(Panel(Markdown(reply or "_(no text)_"), border_style="magenta", title="claude"))

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="claude-engineer", description="Interactive Claude Opus 4.7 coding agent.")
    parser.add_argument("--model", help="Override the model (default: claude-opus-4-7)")
    parser.add_argument("--env", default=".env", help="Path to .env file (default: .env)")
    parser.add_argument("--verbose", action="store_true", help="Print tool calls as they happen")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    try:
        cfg = Config.load(env_file=args.env)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.model:
        cfg.model = args.model
    if args.verbose:
        cfg.verbose = True

    agent = Agent(config=cfg)
    _repl(agent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
