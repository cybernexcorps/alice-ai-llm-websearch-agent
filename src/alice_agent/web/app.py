"""FastAPI application factory for Alice Agent web interface."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from alice_agent.web.routes import router

# Resolve static directory relative to this package
_PACKAGE_DIR = Path(__file__).parent.parent.parent.parent  # project root
_STATIC_DIR = _PACKAGE_DIR / "static"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Alice Agent",
        description="AI web search agent for DDVB branding agency",
        version="0.2.0",
        docs_url="/api/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    # Mount static files last (catches all unmatched paths for SPA routing)
    if _STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")

    return app
