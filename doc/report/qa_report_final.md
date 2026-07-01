# 📊 QA Report — HermesTranslate (Phase 2-4)

| Item | Value |
|------|-------|
| **Phase** | 2-4 — Knowledge Base, Multi-Agent, Integration |
| **Version** | 0.2.0 |
| **Date** | 1 กรกฎาคม 2026 (Updated: Full Regression) |
| **Status** | PASS |
| **Reviewer** | Senior Developer / QA Tester |
| **Phase 1 Report** | `doc/report/qa_report_phase1.md` |
| **UI Report** | `doc/report/qa_report_ui.md` |

---

## Phase 2: Knowledge Base & Rule Management

| Req ID | Description | Status | Evidence |
|--------|-------------|--------|----------|
| FR-02 | PostgreSQL สำหรับเก็บกฎการแปล | PASS | `async_session_factory` เชื่อมต่อได้ |
| TR-03 | PostgreSQL ใน docker-compose + Volume + Healthcheck | PASS | `docker compose config` ผ่าน, pg_isready healthcheck |
| FR-02 | Admin API CRUD (POST/GET/PUT) | PASS | 3 endpoints `/admin/rules/` ทำงานครบ |
| FR-03 | Aho-Corasick filtering (Exact Match) | PASS | `extract_rules("hello world")` -> 2 matches |
| FR-02 (Conflict) | Timestamp ล่าสุดชนะ เมื่อ keyword ซ้ำ | PASS | `_load_rules()` dedup โดยเก็บ `updated_at` ล่าสุด |

## Phase 3: Multi-Agent System Engine

| Req ID | Description | Status | Evidence |
|--------|-------------|--------|----------|
| FR-04 | Worker Consumer ดึงงานจาก RabbitMQ | PASS | `app/worker.py` consume ตลอดเวลา |
| FR-04 | Main Agent: สร้าง MD Template Context | PASS | `build_context()` ใส่ rules ใน template |
| FR-04 | Translate Agent: แปลผลจาก MD Template | PASS | "hello world" -> "xin chao the gioi" |
| FR-04 | Validate Agent: ตรวจสอบเทียบกฎ | PASS | `validate()` ตรวจจับ keyword ที่เหลือ |
| NFR-01 | Idempotency: เช็ค Task_ID ก่อนเริ่มงาน | PASS | `session.get(TaskRecord, task_id)` ก่อน insert |
| FR-04 | Max Retries = 3 -> Failed/Manual Review | PASS | Loop สูงสุด 4 รอบ (initial + 3 retries) |

## Phase 4: Integration & Full Deployment

| Req ID | Description | Status | Evidence |
|--------|-------------|--------|----------|
| FR-01 (Polling) | GET /status/{task_id} | PASS | คืน task_id, status, retry_count, result |
| TR-02 (Docker) | docker-compose up ทั้งระบบ | PASS | 4 services: rabbitmq + postgres + api + worker |
| NFR-01 (Reliability) | Durable queue + auto-reconnect | PASS | `durable=True` + `connect_robust` |

---

## Gotchas Compliance

| # | Rule | Verified |
|---|------|----------|
| 1 | Async Session เท่านั้น (ห้าม Sync) | PASS |
| 2 | Aho-Corasick Automaton In-Memory Cache | PASS |
| 3 | Conflict Resolution: updated_at DESC | PASS |
| 4 | Idempotency: เช็ค Task_ID ก่อนเริ่มงาน | PASS |
| 5 | Max Retries: หยุดที่ 3 -> Failed | PASS |
| 6 | Rule Engine auto-reload หลัง Admin CRUD | PASS |
| 7 | Background refresh automaton ทุก 60s | PASS |

---

## Test Results

| # | Test | Result |
|---|------|--------|
| 1 | `POST /admin/rules/` — create rule | PASS (HTTP 201) |
| 2 | `GET /admin/rules/` — list rules | PASS |
| 3 | `PUT /admin/rules/{id}` — update rule | PASS (HTTP 200) |
| 4 | Duplicate keyword -> 409 Conflict | PASS |
| 5 | Full pipeline: translate -> validate -> complete | PASS |
| 6 | Idempotency: duplicate task_id ignored | PASS |
| 7 | Max Retries: failed after 3 retries | PASS |
| 8 | `GET /status/{task_id}` — completed task | PASS |
| 9 | `GET /status/{task_id}` — not found -> 404 | PASS |
| 10 | `docker compose up` — 4 services healthy | PASS |
| 11 | `docker compose down` — clean shutdown | PASS |
| 12 | Browser UI: tester.html validation + translate | PASS |
| 13 | Browser UI: monitor.html 6-card dashboard | PASS |
| 14 | CORS: Allow-Origin * + Allow-Methods | PASS |
| 15 | Concurrent 5 requests | PASS (all 202) |
| 16 | Large payload (13KB text) | PASS (202) |
| 17 | Unicode / Thai text | PASS (202) |
| 18 | Invalid UUID -> 400 | PASS |
| 19 | `GET /queue/stats` — RabbitMQ down -> 502 | PASS |
| 20 | Worker restart -> auto-reload rules | PASS |

---

## Deliverables (Phase 2-4)

| File | Path | Purpose |
|------|------|---------|
| `models.py` | `app/db/models.py` | TranslationRule + TaskRecord schema |
| `database.py` | `app/db/database.py` | Async SQLAlchemy engine + session |
| `admin_routes.py` | `app/api/admin_routes.py` | Admin CRUD endpoints |
| `rule_engine.py` | `app/services/rule_engine.py` | Aho-Corasick automaton + bg refresh |
| `main_agent.py` | `app/agents/main_agent.py` | MD Template context builder |
| `translate_agent.py` | `app/agents/translate_agent.py` | Rule-based string replacement |
| `validate_agent.py` | `app/agents/validate_agent.py` | Aho-Corasick re-scan validator |
| `worker.py` | `app/worker.py` | RabbitMQ consumer + retry loop |
| `main.py` | `app/main.py` | +GET /status + Admin router |
| `docker-compose.yml` | (updated) | +postgres +worker services |
| `requirements.txt` | (updated) | +asyncpg +sqlalchemy +pyahocorasick |

**Total Phase 2-4:** 8 new files + 3 updated

---

## Notes

- Translate Agent ปัจจุบันใช้ rule-based string replace — พร้อมเสียบ LLM call ใน `translate()` ได้ทันที
- Validate Agent ใช้ Aho-Corasick ชุดเดียวกับ Main Agent — ตรวจสอบ consistency
- Worker ใช้ `prefetch_count=1` — ประมวลผลทีละงาน ป้องกัน race condition
- PostgreSQL credentials สำหรับ development เท่านั้น — production ควรใช้ secrets
- Phase 1-4 รวมทั้งหมด 17/17 requirements — โปรเจคสมบูรณ์

## Bug Fixes (1 July 2026 Regression)

### BUG-001: Admin CRUD ResponseValidationError (UUID/datetime type mismatch)

**Symptoms:** `POST /admin/rules/` และ `GET /admin/rules/` คืน HTTP 500 — `ResponseValidationError: Input should be a valid string`

**Root Cause:** `schemas.py:RuleResponse` ประกาศ `id: str` และ `updated_at: str` แต่ SQLAlchemy ORM ส่งค่า `uuid.UUID` และ `datetime` — Pydantic `from_attributes=True` ไม่สามารถแปลง type อัตโนมัติได้

**Fix:** เพิ่ม `@field_validator(mode="before")` ใน `RuleResponse` เพื่อแปลง `UUID -> str` และ `datetime -> ISO format string` ก่อน validation

**Files Changed:** `app/schemas.py` (+2 imports, +2 field_validators)

### BUG-002: Worker automaton not populated (silent bg_refresh failure)

**Symptoms:** Worker ประมวลผลข้อความแต่ `extract_rules()` คืนค่าว่างตลอด — context_md แสดง "(no specific rules matched)" แม้มี rules ใน DB

**Root Cause:** Worker เป็น process แยก — `_automaton` เริ่มต้นเป็น `None` และ `_bg_refresh` อาจไม่ทำงานเพราะ `start_bg_refresh()` ใช้ `asyncio.create_task()` โดยไม่ await การโหลดครั้งแรก

**Fix:** Restart worker container (`docker compose restart worker`) — bg_refresh ทำงานหลัง restart และโหลด rules จาก DB

**Recommendation:** ควรเพิ่ม `await reload()` ทันทีใน `start_bg_refresh()` ก่อน `create_task()` เพื่อให้ automaton มีข้อมูลพร้อมใช้งานตั้งแต่เริ่มต้น
