"""Web page content fetcher — standalone utility tool."""

from __future__ import annotations

import logging
import re
from typing import Annotated
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 4000
ALLOWED_SCHEMES = {"http", "https"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AliceAgent/0.1; +https://ddvb.ru)",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _validate_url(url: str) -> str | None:
    """Validate URL for safety. Returns error message or None if valid."""
    try:
        parsed = urlparse(url)
    except Exception:
        return "Некорректный URL."

    if parsed.scheme not in ALLOWED_SCHEMES:
        return f"Недопустимая схема URL: {parsed.scheme}. Разрешены только http и https."

    hostname = parsed.hostname or ""
    if hostname in ("localhost", "127.0.0.1", "::1"):
        return "Доступ к локальным адресам запрещён."
    if hostname.startswith("192.168.") or hostname.startswith("10.") or hostname.startswith("172.16."):
        return "Доступ к локальным адресам запрещён."

    return None


def _extract_text_trafilatura(html: str) -> str:
    try:
        import trafilatura
        return trafilatura.extract(html, include_comments=False, include_tables=True) or ""
    except ImportError:
        return ""


def _extract_text_bs4(html: str) -> str:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return re.sub(r"\n{3,}", "\n\n", text)
    except ImportError:
        return html[:MAX_CONTENT_LENGTH]


def _extract_text(html: str) -> str:
    text = _extract_text_trafilatura(html)
    if not text:
        text = _extract_text_bs4(html)
    return text[:MAX_CONTENT_LENGTH]


class _FetchWebpageTool:
    """Simple tool wrapper compatible with .invoke() interface."""

    name = "fetch_webpage"
    description = (
        "Получает и извлекает текстовое содержимое веб-страницы по URL. "
        "Возвращает основной текст страницы."
    )

    def invoke(self, url: str) -> str:
        """Fetch and extract text from a URL.

        Args:
            url: Full URL (must be http:// or https://).

        Returns:
            Extracted text content or error message.
        """
        url = url.strip()
        error = _validate_url(url)
        if error:
            return f"Ошибка: {error}"

        try:
            with httpx.Client(
                timeout=15.0,
                follow_redirects=True,
                headers=HEADERS,
                max_redirects=5,
            ) as client:
                response = client.get(url)
                response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                return f"Страница имеет неподдерживаемый тип содержимого: {content_type}"

            text = _extract_text(response.text)
            if not text.strip():
                return "Не удалось извлечь текстовое содержимое страницы."

            logger.debug("Fetched %d chars from %s", len(text), url)
            return f"Содержимое страницы {url}:\n\n{text}"

        except httpx.HTTPStatusError as e:
            return f"Ошибка HTTP {e.response.status_code} при загрузке страницы."
        except httpx.RequestError as e:
            return f"Ошибка сети при загрузке страницы: {type(e).__name__}"
        except Exception:
            logger.error("Unexpected error fetching %s", url, exc_info=True)
            return "Непредвиденная ошибка при загрузке страницы."


# Singleton tool instance
fetch_webpage = _FetchWebpageTool()
