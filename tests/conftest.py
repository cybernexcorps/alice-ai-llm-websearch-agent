"""Shared test fixtures for Alice Agent tests."""

from __future__ import annotations

import pytest

from alice_agent.config import Settings, reset_settings


@pytest.fixture(autouse=True)
def reset_settings_singleton():
    """Reset settings singleton before each test."""
    reset_settings()
    yield
    reset_settings()


@pytest.fixture
def mock_settings(monkeypatch) -> Settings:
    """Create test settings with dummy credentials."""
    monkeypatch.setenv("ALICE_YC_API_KEY", "test-api-key")
    monkeypatch.setenv("ALICE_YC_FOLDER_ID", "test-folder-id")
    monkeypatch.setenv("ALICE_YC_PROMPT_ID", "test-prompt-id")
    monkeypatch.setenv("ALICE_MAX_AGENT_STEPS", "5")
    reset_settings()
    return Settings()


@pytest.fixture
def unconfigured_settings(monkeypatch) -> Settings:
    """Settings without API key configured."""
    monkeypatch.setenv("ALICE_YC_API_KEY", "")
    monkeypatch.setenv("ALICE_YC_FOLDER_ID", "test-folder-id")
    reset_settings()
    return Settings()
