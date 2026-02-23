"""Pydantic request/response schemas for Alice Agent web API."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, field_validator


class SearchRequest(BaseModel):
    query: str

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query не может быть пустым")
        return v


class SearchResponse(BaseModel):
    answer: str
    response_id: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message не может быть пустым")
        return v


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str


class ChatResetRequest(BaseModel):
    conversation_id: str


class ChatResetResponse(BaseModel):
    status: Literal["ok"] = "ok"


class FetchRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def url_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("url не может быть пустым")
        return v


class FetchResponse(BaseModel):
    content: str


class ExportRequest(BaseModel):
    query: str
    answer: str
    format: Literal["json", "md"]


class ConfigResponse(BaseModel):
    version: str
    agent_id: str
    folder_id: str
    endpoint: str
    max_steps: int
    api_key_configured: bool
