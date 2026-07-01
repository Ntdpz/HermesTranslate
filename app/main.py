import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.api.admin_routes import router as admin_router
from app.config import QUEUE_NAME, RABBITMQ_MANAGEMENT_URL
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

# CORS — allow browser-based UIs to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)
# Serve static files (tester.html, monitor.html)
app.mount("/static", StaticFiles(directory="static"), name="static")


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


@app.get("/queue/stats")
async def get_queue_stats():
    """Query RabbitMQ Management API for queue statistics."""
    url = f"{RABBITMQ_MANAGEMENT_URL}/api/queues/%2F/{QUEUE_NAME}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=5.0)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail="Unable to reach RabbitMQ Management API",
            )
        data = resp.json()
    return {
        "queue_name": data.get("name"),
        "messages_ready": data.get("messages_ready", 0),
        "messages_unacked": data.get("messages_unacknowledged", 0),
        "messages_total": data.get("messages", 0),
        "consumers": data.get("consumers", 0),
        "publish_rate": data.get("message_stats", {}).get("publish_details", {}).get("rate", 0.0),
        "deliver_rate": data.get("message_stats", {}).get("deliver_details", {}).get("rate", 0.0),
    }
