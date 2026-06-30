# 📖 Manual Test Guide — HermesTranslate Phase 1

**ส่วนงาน:** API Gateway & Message Queue
**วันที่:** 30 มิถุนายน 2026

---

## Prerequisites
- Docker Desktop ทำงานอยู่
- Port 8000, 5672, 15672 ว่าง

---

## Test 1: Startup

```bash
cd D:\HermesTranslate\HermesTranslate
docker compose up -d
```

**Expected:** รอประมาณ 30 วินาที แล้ว `docker compose ps` แสดงทั้ง 2 services

```
NAME                         STATUS
hermestranslate-api-1        Up
hermestranslate-rabbitmq-1   Up (healthy)
```

---

## Test 2: API — Basic Request

```bash
curl -X POST http://localhost:8000/translate/ \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?"}'
```

**Expected:** HTTP 202

```json
{"task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "status": "pending"}
```

---

## Test 3: API — Unique Task IDs (Concurrency)

```bash
for i in 1 2 3; do
  curl -s -X POST http://localhost:8000/translate/ \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"Request $i\"}"
  echo ""
done
```

**Expected:** `task_id` ทั้ง 3 ตัวแตกต่างกันทั้งหมด

---

## Test 4: API — Validation (Missing Field)

```bash
curl -s -w "\nHTTP:%{http_code}\n" -X POST http://localhost:8000/translate/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected:** HTTP 422 Unprocessable Entity — แจ้งว่า field `text` required

---

## Test 5: RabbitMQ — Message Count

```bash
curl -s -u guest:guest http://localhost:15672/api/queues/%2F/translation_tasks
```

**Expected:** `"messages"` count > 0

หรือเปิด Browser:
- URL: `http://localhost:15672`
- Login: `guest` / `guest`
- Tab: Queues → `translation_tasks`

---

## Test 6: RabbitMQ — Message Content

```bash
curl -s -u guest:guest -X POST \
  "http://localhost:15672/api/queues/%2F/translation_tasks/get" \
  -H "Content-Type: application/json" \
  -d '{"count":1,"ackmode":"ack_requeue_true","encoding":"auto","truncate":50000}'
```

**Expected:** payload ประกอบด้วย `{"task_id": "...", "text": "..."}` ตรงกับที่ส่งเข้า API

---

## Test 7: API — Swagger Docs

เปิด Browser: `http://localhost:8000/docs`

**Expected:** Swagger UI แสดง `POST /translate/` พร้อม Request/Response schema

---

## Test 8: Shutdown

```bash
docker compose down
```

**Expected:** `docker ps` ไม่มี containers ของ HermesTranslate หลงเหลือ
