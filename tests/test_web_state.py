"""Tests for SessionManager (in-memory chat session state)."""

from __future__ import annotations

import time

import pytest

from alice_agent.web.state import SessionManager, _SESSION_TTL_SECONDS


class TestSessionManager:
    def test_creates_new_session_when_id_is_none(self, mock_settings):
        sm = SessionManager()
        runner, cid = sm.get_or_create(None, mock_settings)
        assert cid is not None
        assert runner is not None
        assert sm.session_count() == 1

    def test_returns_same_runner_for_same_id(self, mock_settings):
        sm = SessionManager()
        _, cid = sm.get_or_create(None, mock_settings)
        runner1, _ = sm.get_or_create(cid, mock_settings)
        runner2, _ = sm.get_or_create(cid, mock_settings)
        assert runner1 is runner2

    def test_creates_new_session_for_unknown_id(self, mock_settings):
        sm = SessionManager()
        _, cid = sm.get_or_create("nonexistent-id-12345", mock_settings)
        assert cid != "nonexistent-id-12345"
        assert sm.session_count() == 1

    def test_reset_removes_session(self, mock_settings):
        sm = SessionManager()
        _, cid = sm.get_or_create(None, mock_settings)
        assert sm.session_count() == 1
        sm.reset(cid)
        assert sm.session_count() == 0

    def test_reset_unknown_id_is_noop(self):
        sm = SessionManager()
        sm.reset("does-not-exist")  # Should not raise

    def test_multiple_sessions(self, mock_settings):
        sm = SessionManager()
        _, cid1 = sm.get_or_create(None, mock_settings)
        _, cid2 = sm.get_or_create(None, mock_settings)
        assert cid1 != cid2
        assert sm.session_count() == 2

    def test_ttl_eviction(self, mock_settings, monkeypatch):
        """Stale sessions are evicted on next access."""
        sm = SessionManager()
        _, cid = sm.get_or_create(None, mock_settings)
        assert sm.session_count() == 1

        # Wind the clock forward past TTL
        future_time = time.monotonic() + _SESSION_TTL_SECONDS + 1
        monkeypatch.setattr("alice_agent.web.state.time.monotonic", lambda: future_time)

        # Access triggers eviction
        sm.get_or_create(None, mock_settings)
        assert sm.session_count() == 1  # Old session evicted, new one created

    def test_conversation_id_is_uuid(self, mock_settings):
        sm = SessionManager()
        _, cid = sm.get_or_create(None, mock_settings)
        # UUID4 format: 8-4-4-4-12 hex chars
        import re
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        assert re.match(pattern, cid), f"Expected UUID4, got: {cid}"

    def test_existing_conversation_id_returned_unchanged(self, mock_settings):
        sm = SessionManager()
        _, cid1 = sm.get_or_create(None, mock_settings)
        _, cid2 = sm.get_or_create(cid1, mock_settings)
        assert cid1 == cid2
