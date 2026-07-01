# 📖 Manual Test Guide — HermesTranslate Phase 4

**ส่วนงาน:** Integration & Full Deployment
**วันที่:** 1 กรกฎาคม 2026

---

## Prerequisites

- Phase 1, 2, 3 ทำงานได้สมบูรณ์ (API + RabbitMQ + PostgreSQL + Multi-Agent)
- Docker Desktop ทำงานอยู่
- Port 8000, 5432, 5672, 15672 ว่าง
- รันจาก root directory: `D:\HermesTranslate\HermesTranslate`

---

## Test 1: Build Docker Images

```bash
cd D:\HermesTranslate\HermesTranslate
docker compose build
```

**Expected:** Build สำเร็จ — สร้าง image `hermestranslate-api` และ `hermestranslate-worker`
ไม่มี error ตอน `pip install` หรือ `COPY`

---

## Test 2: Start All Services

```bash
docker compose up -d
```

**Expected:** Containers เริ่มตามลำดับ:
1. postgres → healthy
2. rabbitmq → healthy
3. api → started
4. worker → started

---

## Test 3: Verify All Containers Running

```bash
docker compose ps
```

**Expected:**
```
NAME                         STATUS
hermestranslate-api-1        Up
hermestranslate-postgres-1   Up (healthy)
hermestranslate-rabbitmq-1   Up (healthy)
hermestranslate-worker-1     Up
```

4 services ทั้งหมด Up — postgres และ rabbitmq แสดง `(healthy)`

---

## Test 4: API — POST /translate/ (202 Accepted)

```bash
curl -s -w "\nHTTP:%{http_code}\n" -X POST http://localhost:8000/translate/ \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'
```

**Expected:**
```json
{"task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "status": "pending"}
HTTP:202
```

ได้รับ `task_id` (UUID v4) และ `status: "pending"` ทันที — ไม่ต้องรอแปลเสร็จ

---

## Test 5: GET /status/{task_id} — Task Completed

```bash
# ใช้ task_id จาก Test 4
curl -s http://localhost:8000/status/<TASK_ID> | python -m json.tool
```

**Expected:**
```json
{
    "task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "status": "completed",
    "retry_count": 0,
    "created_at": "2026-07-01T...",
    "result": "Hello world"
}
```

Response มีครบ 5 fields — `status` เป็น `completed` หรือ `failed` (ไม่ใช่ `pending`)

---

## Test 6: GET /status/{task_id} — Task Not Found (404)

```bash
curl -s -w "\nHTTP:%{http_code}\n" http://localhost:8000/status/nonexistent-id
```

**Expected:**
```json
{"detail": "Task not found"}
HTTP:404
```

---

## Test 7: Swagger Docs — All Endpoints

เปิด Browser: `http://localhost:8000/docs`

**Expected:** Swagger UI แสดง 5 endpoints:
- `POST /translate/`
- `GET /status/{task_id}`
- `POST /admin/rules/`
- `GET /admin/rules/`
- `PUT /admin/rules/{rule_id}`

ลองกด "Try it out" บน `POST /translate/` และ `GET /status/{task_id}` — ต้องทำงานได้

---

## Test 8: Worker Logs — No Errors

```bash
docker compose logs worker
```

**Expected:**
- ไม่มี Traceback หรือ ERROR
- มี log `RabbitMQ connection attempt` สำเร็จ (attempt 1)
- มี log การ consume message

---

## Test 9: RabbitMQ Management UI

เปิด Browser: `http://localhost:15672`
- Username: `guest`
- Password: `guest`

**Expected:**
- Queues tab → มี queue ชื่อ `translation_tasks` (durable)
- ถ้ามีงานค้าง → Messages ready > 0

---

## Test 10: RabbitMQ Durable Queue — Survive Restart

```bash
# 1. ส่งงานเข้าระบบ
curl -s -X POST http://localhost:8000/translate/ \
  -H "Content-Type: application/json" \
  -d '{"text": "test durability"}'

# 2. Restart RabbitMQ (worker จะ reconnect เอง)
docker compose restart rabbitmq

# 3. รอ worker reconnect และประมวลผล (~10s)
sleep 10

# 4. เช็คว่างานที่ค้างถูกประมวลผล
curl -s -u guest:guest http://localhost:15672/api/queues/%2F/translation_tasks | python -c "import sys,json; d=json.load(sys.stdin); print(f'messages_ready={d[\"messages_ready\"]}, messages_unacknowledged={d[\"messages_unacknowledged\"]}')"
```

**Expected:** `messages_ready=0` — งานในคิวถูก consume หมด ไม่มีหาย

---

## Test 11: PostgreSQL Data Persistence — Survive Restart

```bash
# 1. เพิ่มกฎผ่าน API
curl -s -X POST http://localhost:8000/admin/rules/ \
  -H "Content-Type: application/json" \
  -d '{"keyword": "persist_test", "rule_text": "Persistence verification"}'

# 2. Restart PostgreSQL
docker compose restart postgres

# 3. รอให้ api reconnect (~10s)
sleep 10

# 4. ดึงกฎทั้งหมด — ต้องมี persist_test
curl -s http://localhost:8000/admin/rules/ | python -c "import sys,json; rules=json.load(sys.stdin); found=[r for r in rules if r['keyword']=='persist_test']; print(f'Found: {len(found)} rule(s)'); assert found, 'Rule lost after restart!'"
```

**Expected:** `Found: 1 rule(s)` — กฎไม่หายหลัง restart

---

## Test 12: Full Shutdown

```bash
docker compose down
```

**Expected:**
```bash
docker compose ps
# → ไม่มี containers ของ HermesTranslate หลงเหลือ
```

---

## Quick Smoke Test (One-liner)

```bash
cd D:\HermesTranslate\HermesTranslate && \
docker compose up -d && sleep 10 && \
curl -s -X POST http://localhost:8000/translate/ -H "Content-Type: application/json" -d '{"text":"smoke test"}' && echo "" && \
TID=$(curl -s -X POST http://localhost:8000/translate/ -H "Content-Type: application/json" -d '{"text":"smoke"}' | python -c "import sys,json; print(json.load(sys.stdin)['task_id'])") && \
sleep 2 && \
echo "--- Status Check ---" && \
curl -s http://localhost:8000/status/$TID && echo "" && \
echo "--- 404 Check ---" && \
curl -s -w "\nHTTP:%{http_code}\n" http://localhost:8000/status/fake-id && \
echo "--- Swagger ---" && \
curl -s -o /dev/null -w "Swagger UI HTTP:%{http_code}\n" http://localhost:8000/docs && \
echo "--- Done ---" && \
docker compose down
```

**Expected:** All checks pass — HTTP 202, status completed, HTTP 404, Swagger 200, clean shutdown
