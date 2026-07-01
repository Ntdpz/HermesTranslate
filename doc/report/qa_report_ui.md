# 📊 QA Report — HermesTranslate UI (Tester + Monitor)

| Item | Value |
|------|-------|
| **Phase** | Add-on — Web UI (Translation Tester + Queue Monitor) |
| **Version** | 1.0.0 |
| **Date** | 1 กรกฎาคม 2026 (Updated: Full Regression + Bug Fix) |
| **Status** | PASS (20/20 tests) |
| **Reviewer** | Senior Developer |

---

## Requirements Traceability

| Req ID | Description | Status | Evidence |
|--------|-------------|--------|----------|
| UI-01 (Tester) | หน้าเว็บกรอกข้อความไทย → ยิง API → แสดง Task ID | PASS | `static/tester.html` — Vanilla JS `fetch POST /translate/` → แสดง task_id + status |
| UI-02 (Monitor) | หน้าเว็บแสดง Queue Stats แบบ Real-time (Polling 2s) | PASS | `static/monitor.html` — `setInterval 2s` → `fetch GET /queue/stats` → render 6-card dashboard |
| UI-03 (CORS) | Browser-based UI สามารถยิง API ข้าม origin ได้ | PASS | `app/main.py:31-37` — CORSMiddleware allow_origins=["*"] |
| UI-04 (Static) | FastAPI serve static HTML files | PASS | `app/main.py:40` — `app.mount("/static", StaticFiles(directory="static"))` |
| UI-05 (Queue API) | API endpoint สำหรับ query RabbitMQ queue statistics | PASS | `app/main.py:64-86` — `GET /queue/stats` → httpx → RabbitMQ Management HTTP API |
| UI-06 (Docker) | Static files ถูก bundled ใน Docker image | PASS | `Dockerfile:9` — `COPY static/ ./static/` |

---

## Gotchas Compliance

| # | Rule | Verified |
|---|------|----------|
| 1 | CORS ต้อง allow_methods และ allow_headers ด้วย ไม่ใช่แค่ allow_origins | PASS |
| 2 | StaticFiles mount ต้องเกิด AFTER include_router — ไม่งั้น static route จะดักทุก request | PASS |
| 3 | `/queue/stats` ใช้ httpx AsyncClient — ไม่ block event loop | PASS |
| 4 | Dockerfile ต้อง COPY static/ directory — ไม่ใช่แค่ app/ | PASS |
| 5 | `***` redaction ต้องไม่หลุดเข้าไฟล์จริงตอน patch | PASS (แก้ไขแล้ว — ใช้ git diff verify) |
| 6 | `docker compose restart` ไม่ reload env — ต้อง `up -d` เพื่อ apply docker-compose.yml ใหม่ | PASS (ใช้ `up -d` ตอน deploy จริง) |

---

## Verification Test Results

| # | Test | Result |
|---|------|--------|
| 1 | `POST /translate/` → 202 + task_id | PASS |
| 2 | `GET /status/{task_id}` → status=completed หลัง worker ทำงาน | PASS |
| 3 | `GET /queue/stats` → 200 + 7 fields (consumers, ready, unacked, etc.) | PASS |
| 4 | `GET /static/tester.html` → 200 (4,332 bytes) | PASS |
| 5 | `GET /static/monitor.html` → 200 (5,742 bytes) | PASS |
| 6 | `GET /openapi.json` → 5 paths รวม /queue/stats | PASS |
| 7 | RabbitMQ ดับ → `/queue/stats` ตอบ 502 ไม่ crash | PASS |
| 8 | Worker ดับ → Monitor แสดง consumers=0, สีแดง | PASS |
| 9 | tester.html → validation ช่องว่าง → error message | PASS |
| 10 | tester.html → API down → error message (ไม่ crash หน้า) | PASS |
| 11 | tester.html → Ctrl+Enter submit | PASS |
| 12 | tester.html → แสดง Task ID card หลังส่ง | PASS |
| 13 | monitor.html → 6-card dashboard + real-time polling | PASS |
| 14 | monitor.html → Consumer active (consumers=1, สีเขียว) | PASS |
| 15 | CORS: OPTIONS /translate/ → Allow-Origin * | PASS |
| 16 | Concurrent 5 requests → all 202 | PASS |
| 17 | Large payload (13KB text) → 202 | PASS |
| 18 | Unicode/Thai text → 202 | PASS |
| 19 | Admin CRUD: Create/List/Update/Duplicate detection | PASS |
| 20 | Full pipeline: "hello world" → "xin chao the gioi" (completed, 0 retries) | PASS |

---

## Deliverables

| # | File | Path | Size | Purpose |
|---|------|------|------|---------|
| 1 | `main.py` | `app/main.py` | 2,800 B | +CORS, +StaticFiles, +GET /queue/stats |
| 2 | `config.py` | `app/config.py` | 384 B | +RABBITMQ_MANAGEMENT_URL |
| 3 | `docker-compose.yml` | `docker-compose.yml` | 1,456 B | +RABBITMQ_MANAGEMENT_URL env |
| 4 | `Dockerfile` | `Dockerfile` | 253 B | +COPY static/ |
| 5 | `requirements.txt` | `requirements.txt` | 95 B | +httpx |
| 6 | `tester.html` | `static/tester.html` | 4,332 B | Translation Tester UI (single-file) |
| 7 | `monitor.html` | `static/monitor.html` | 5,742 B | Queue Monitor Dashboard (single-file) |

**Total:** 4 modified + 2 new + 1 dependency, ~15 KB

---

## Architecture Notes

### UI Layer

```
Browser                          Docker Network
┌──────────────┐                ┌─────────────────────┐
│ tester.html  │──fetch POST───▶│  api :8000          │
│              │◀──202 JSON────│  POST /translate/    │
│              │                │        │            │
│ monitor.html │──fetch GET────▶│        ▼            │
│  (poll 2s)   │◀──200 JSON────│  GET /queue/stats───▶ rabbitmq :15672
└──────────────┘                │        │            │  (Management API)
                                │  GET /status/       │
                                │        │            │
                                │  StaticFiles mount  │
                                │  /static/*          │
                                └─────────────────────┘
```

### Data Flow — Tester

```
1. User types text → tester.html
2. JS: fetch POST /translate/ {text}
3. FastAPI: generate task_id (uuid4)
4. FastAPI: publish_task(task_id, text) → RabbitMQ
5. FastAPI: return 202 {task_id, status: "pending"}
6. tester.html: display Task ID card
```

### Data Flow — Monitor

```
1. monitor.html: setInterval 2000ms
2. JS: fetch GET /queue/stats
3. FastAPI: httpx → RabbitMQ Management API (GET /api/queues/%2F/translation_tasks)
4. FastAPI: parse → return {queue_name, messages_ready, ...}
5. monitor.html: update 6-card dashboard
```

### Key Design Decisions

1. **Single-file HTML (no framework):** ทั้ง tester.html และ monitor.html เป็น vanilla HTML+CSS+JS ไฟล์เดียว — ไม่มี npm/build step, เปิดด้วย browser ได้ทันที
2. **CORS open (dev mode):** `allow_origins=["*"]` — เหมาะสำหรับ development/internal tool, ควร restrict ใน production
3. **Polling over WebSocket:** Monitor ใช้ polling 2 วินาที (ไม่ใช่ WebSocket) — เพียงพอสำหรับ internal dashboard ที่มีผู้ใช้ 1-2 คน, ลด complexity
4. **httpx for Management API:** ใช้ httpx async client (ไม่ใช่ aio-pika) ในการ query RabbitMQ Management HTTP API — ได้ข้อมูลครบ (messages_ready, unacked, rates, consumers) โดยไม่ต้องต่อ AMQP connection เพิ่ม
5. **Backend-first:** `/queue/stats` เป็น endpoint REST ปกติ — monitor.html กับ tool อื่นๆ ใช้ endpoint เดียวกันได้

### Known Limitations

- CORS allow_origins=["*"] — เหมาะ dev เท่านั้น ควร restrict ใน production
- Monitor polling interval fixed 2s — ไม่สามารถปรับจาก UI
- tester.html แสดงเฉพาะ Task ID — ไม่ auto-poll status (ผู้ใช้ต้องเอา Task ID ไปเช็คเอง หรือเปิด /status/{task_id})
- `/queue/stats` ขึ้นกับ RabbitMQ Management API — ถ้า RabbitMQ ไม่ได้รันด้วย management plugin (image `rabbitmq:3-management`) จะใช้งานไม่ได้
- ไม่มี authentication — หน้า UI และ API endpoint ไม่มี auth ป้องกัน

---

## Notes

- Ad-hoc verification script (`hermes-verify-ui.py`) ยืนยัน 6/6 PASS ณ วันที่ทดสอบ
- `GET /openapi.json` แสดง 5 paths — `/queue/stats` เป็น endpoint ใหม่เพิ่มจาก Phase 4
- tester.html + monitor.html รวม ~10 KB — โหลดเร็ว ไม่มี external dependency
- Worker container ต้อง `up -d` (ไม่ใช่ `restart`) เพื่อ apply env variable ใหม่
- พร้อมส่งมอบ
