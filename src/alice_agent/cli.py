"""Typer CLI for Alice Agent.

Commands:
  alice search "query"   -- single query via Yandex AI Studio Agent (with built-in WebSearch)
  alice chat             -- interactive REPL with conversation memory
  alice fetch <url>      -- fetch and extract text from a URL
  alice version          -- show configuration info
"""

from __future__ import annotations

import logging
import sys

import openai
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.prompt import Prompt

from alice_agent.export import export_result
from alice_agent.output import (
    console,
    print_answer,
    print_error,
    print_info,
    print_separator,
    print_version_panel,
    print_warning,
)

app = typer.Typer(
    name="alice",
    help="Alice AI — веб-поиск агент для DDVB (Alice AI LLM + Yandex AI Studio)",
    add_completion=False,
    rich_markup_mode="rich",
)


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(name)s: %(message)s",
        stream=sys.stderr,
    )
    if verbose:
        logging.getLogger("alice_agent").setLevel(logging.DEBUG)


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Поисковый запрос на русском языке")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Показывать отладочную информацию")] = False,
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Сохранить результат в файл (.json или .md)")] = None,
    interactive: Annotated[bool, typer.Option("--interactive", "-i", help="Продолжить диалог после ответа (для уточняющих вопросов)")] = False,
) -> None:
    """Выполнить поисковый запрос через агент Yandex AI Studio (WebSearch встроен)."""
    _setup_logging(verbose)

    from alice_agent.agent import AgentRunner
    from alice_agent.config import get_settings

    settings = get_settings()
    if not settings.is_configured():
        print_error("ALICE_YC_API_KEY не установлен. Добавьте его в .env файл.")
        raise typer.Exit(1)

    if verbose:
        print_info(f"Запрос: {query}")
        print_info(f"Агент: {settings.yc_prompt_id} / папка: {settings.yc_folder_id}")
        print_separator()

    runner = AgentRunner(settings=settings)

    with console.status("[dim]Поиск...[/dim]", spinner="dots"):
        answer = runner.run(query)

    print_answer(answer)

    if output:
        try:
            export_result(query=query, answer=answer, path=output)
            print_info(f"Результат сохранён: {output}")
        except ValueError as e:
            print_error(str(e))
            raise typer.Exit(1)

    if not interactive:
        return

    print_separator()
    console.print("[dim]Интерактивный режим: /quit — выйти, /new — новый разговор[/dim]")
    print_separator()

    while True:
        try:
            user_input = Prompt.ask("[bold]Вы[/bold]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]До свидания![/dim]")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit", "/q"):
            console.print("[dim]До свидания![/dim]")
            break

        if user_input.lower() in ("/new", "/reset"):
            runner.new_conversation()
            print_info("Новый разговор начат.")
            print_separator()
            continue

        try:
            with console.status("[dim]Думаю...[/dim]", spinner="dots"):
                answer = runner.run(user_input)
        except openai.APIError as exc:
            print_warning(f"Ошибка API: {exc}. Попробуйте ещё раз или введите /new.")
            continue

        print_answer(answer)
        print_separator()


@app.command()
def chat(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Показывать отладочную информацию")] = False,
) -> None:
    """Запустить интерактивный чат с памятью разговора.

    Команды в чате:
      /new    — начать новый разговор
      /quit   — выйти
    """
    _setup_logging(verbose)

    from alice_agent.agent import AgentRunner
    from alice_agent.config import get_settings

    settings = get_settings()
    if not settings.is_configured():
        print_error("ALICE_YC_API_KEY не установлен. Добавьте его в .env файл.")
        raise typer.Exit(1)

    console.print("[bright_blue]Алиса[/bright_blue] — интерактивный чат")
    console.print("[dim]Команды: /new (новый разговор), /quit (выход)[/dim]")
    print_separator()

    runner = AgentRunner(settings=settings)

    while True:
        try:
            user_input = Prompt.ask("[bold]Вы[/bold]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]До свидания![/dim]")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit", "/q"):
            console.print("[dim]До свидания![/dim]")
            break

        if user_input.lower() in ("/new", "/reset"):
            runner.new_conversation()
            print_info("Новый разговор начат.")
            print_separator()
            continue

        try:
            with console.status("[dim]Думаю...[/dim]", spinner="dots"):
                answer = runner.run(user_input)
        except openai.APIError as exc:
            print_warning(f"Ошибка API: {exc}. Попробуйте ещё раз или введите /new.")
            continue

        print_answer(answer)
        print_separator()


@app.command()
def fetch(
    url: Annotated[str, typer.Argument(help="URL страницы для извлечения текста")],
) -> None:
    """Получить и извлечь текстовое содержимое веб-страницы."""
    from alice_agent.tools.web_fetch import fetch_webpage

    result = fetch_webpage.invoke(url)
    print_answer(result, title="Содержимое страницы")


@app.command()
def version() -> None:
    """Показать версию и конфигурацию агента."""
    from alice_agent.config import get_settings
    settings = get_settings()
    print_version_panel(settings)


@app.command()
def web(
    host: Annotated[str, typer.Option("--host", help="Адрес для прослушивания")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", "-p", help="Порт")] = 8080,
    reload: Annotated[bool, typer.Option("--reload", help="Авто-перезагрузка при изменении файлов")] = False,
) -> None:
    """Запустить веб-интерфейс Alice Agent."""
    import uvicorn
    from alice_agent.web.app import create_app

    print_info(f"Запуск веб-интерфейса на http://{host}:{port}")
    uvicorn.run(create_app(), host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
