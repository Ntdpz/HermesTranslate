from pydantic import BaseModel


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


class RuleUpdate(BaseModel):
    keyword: str | None = None
    rule_text: str | None = None
