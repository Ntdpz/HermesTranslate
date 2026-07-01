import uuid
from datetime import datetime
from typing import Any

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
