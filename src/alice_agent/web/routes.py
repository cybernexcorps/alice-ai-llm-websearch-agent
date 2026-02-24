"""FastAPI route handlers for Alice Agent web API."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from alice_agent.agent import AgentRunner
from alice_agent.config import AGENT_BASE_URL, get_settings
from alice_agent.tools.web_fetch import fetch_webpage
from alice_agent.web.models import (
    ChatResetRequest,
    ChatResetResponse,
    ChatRequest,
    ChatResponse,
    ConfigResponse,
    ExportRequest,
    FetchRequest,
    FetchResponse,
    SearchRequest,
    SearchResponse,
)
from alice_agent.web.state import SessionManager

router = APIRouter(prefix="/api")

# Module-level session manager (shared across requests)
_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Return the module-level session manager (injectable for testing)."""
    return _session_manager


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    """Run a one-shot search query via Yandex AI Studio agent."""
    settings = get_settings()
    if not settings.is_configured():
        raise HTTPException(status_code=503, detail="API ключ не настроен.")

    runner = AgentRunner(settings=settings)
    answer = await asyncio.to_thread(runner.run, req.query)
    return SearchResponse(
        answer=answer,
        response_id=runner._previous_response_id,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """Send a message in a multi-turn conversation."""
    settings = get_settings()
    if not settings.is_configured():
        raise HTTPException(status_code=503, detail="API ключ не настроен.")

    sm = get_session_manager()
    runner, conv_id = sm.get_or_create(req.conversation_id, settings)
    answer = await asyncio.to_thread(runner.run, req.message)
    return ChatResponse(answer=answer, conversation_id=conv_id)


@router.post("/chat/reset", response_model=ChatResetResponse)
async def chat_reset(req: ChatResetRequest) -> ChatResetResponse:
    """Reset (delete) a conversation session."""
    sm = get_session_manager()
    sm.reset(req.conversation_id)
    return ChatResetResponse()


@router.post("/fetch", response_model=FetchResponse)
async def fetch(req: FetchRequest) -> FetchResponse:
    """Fetch and extract text content from a URL."""
    content = await asyncio.to_thread(fetch_webpage.invoke, req.url)
    return FetchResponse(content=content)


@router.post("/export")
async def export(req: ExportRequest) -> Response:
    """Generate and download a search result as JSON or Markdown."""
    timestamp = datetime.now(tz=timezone.utc).isoformat()

    if req.format == "json":
        payload = {
            "query": req.query,
            "answer": req.answer,
            "timestamp": timestamp,
        }
        content = json.dumps(payload, ensure_ascii=False, indent=2)
        media_type = "application/json"
        filename = "alice-result.json"
    else:
        content = f"# {req.query}\n\n{req.answer}\n\n---\n*{timestamp}*\n"
        media_type = "text/markdown; charset=utf-8"
        filename = "alice-result.md"

    return Response(
        content=content.encode("utf-8"),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/config", response_model=ConfigResponse)
async def config() -> ConfigResponse:
    """Return current agent configuration (no secrets)."""
    from alice_agent import __version__

    settings = get_settings()
    return ConfigResponse(
        version=__version__,
        agent_id=settings.yc_prompt_id,
        folder_id=settings.yc_folder_id,
        endpoint=AGENT_BASE_URL,
        max_steps=settings.max_agent_steps,
        api_key_configured=settings.is_configured(),
    )
