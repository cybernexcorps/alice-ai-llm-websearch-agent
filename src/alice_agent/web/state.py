"""In-memory session manager for multi-turn chat conversations."""

from __future__ import annotations

import time
from typing import Optional

from alice_agent.agent import AgentRunner
from alice_agent.config import Settings

_SESSION_TTL_SECONDS = 3600  # 1 hour


class SessionManager:
    """Manages per-conversation AgentRunner instances.

    Keyed by conversation_id (UUID string). Lazy TTL eviction: stale sessions
    are removed when any session is accessed or created.
    """

    def __init__(self) -> None:
        # conversation_id -> (AgentRunner, last_accessed_timestamp)
        self._sessions: dict[str, tuple[AgentRunner, float]] = {}

    def _evict_stale(self) -> None:
        now = time.monotonic()
        stale = [
            cid
            for cid, (_, ts) in self._sessions.items()
            if now - ts > _SESSION_TTL_SECONDS
        ]
        for cid in stale:
            del self._sessions[cid]

    def get_or_create(
        self,
        conversation_id: Optional[str],
        settings: Settings,
    ) -> tuple[AgentRunner, str]:
        """Return (runner, conversation_id) for the given session.

        If conversation_id is None or unknown, a new session is created.
        Returns the (possibly new) conversation_id alongside the runner.
        """
        self._evict_stale()

        if conversation_id and conversation_id in self._sessions:
            runner, _ = self._sessions[conversation_id]
            self._sessions[conversation_id] = (runner, time.monotonic())
            return runner, conversation_id

        # Create new session
        import uuid
        new_id = str(uuid.uuid4())
        runner = AgentRunner(settings=settings)
        self._sessions[new_id] = (runner, time.monotonic())
        return runner, new_id

    def reset(self, conversation_id: str) -> None:
        """Reset (delete) a conversation session."""
        self._sessions.pop(conversation_id, None)

    def session_count(self) -> int:
        """Return the number of active sessions (for testing)."""
        return len(self._sessions)
