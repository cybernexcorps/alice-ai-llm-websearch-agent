"""Tests for web API Pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from alice_agent.web.models import (
    ChatRequest,
    ChatResetRequest,
    ChatResetResponse,
    ChatResponse,
    ConfigResponse,
    ExportRequest,
    FetchRequest,
    FetchResponse,
    SearchRequest,
    SearchResponse,
)


class TestSearchRequest:
    def test_valid(self):
        r = SearchRequest(query="тренды брендинга 2026")
        assert r.query == "тренды брендинга 2026"

    def test_strips_whitespace(self):
        r = SearchRequest(query="  запрос  ")
        assert r.query == "запрос"

    def test_empty_raises(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="   ")


class TestSearchResponse:
    def test_valid(self):
        r = SearchResponse(answer="Ответ агента", response_id="r1")
        assert r.answer == "Ответ агента"
        assert r.response_id == "r1"

    def test_response_id_optional(self):
        r = SearchResponse(answer="Ответ")
        assert r.response_id is None


class TestChatRequest:
    def test_valid_no_conversation(self):
        r = ChatRequest(message="Привет")
        assert r.message == "Привет"
        assert r.conversation_id is None

    def test_valid_with_conversation(self):
        r = ChatRequest(message="Продолжим", conversation_id="conv-123")
        assert r.conversation_id == "conv-123"

    def test_strips_message(self):
        r = ChatRequest(message="  текст  ")
        assert r.message == "текст"

    def test_empty_message_raises(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="")


class TestChatResponse:
    def test_valid(self):
        r = ChatResponse(answer="Ответ", conversation_id="abc")
        assert r.conversation_id == "abc"


class TestChatResetRequest:
    def test_valid(self):
        r = ChatResetRequest(conversation_id="conv-456")
        assert r.conversation_id == "conv-456"


class TestChatResetResponse:
    def test_default_status(self):
        r = ChatResetResponse()
        assert r.status == "ok"


class TestFetchRequest:
    def test_valid(self):
        r = FetchRequest(url="https://ddvb.ru")
        assert r.url == "https://ddvb.ru"

    def test_strips_url(self):
        r = FetchRequest(url="  https://example.com  ")
        assert r.url == "https://example.com"

    def test_empty_raises(self):
        with pytest.raises(ValidationError):
            FetchRequest(url="")


class TestFetchResponse:
    def test_valid(self):
        r = FetchResponse(content="Текст страницы")
        assert r.content == "Текст страницы"


class TestExportRequest:
    def test_json_format(self):
        r = ExportRequest(query="q", answer="a", format="json")
        assert r.format == "json"

    def test_md_format(self):
        r = ExportRequest(query="q", answer="a", format="md")
        assert r.format == "md"

    def test_invalid_format_raises(self):
        with pytest.raises(ValidationError):
            ExportRequest(query="q", answer="a", format="csv")


class TestConfigResponse:
    def test_valid(self):
        r = ConfigResponse(
            version="0.2.0",
            agent_id="agent123",
            folder_id="folder456",
            endpoint="https://api.example.com/v1",
            max_steps=15,
            api_key_configured=True,
        )
        assert r.version == "0.2.0"
        assert r.api_key_configured is True
