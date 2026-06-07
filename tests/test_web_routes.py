"""Tests for FastAPI web routes using TestClient with mocked AgentRunner."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

FINAL_ANSWER = "Ответ агента на запрос о брендинге."
FETCH_CONTENT = "Содержимое страницы https://ddvb.ru:\n\nДДВБ — брендинговое агентство."


@pytest.fixture
def app(mock_settings):
    """Create FastAPI app with test settings injected."""
    from alice_agent.web.app import create_app
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def mock_runner():
    runner = MagicMock()
    runner.run.return_value = FINAL_ANSWER
    runner._previous_response_id = "resp-1"
    return runner


# ── /api/search ──────────────────────────────────────────────

class TestSearchEndpoint:
    def test_returns_answer(self, client, mock_settings, mock_runner):
        with patch("alice_agent.web.routes.AgentRunner", return_value=mock_runner), \
             patch("alice_agent.web.routes.get_settings", return_value=mock_settings):
            resp = client.post("/api/search", json={"query": "тренды брендинга"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == FINAL_ANSWER

    def test_empty_query_returns_422(self, client):
        resp = client.post("/api/search", json={"query": ""})
        assert resp.status_code == 422

    def test_missing_query_returns_422(self, client):
        resp = client.post("/api/search", json={})
        assert resp.status_code == 422

    def test_unconfigured_returns_503(self, client, unconfigured_settings):
        with patch("alice_agent.web.routes.get_settings", return_value=unconfigured_settings):
            resp = client.post("/api/search", json={"query": "запрос"})
        assert resp.status_code == 503


# ── /api/chat ─────────────────────────────────────────────────

class TestChatEndpoint:
    def test_creates_new_session(self, client, mock_settings, mock_runner):
        # AgentRunner is instantiated inside SessionManager (state.py), so patch there
        with patch("alice_agent.web.state.AgentRunner", return_value=mock_runner), \
             patch("alice_agent.web.routes.get_settings", return_value=mock_settings):
            resp = client.post("/api/chat", json={"message": "Привет"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == FINAL_ANSWER
        assert "conversation_id" in data
        assert data["conversation_id"]  # Not empty

    def test_empty_message_returns_422(self, client):
        resp = client.post("/api/chat", json={"message": ""})
        assert resp.status_code == 422

    def test_unconfigured_returns_503(self, client, unconfigured_settings):
        with patch("alice_agent.web.routes.get_settings", return_value=unconfigured_settings):
            resp = client.post("/api/chat", json={"message": "тест"})
        assert resp.status_code == 503


# ── /api/chat/reset ───────────────────────────────────────────

class TestChatResetEndpoint:
    def test_reset_returns_ok(self, client, mock_settings, mock_runner):
        # First, create a session
        with patch("alice_agent.web.state.AgentRunner", return_value=mock_runner), \
             patch("alice_agent.web.routes.get_settings", return_value=mock_settings):
            chat_resp = client.post("/api/chat", json={"message": "Привет"})
        conv_id = chat_resp.json()["conversation_id"]

        resp = client.post("/api/chat/reset", json={"conversation_id": conv_id})
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_reset_unknown_id_still_ok(self, client):
        resp = client.post("/api/chat/reset", json={"conversation_id": "nonexistent"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ── /api/fetch ────────────────────────────────────────────────

class TestFetchEndpoint:
    def test_returns_content(self, client):
        with patch("alice_agent.web.routes.fetch_webpage") as mock_fw:
            mock_fw.invoke.return_value = FETCH_CONTENT
            resp = client.post("/api/fetch", json={"url": "https://ddvb.ru"})
        assert resp.status_code == 200
        assert resp.json()["content"] == FETCH_CONTENT

    def test_empty_url_returns_422(self, client):
        resp = client.post("/api/fetch", json={"url": ""})
        assert resp.status_code == 422


# ── /api/export ───────────────────────────────────────────────

class TestExportEndpoint:
    def test_json_export(self, client):
        resp = client.post("/api/export", json={
            "query": "тренды", "answer": "Ответ", "format": "json"
        })
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        assert "attachment" in resp.headers["content-disposition"]
        import json
        data = json.loads(resp.content)
        assert data["query"] == "тренды"
        assert data["answer"] == "Ответ"
        assert "timestamp" in data

    def test_md_export(self, client):
        resp = client.post("/api/export", json={
            "query": "вопрос", "answer": "Ответ на вопрос", "format": "md"
        })
        assert resp.status_code == 200
        assert "markdown" in resp.headers["content-type"]
        body = resp.content.decode("utf-8")
        assert "# вопрос" in body
        assert "Ответ на вопрос" in body

    def test_invalid_format_returns_422(self, client):
        resp = client.post("/api/export", json={
            "query": "q", "answer": "a", "format": "xlsx"
        })
        assert resp.status_code == 422


# ── /api/config ───────────────────────────────────────────────

class TestConfigEndpoint:
    def test_returns_config(self, client, mock_settings):
        with patch("alice_agent.web.routes.get_settings", return_value=mock_settings):
            resp = client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        assert "agent_id" in data
        assert "folder_id" in data
        assert "endpoint" in data
        assert "max_steps" in data
        assert "api_key_configured" in data

    def test_api_key_configured_true(self, client, mock_settings):
        with patch("alice_agent.web.routes.get_settings", return_value=mock_settings):
            resp = client.get("/api/config")
        assert resp.json()["api_key_configured"] is True

    def test_api_key_configured_false(self, client, unconfigured_settings):
        with patch("alice_agent.web.routes.get_settings", return_value=unconfigured_settings):
            resp = client.get("/api/config")
        assert resp.json()["api_key_configured"] is False
