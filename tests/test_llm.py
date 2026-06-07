"""Tests for Alice Agent configuration and client setup."""

from __future__ import annotations

import pytest


class TestSettings:
    """Tests for Pydantic Settings configuration."""

    def test_default_prompt_id(self):
        """Default prompt ID should be the configured agent."""
        from alice_agent.config import Settings
        s = Settings()
        assert s.yc_prompt_id == "fvtvl13pf2lknmsk33to"

    def test_default_folder_id(self):
        """Default folder ID should be the DDVB folder."""
        from alice_agent.config import Settings
        s = Settings()
        assert s.yc_folder_id == "b1g6co0cfokq8k24mu7n"

    def test_api_key_from_env(self, monkeypatch):
        """API key should be loaded from ALICE_YC_API_KEY env var."""
        monkeypatch.setenv("ALICE_YC_API_KEY", "my-secret-key")
        from alice_agent.config import reset_settings, Settings
        reset_settings()
        s = Settings()
        assert s.yc_api_key.get_secret_value() == "my-secret-key"

    def test_prompt_id_from_env(self, monkeypatch):
        """Prompt ID should be overridable via env var."""
        monkeypatch.setenv("ALICE_YC_PROMPT_ID", "custom-prompt-id")
        from alice_agent.config import reset_settings, Settings
        reset_settings()
        s = Settings()
        assert s.yc_prompt_id == "custom-prompt-id"

    def test_is_configured_with_key(self, monkeypatch):
        """is_configured() True when API key is set."""
        monkeypatch.setenv("ALICE_YC_API_KEY", "some-key")
        from alice_agent.config import reset_settings, Settings
        reset_settings()
        s = Settings()
        assert s.is_configured() is True

    def test_is_configured_without_key(self, monkeypatch):
        """is_configured() False when API key is empty."""
        monkeypatch.setenv("ALICE_YC_API_KEY", "")
        from alice_agent.config import reset_settings, Settings
        reset_settings()
        s = Settings()
        assert s.is_configured() is False

    def test_secret_key_not_in_repr(self, mock_settings):
        """API key value should not appear in str() of settings."""
        assert "test-api-key" not in str(mock_settings.yc_api_key)

    def test_get_settings_singleton(self, monkeypatch):
        """get_settings() should return same instance on repeated calls."""
        from alice_agent.config import get_settings, reset_settings
        reset_settings()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_reset_settings_clears_singleton(self):
        """reset_settings() should clear the cached instance."""
        from alice_agent.config import get_settings, reset_settings
        reset_settings()
        s1 = get_settings()
        reset_settings()
        s2 = get_settings()
        assert s1 is not s2


class TestAgentBaseUrl:
    """Tests for the agent endpoint configuration."""

    def test_agent_base_url_is_rest_assistant(self):
        """AGENT_BASE_URL should point to rest-assistant endpoint."""
        from alice_agent.config import AGENT_BASE_URL
        assert "rest-assistant.api.cloud.yandex.net" in AGENT_BASE_URL
        assert AGENT_BASE_URL.startswith("https://")

    def test_agent_base_url_is_v1(self):
        """AGENT_BASE_URL should use /v1 path."""
        from alice_agent.config import AGENT_BASE_URL
        assert AGENT_BASE_URL.endswith("/v1")
