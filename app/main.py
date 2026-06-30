import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select

from app.api.admin_routes import router as admin_router
from app.db.database import engine, get_db
from app.db.models import Base, TaskRecord
from app.mq_publisher import close_connection, publish_task
from app.schemas import TranslationRequest, TranslationResponse
from app.services.rule_engine import start_bg_refresh, stop_bg_refresh


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await start_bg_refresh(interval=60)
    yield
    await stop_bg_refresh()
    await engine.dispose()
    await close_connection()


app = FastAPI(title="HermesTranslate", version="0.1.0", lifespan=lifespan)
app.include_router(admin_router)


@app.post("/translate/", response_model=TranslationResponse, status_code=202)
async def create_translation_task(request: TranslationRequest):
    task_id = str(uuid.uuid4())
    await publish_task(task_id, request.text)
    return TranslationResponse(task_id=task_id, status="pending")


@app.get("/status/{task_id}")
async def get_task_status(task_id: str, db=Depends(get_db)):
    record = await db.get(TaskRecord, task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": record.task_id,
        "status": record.status,
        "retry_count": record.retry_count,
        "created_at": record.created_at.isoformat(),
        "result": record.result_text,
    }
