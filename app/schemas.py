import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, field_serializer, field_validator


class TranslationRequest(BaseModel):
    text: str


class TranslationResponse(BaseModel):
    task_id: str
    status: str


class RuleCreate(BaseModel):
    keyword: str
    rule_text: str


class RuleResponse(BaseModel):
    id: str
    keyword: str
    rule_text: str
    updated_at: str

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v: Any) -> str:
        if isinstance(v, uuid.UUID):
            return str(v)
        return str(v)

    @field_validator("updated_at", mode="before")
    @classmethod
    def coerce_updated_at(cls, v: Any) -> str:
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)


class RuleUpdate(BaseModel):
    keyword: str | None = None
    rule_text: str | None = None


class TaskStatusResponse(BaseModel):
    """Response payload for WebSocket and status polling"""
    task_id: str
    status: str
    retry_count: int = 0
    result: str | None = None
    original_text: str | None = None


class HistoryItem(BaseModel):
    """Lightweight history record for localStorage / history API"""
    task_id: str
    status: str
    original_text: str | None = None
    result_text: str | None = None
    created_at: str


class AgentChatRequest(BaseModel):
    """Request to chat directly with a specific agent (no queue)."""
    agent: str  # "main", "translate", "validate"
    text: str


class AgentChatResponse(BaseModel):
    """Response from agent chat — output + metadata."""
    agent: str
    input_text: str
    output_text: str
    meta: dict = {}


class TeachRequest(BaseModel):
    """Teaching feedback — user corrects an agent's output."""
    agent: str  # "main", "translate", "validate"
    original: str  # original input text
    output: str  # what the agent produced
    expected: str | None = None  # what it should have been
    note: str | None = None  # free-text teaching note
