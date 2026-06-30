import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.mq_publisher import close_connection, publish_task
from app.schemas import TranslationRequest, TranslationResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_connection()


app = FastAPI(title="HermesTranslate", version="0.1.0", lifespan=lifespan)


@app.post("/translate/", response_model=TranslationResponse, status_code=202)
async def create_translation_task(request: TranslationRequest):
    task_id = str(uuid.uuid4())
    await publish_task(task_id, request.text)
    return TranslationResponse(task_id=task_id, status="pending")
