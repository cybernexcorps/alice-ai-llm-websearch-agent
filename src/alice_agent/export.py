"""Export search results to JSON or Markdown files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def export_result(query: str, answer: str, path: Path) -> None:
    """Write search result to *path* in JSON or Markdown format.

    Format is determined by the file extension:
      - ``.json``  — structured JSON with query, answer, and timestamp
      - ``.md``    — Markdown document with H1 query and answer body

    Args:
        query: The original search query.
        answer: The agent's answer text.
        path:   Destination file path. Parent directories are created if needed.

    Raises:
        ValueError: If the file extension is not ``.json`` or ``.md``.
    """
    suffix = path.suffix.lower()
    if suffix not in {".json", ".md"}:
        raise ValueError(
            f"Неподдерживаемый формат файла: '{suffix}'. Используйте .json или .md"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=timezone.utc).isoformat()

    if suffix == ".json":
        payload = {
            "query": query,
            "answer": answer,
            "timestamp": timestamp,
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    else:
        md = f"# {query}\n\n{answer}\n\n---\n*{timestamp}*\n"
        path.write_text(md, encoding="utf-8")
