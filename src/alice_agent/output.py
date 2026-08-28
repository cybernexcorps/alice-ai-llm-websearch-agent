"""Rich console output formatting for Alice Agent."""

from __future__ import annotations

import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.spinner import Spinner
from rich.style import Style
from rich.text import Text

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Shared console instance — force UTF-8 on Windows to support Cyrillic + symbols
console = Console(highlight=False, safe_box=True, legacy_windows=False)

# DDVB brand colors
ALICE_BLUE = "bright_blue"
TOOL_YELLOW = "yellow"
ERROR_RED = "red"
SUCCESS_GREEN = "green"
MUTED = "dim"


import re


def print_answer(text: str, title: str = "Алиса") -> None:
    """Print the final agent answer in a styled panel with Markdown."""
    display_text = re.sub(
        r"data:image/[^;]+;base64,[A-Za-z0-9+/=]{100,}",
        "[Изображение сгенерировано (base64)]",
        text,
    )
    md = Markdown(display_text)
    panel = Panel(
        md,
        title=f"[{ALICE_BLUE}]{title}[/{ALICE_BLUE}]",
        border_style=ALICE_BLUE,
        padding=(1, 2),
    )
    console.print(panel)


def print_tool_call(tool_name: str, args_str: str) -> None:
    """Print a tool call event."""
    console.print(
        f"  [{TOOL_YELLOW}]→ {tool_name}[/{TOOL_YELLOW}] [dim]{args_str}[/dim]"
    )


def print_tool_result(tool_name: str, result_preview: str) -> None:
    """Print a tool result preview."""
    console.print(
        f"  [{SUCCESS_GREEN}]← {tool_name}[/{SUCCESS_GREEN}] [dim]{result_preview[:120]}...[/dim]"
    )


def print_step(message: str) -> None:
    """Print a verbose step message."""
    console.print(f"  [dim]{message}[/dim]")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[{ERROR_RED}]Ошибка: {message}[/{ERROR_RED}]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[{TOOL_YELLOW}]Предупреждение: {message}[/{TOOL_YELLOW}]")


def print_info(message: str) -> None:
    """Print an informational message."""
    console.print(f"[{MUTED}]{message}[/{MUTED}]")


def print_separator() -> None:
    """Print a visual separator."""
    console.print(Rule(style=MUTED))


def print_version_panel(settings) -> None:
    """Print version and configuration info panel."""
    from alice_agent import __version__

    from alice_agent.config import AGENT_BASE_URL
    lines = [
        f"[bold]Alice Agent[/bold] v{__version__}",
        "",
        f"[dim]Agent ID:[/dim]     {settings.yc_prompt_id}",
        f"[dim]Folder ID:[/dim]    {settings.yc_folder_id}",
        f"[dim]Endpoint:[/dim]     {AGENT_BASE_URL}",
        f"[dim]Max steps:[/dim]    {settings.max_agent_steps}",
        "",
        f"[dim]API key:[/dim]      {'[green]OK[/green]' if settings.is_configured() else '[red]NOT SET (add ALICE_YC_API_KEY to .env)[/red]'}",
    ]

    panel = Panel(
        "\n".join(lines),
        title=f"[{ALICE_BLUE}]Alice Agent Configuration[/{ALICE_BLUE}]",
        border_style=ALICE_BLUE,
        padding=(1, 2),
    )
    console.print(panel)


