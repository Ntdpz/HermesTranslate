# 📖 Manual Test Guide — HermesTranslate (Phase 2-4)

**Phase 1 Guide:** `doc/test-guide/test_guide_phase1.md`
**วันที่:** 30 มิถุนายน 2026

---

## Prerequisites

- Phase 1 ผ่านทั้งหมด (API + RabbitMQ ทำงาน)
- Docker Desktop
- Port 5432, 8000, 5672, 15672 ว่าง

---

## Phase 2: Knowledge Base & Rule Management

### Test 2.1: Admin — Create Rule

```bash
curl -X POST http://localhost:8000/admin/rules/ \
  -H "Content-Type: application/json" \
  -d '{"keyword": "hello", "rule_text": "Translate hello to xin chao"}'
```

**Expected:** HTTP 201 Created
```json
{"id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "keyword": "hello", "rule_text": "Translate hello to xin chao", "updated_at": "2026-06-30T..."}
```

### Test 2.2: Admin — List All Rules

```bash
curl http://localhost:8000/admin/rules/
```

**Expected:** HTTP 200, JSON array มีกฎที่เพิ่มไว้ (เรียงตาม updated_at ล่าสุด)

### Test 2.3: Admin — Update Rule

```bash
curl -X PUT http://localhost:8000/admin/rules/<RULE_ID> \
  -H "Content-Type: application/json" \
  -d '{"rule_text": "Translate hello to sawasdee"}'
```

**Expected:** HTTP 200, `updated_at` เปลี่ยนเป็นเวลาล่าสุด

### Test 2.4: Admin — Duplicate Keyword (409)

```bash
curl -s -w "\nHTTP:%{http_code}\n" -X POST http://localhost:8000/admin/rules/ \
  -H "Content-Type: application/json" \
  -d '{"keyword": "hello", "rule_text": "duplicate"}'
```

**Expected:** HTTP 409 Conflict — `"detail": "Keyword 'hello' already exists"`

---

## Phase 3: Multi-Agent Pipeline

### Test 3.1: Full Translation Pipeline

```bash
# Step 1: Add rules
curl -X POST http://localhost:8000/admin/rules/ \
  -H "Content-Type: application/json" \
  -d '{"keyword": "hello", "rule_text": "Translate hello to xin chao"}'

curl -X POST http://localhost:8000/admin/rules/ \
  -H "Content-Type: application/json" \
  -d '{"keyword": "world", "rule_text": "Translate world to the gioi"}'

# Step 2: Submit translation task
curl -X POST http://localhost:8000/translate/ \
  -H "Content-Type: application/json" \
  -d '{"text": "hello world"}'
```

**Expected:** HTTP 202
```json
{"task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "status": "pending"}
```

### Test 3.2: Check Status (หลังรอ 1-2 วินาที)

```bash
curl http://localhost:8000/status/<TASK_ID>
```

**Expected:** HTTP 200
```json
{
  "task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "status": "completed",
  "retry_count": 0,
  "created_at": "2026-06-30T...",
  "result": "xin chao the gioi"
}
```

### Test 3.3: Idempotency — Duplicate Task_ID

```bash
# ส่ง task_id เดิมซ้ำผ่าน API
# Worker log ต้องแสดงว่าข้าม task นี้ (existing record found)
```

**Expected:** Worker ไม่สร้าง TaskRecord ซ้ำ — `status` ไม่เปลี่ยน

### Test 3.4: Max Retries — Fail Case

```bash
# Step 1: Add a rule with NO replacement (keyword stays in text)
curl -X POST http://localhost:8000/admin/rules/ \
  -H "Content-Type: application/json" \
  -d '{"keyword": "fail", "rule_text": "This rule has no translation target"}'

# Step 2: Submit text containing the keyword
curl -X POST http://localhost:8000/translate/ \
  -H "Content-Type: application/json" \
  -d '{"text": "fail forever"}'

# Step 3: Check status after ~3 retries
curl http://localhost:8000/status/<TASK_ID>
```

**Expected:**
```json
{"status": "failed", "retry_count": 3, "result": "..."}
```

---

## Phase 4: Integration & Deployment

### Test 4.1: Docker Compose — All Services

```bash
cd D:\HermesTranslate\HermesTranslate
docker compose up -d
docker compose ps
```

**Expected:** 4 services ทั้งหมด Up
```
NAME                          STATUS
hermestranslate-api-1         Up
hermestranslate-rabbitmq-1    Up (healthy)
hermestranslate-postgres-1    Up (healthy)
hermestranslate-worker-1      Up
```

### Test 4.2: GET /status — Task Not Found

```bash
curl -s -w "\nHTTP:%{http_code}\n" http://localhost:8000/status/nonexistent-id
```

**Expected:** HTTP 404 — `"detail": "Task not found"`

### Test 4.3: Swagger Docs (All Endpoints)

เปิด Browser: `http://localhost:8000/docs`

**Expected:** Swagger UI แสดง 5 endpoints:
- `POST /translate/`
- `GET /status/{task_id}`
- `POST /admin/rules/`
- `GET /admin/rules/`
- `PUT /admin/rules/{rule_id}`

### Test 4.4: RabbitMQ — Durable Queue Survival

```bash
docker compose restart rabbitmq
# ตรวจสอบว่าข้อมูลในคิวยังอยู่
curl -s -u guest:guest http://localhost:15672/api/queues/%2F/translation_tasks | grep messages
```

**Expected:** `"messages"` count เท่าเดิม (หรือมากกว่า) — ข้อมูลไม่หาย

### Test 4.5: PostgreSQL — Data Persistence

```bash
# เพิ่มกฎผ่าน API
curl -X POST http://localhost:8000/admin/rules/ \
  -H "Content-Type: application/json" \
  -d '{"keyword": "persist", "rule_text": "Persistence test"}'

# Restart PostgreSQL
docker compose restart postgres

# ดึงกฎทั้งหมด — ต้องยังมี persist อยู่
curl http://localhost:8000/admin/rules/ | grep persist
```

**Expected:** กฎ `persist` ยังอยู่หลัง restart

### Test 4.6: Shutdown

```bash
docker compose down
```

**Expected:** `docker ps` ไม่มี containers ของ HermesTranslate เหลือ

---

## Quick Smoke Test (One-liner)

```bash
# Start -> Add rules -> Translate -> Check -> Stop
docker compose up -d && sleep 10 && \
curl -s -X POST http://localhost:8000/admin/rules/ -H "Content-Type: application/json" -d '{"keyword":"hello","rule_text":"Translate hello to xin chao"}' && \
TID=$(curl -s -X POST http://localhost:8000/translate/ -H "Content-Type: application/json" -d '{"text":"hello"}' | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4) && \
sleep 3 && \
curl -s http://localhost:8000/status/$TID && \
echo "" && \
docker compose down
```
