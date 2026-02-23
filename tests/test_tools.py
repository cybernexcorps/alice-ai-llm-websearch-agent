"""Tests for Alice Agent local tools (web_fetch)."""

from __future__ import annotations

import httpx
import respx


class TestFetchWebpage:
    """Tests for fetch_webpage tool."""

    def test_invalid_scheme_rejected(self):
        """Should reject non-HTTP schemes."""
        from alice_agent.tools.web_fetch import fetch_webpage
        result = fetch_webpage.invoke("ftp://example.com/file")
        assert "ошибка" in result.lower() or "недопустимая" in result.lower()

    def test_localhost_rejected(self):
        """Should reject localhost URLs."""
        from alice_agent.tools.web_fetch import fetch_webpage
        result = fetch_webpage.invoke("http://localhost/admin")
        assert "ошибка" in result.lower() or "запрещён" in result.lower()

    def test_private_ip_rejected(self):
        """Should reject private IP URLs."""
        from alice_agent.tools.web_fetch import fetch_webpage
        result = fetch_webpage.invoke("http://192.168.1.1/config")
        assert "ошибка" in result.lower() or "запрещён" in result.lower()

    def test_javascript_scheme_rejected(self):
        """Should reject javascript: scheme."""
        from alice_agent.tools.web_fetch import _validate_url
        assert _validate_url("javascript:alert(1)") is not None

    def test_file_scheme_rejected(self):
        """Should reject file:// scheme."""
        from alice_agent.tools.web_fetch import _validate_url
        assert _validate_url("file:///etc/passwd") is not None

    def test_valid_https_url_accepted(self):
        """Should accept valid HTTPS URLs."""
        from alice_agent.tools.web_fetch import _validate_url
        assert _validate_url("https://example.com/page") is None

    def test_valid_http_url_accepted(self):
        """Should accept valid HTTP URLs."""
        from alice_agent.tools.web_fetch import _validate_url
        assert _validate_url("http://example.ru/article") is None

    @respx.mock
    def test_fetch_returns_content(self):
        """Should fetch and extract text from HTML page."""
        html = """
        <html><body>
        <article>
        <h1>Тренды брендинга</h1>
        <p>В 2026 году основными трендами являются AI и устойчивость.</p>
        </article>
        </body></html>
        """
        respx.get("https://example.ru/article").mock(
            return_value=httpx.Response(
                200, text=html, headers={"content-type": "text/html; charset=utf-8"}
            )
        )

        from alice_agent.tools.web_fetch import fetch_webpage
        result = fetch_webpage.invoke("https://example.ru/article")
        assert "example.ru" in result
        assert len(result) > 20

    @respx.mock
    def test_fetch_non_html_rejected(self):
        """Should reject non-HTML content types."""
        respx.get("https://example.ru/data.pdf").mock(
            return_value=httpx.Response(
                200,
                content=b"%PDF-1.4",
                headers={"content-type": "application/pdf"},
            )
        )

        from alice_agent.tools.web_fetch import fetch_webpage
        result = fetch_webpage.invoke("https://example.ru/data.pdf")
        assert "неподдерживаемый" in result.lower() or "тип" in result.lower()

    @respx.mock
    def test_fetch_404_returns_error(self):
        """Should return error message on HTTP 404."""
        respx.get("https://example.ru/notfound").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        from alice_agent.tools.web_fetch import fetch_webpage
        result = fetch_webpage.invoke("https://example.ru/notfound")
        assert "404" in result or "ошибка" in result.lower()

    def test_tool_has_correct_name(self):
        """fetch_webpage tool should have expected name."""
        from alice_agent.tools.web_fetch import fetch_webpage
        assert fetch_webpage.name == "fetch_webpage"

    def test_tools_module_exports_fetch_webpage(self):
        """tools __init__ should export fetch_webpage."""
        from alice_agent.tools import fetch_webpage
        assert callable(fetch_webpage.invoke)
