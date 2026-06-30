from pydantic import BaseModel


class TranslationRequest(BaseModel):
    text: str


class TranslationResponse(BaseModel):
    task_id: str
    status: str
