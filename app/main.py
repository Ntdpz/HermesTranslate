import asyncio
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.api.admin_routes import router as admin_router
from app.hermes_manager import router as hermes_router
from app.config import QUEUE_NAME, RABBITMQ_MANAGEMENT_URL
from app.db.database import async_session_factory, engine, get_db
from app.db.models import Base, TaskRecord
from app.mq_publisher import close_connection, publish_task
import re

from app.agents.main_agent import build_context
from app.agents.translate_agent import translate
from app.agents.validate_agent import validate
from app.schemas import AgentChatRequest, AgentChatResponse, HistoryItem, TaskStatusResponse, TranslationRequest, TranslationResponse
from app.schemas import RuleCreate, TeachRequest
from app.services.rule_engine import extract_rules, reload as reload_rules, start_bg_refresh, stop_bg_refresh


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
app.include_router(hermes_router)
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


@app.post("/cancel/{task_id}")
async def cancel_task(task_id: str, db=Depends(get_db)):
    """Cancel a pending or in-progress translation task."""
    record = await db.get(TaskRecord, task_id)
    if record is None:
        # Create a preemptive cancelled record so the worker skips it
        record = TaskRecord(task_id=task_id, status="cancelled")
        db.add(record)
        await db.commit()
        return {"task_id": task_id, "status": "cancelled"}
    if record.status in ("completed", "failed", "cancelled"):
        raise HTTPException(
            status_code=409,
            detail=f"Task already in terminal state: {record.status}",
        )
    record.status = "cancelled"
    await db.commit()
    return {"task_id": task_id, "status": "cancelled"}


@app.get("/history")
async def get_history(limit: int = 20, db=Depends(get_db)):
    """Return recent translation tasks for client-side history."""
    result = await db.execute(
        select(TaskRecord)
        .where(TaskRecord.original_text.isnot(None))
        .order_by(TaskRecord.created_at.desc())
        .limit(min(limit, 50))
    )
    records = result.scalars().all()
    return [
        {
            "task_id": r.task_id,
            "status": r.status,
            "original_text": r.original_text,
            "result_text": r.result_text,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]


@app.post("/agent/chat", response_model=AgentChatResponse)
async def agent_chat(request: AgentChatRequest):
    """Call an agent directly (bypasses queue) for interactive console use."""
    if request.agent == "main":
        context_md = await build_context("console", request.text)
        rules = await extract_rules(request.text)
        return AgentChatResponse(
            agent="main",
            input_text=request.text,
            output_text=context_md,
            meta={"rules_matched": len(rules), "rules": rules},
        )
    elif request.agent == "translate":
        translated = await translate(request.text)
        rule_pattern = re.findall(
            r"\d+\. \*\*(.+?)\*\*: (.+?) \(updated:", request.text
        )
        rules_applied = [
            {"keyword": kw, "rule_text": rt} for kw, rt in rule_pattern
        ]
        return AgentChatResponse(
            agent="translate",
            input_text=request.text,
            output_text=translated,
            meta={"rules_applied": len(rules_applied), "rules": rules_applied},
        )
    elif request.agent == "validate":
        is_valid = await validate(request.text)
        violations = await extract_rules(request.text)
        return AgentChatResponse(
            agent="validate",
            input_text=request.text,
            output_text="PASS" if is_valid else f"FAIL — {len(violations)} violation(s) found",
            meta={"valid": is_valid, "violations": violations},
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent: {request.agent}. Use 'main', 'translate', or 'validate'.",
        )


@app.post("/agent/teach")
async def teach_agent(request: TeachRequest, db=Depends(get_db)):
    """Save teaching feedback — creates a new translation rule if parseable."""
    import json
    from pathlib import Path
    from datetime import datetime

    result = {"agent": request.agent, "action": "noted"}

    # Try to extract a keyword→replacement pattern
    if request.expected and request.original:
        # Heuristic: find the differing word between original and expected
        orig_words = set(request.original.lower().split())
        expected_words = set(request.expected.lower().split())
        # Words in original not in expected → likely the keyword to replace
        for word in sorted(orig_words - expected_words, key=len, reverse=True):
            if len(word) >= 2:
                # Create rule: keyword=word, rule_text="to <expected>"
                from app.db.models import TranslationRule
                from sqlalchemy import select

                existing = await db.execute(
                    select(TranslationRule).where(TranslationRule.keyword == word)
                )
                if existing.scalar_one_or_none() is None:
                    db_rule = TranslationRule(
                        keyword=word,
                        rule_text=f"to {request.expected}",
                    )
                    db.add(db_rule)
                    await db.commit()
                    await reload_rules()
                    result["action"] = "rule_created"
                    result["keyword"] = word
                    result["rule_text"] = f"to {request.expected}"
                    break

    # Always save to teach log for reference
    log_path = Path(__file__).parent / "teach_log.json"
    log = []
    if log_path.exists():
        log = json.loads(log_path.read_text())
    log.append({
        "agent": request.agent,
        "original": request.original,
        "output": request.output,
        "expected": request.expected,
        "note": request.note,
        "action": result["action"],
        "timestamp": datetime.now().isoformat(),
    })
    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    result["log_count"] = len(log)

    return result


@app.websocket("/ws/task/{task_id}")
async def websocket_task(websocket: WebSocket, task_id: str):
    """Real-time task status updates via WebSocket with 1-second DB polling."""
    await websocket.accept()
    try:
        while True:
            async with async_session_factory() as session:
                record = await session.get(TaskRecord, task_id)
                if record:
                    await websocket.send_json({
                        "task_id": record.task_id,
                        "status": record.status,
                        "retry_count": record.retry_count,
                        "result": record.result_text,
                        "original_text": record.original_text,
                    })
                    if record.status in ("completed", "failed", "cancelled"):
                        break
                else:
                    # Record not yet created by worker — still pending
                    await websocket.send_json({
                        "task_id": task_id,
                        "status": "pending",
                        "retry_count": 0,
                        "result": None,
                        "original_text": None,
                    })
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
