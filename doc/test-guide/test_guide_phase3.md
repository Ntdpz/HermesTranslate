# 📖 Manual Test Guide — HermesTranslate Phase 3

**ส่วนงาน:** Multi-Agent System Engine
**วันที่:** 1 กรกฎาคม 2026

---

## Prerequisites

- Phase 1 และ 2 ทำงานได้สมบูรณ์ (API + RabbitMQ + PostgreSQL + Rule Engine)
- Docker Desktop ทำงานอยู่
- มีกฎการแปลอย่างน้อย 2-3 รายการในฐานข้อมูล (ผ่าน `POST /admin/rules`)

---

## Unit Tests (ไม่ต้องใช้ Docker)

### Test 1: Main Agent — build_context() ทำงานถูกต้องเมื่อมีกฎตรง

```python
# รันใน Python หรือผ่าน pytest
from app.agents.main_agent import build_context
ctx = build_context("test-1", "Hello world")
assert "Translation Task" in ctx
assert "Original Text" in ctx
assert "Matched Rules" in ctx
assert "Instructions" in ctx
```

**Expected:** Template มี 4 sections ครบ: Header, Original Text, Matched Rules, Instructions

---

### Test 2: Main Agent — build_context() จัดการกรณีไม่มีกฎตรง

```python
ctx = build_context("test-2", "No keywords here")
assert "no specific rules matched" in ctx
```

**Expected:** แสดงข้อความ "(no specific rules matched)" แทนที่จะ error

---

### Test 3: Translate Agent — translate() ใช้กฎแทนที่ keyword

```python
from app.agents.translate_agent import translate
# ให้ context_md ที่มีกฎ "Hello" → "สวัสดี"
result = translate(ctx)
assert "Hello" not in result  # keyword ต้องหายไป
assert "สวัสดี" in result     # replacement ต้องปรากฏ
```

**Expected:** `str.replace()` ทำงานถูกต้อง — keyword ถูกลบ replacement ถูกเพิ่ม

---

### Test 4: Translate Agent — translate() กรณี input ว่าง

```python
result = translate("")
assert result == ""
```

**Expected:** คืนค่า empty string ไม่ error

---

### Test 5: Validate Agent — validate() ผ่านเมื่อไม่มี keyword หลงเหลือ

```python
from app.agents.validate_agent import validate
result = validate("สวัสดี ชาวโลก")  # แปลครบ ไม่มี keyword หลง
assert result is True
```

**Expected:** `True` — ไม่มี keyword จากกฎหลงเหลือในข้อความ

---

### Test 6: Validate Agent — validate() ไม่ผ่านเมื่อมี keyword หลง

```python
result = validate("Hello world with AI")  # keyword ยังอยู่
assert result is False
```

**Expected:** `False` — พบ keyword จากกฎที่ยังไม่ได้แปล

---

### Test 7: Retry Logic — หยุดที่รอบ 4 (MAX_RETRIES=3)

```python
# จำลองกฎที่ "แปลแล้ว keyword ไม่หาย" (self-replace rule)
# เช่น rule: "Hello" → "Hello" ทำให้ validate ไม่ผ่านตลอด
# Worker ต้องวน 4 รอบ (1 ครั้งแรก + 3 retries) แล้วหยุด status="failed"
```

**Expected:** 
- Attempt 1: validate=False → retry
- Attempt 2: validate=False → retry  
- Attempt 3: validate=False → retry
- Attempt 4: validate=False → stop, status="failed"
- **ห้าม** run ต่อเกิน 4 รอบ (ป้องกัน infinite loop)

---

## Integration Tests (ต้องใช้ Docker)

### Test 8: Worker Startup

```bash
cd D:\HermesTranslate\HermesTranslate
docker compose up -d
```

**Expected:** `docker compose ps` แสดง 4 services:
```
NAME                          STATUS
hermestranslate-api-1         Up
hermestranslate-rabbitmq-1    Up (healthy)
hermestranslate-postgres-1    Up (healthy)
hermestranslate-worker-1      Up
```

---

### Test 9: End-to-End — ยิง API → Worker แปล → เช็คสถานะ

```bash
# 1. เพิ่มกฎแปล (ต้องทำก่อน)
curl -X POST http://localhost:8000/admin/rules \
  -H "Content-Type: application/json" \
  -d '{"keyword": "Hello", "rule_text": "Translate Hello to สวัสดี"}'

# 2. ส่งข้อความแปล
curl -X POST http://localhost:8000/translate/ \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'
# → {"task_id": "...", "status": "pending"}

# 3. รอ 5 วินาทีให้ Worker ประมวลผล

# 4. เช็คสถานะ
curl http://localhost:8000/status/{task_id}
```

**Expected:** Response ประกอบด้วย `status: "completed"` และ `result_text` ที่มี "สวัสดี" แทน "Hello"

---

### Test 10: Retry Scenario — งานที่แปลไม่ผ่าน

```bash
# เพิ่มกฎที่จงใจให้ validate ไม่ผ่าน
curl -X POST http://localhost:8000/admin/rules \
  -H "Content-Type: application/json" \
  -d '{"keyword": "testretry", "rule_text": "Keep as testretry"}'

# ส่งข้อความที่มี keyword นี้
curl -X POST http://localhost:8000/translate/ \
  -H "Content-Type: application/json" \
  -d '{"text": "testretry message"}'

# รอ ~15-30 วินาทีให้ retry loop ทำงานครบ 4 รอบ
# เช็คสถานะ
curl http://localhost:8000/status/{task_id}
```

**Expected:** `status: "failed"` และ `retry_count: 3`

---

### Test 11: Idempotency — ป้องกันการทำงานซ้ำ

```bash
# ใช้ RabbitMQ Management UI ส่งข้อความซ้ำด้วย task_id เดิม
# หรือใช้ curl:
curl -s -u guest:guest -X POST \
  "http://localhost:15672/api/exchanges/%2F/amq.default/publish" \
  -H "Content-Type: application/json" \
  -d '{"properties":{},"routing_key":"translation_tasks","payload":"{\"task_id\":\"SAME-ID-123\",\"text\":\"dup\"}","payload_encoding":"string"}'

# Worker ต้องเช็ค TaskRecord ก่อนทำงาน — ถ้า task_id มีอยู่แล้ว ข้ามทันที
```

**Expected:** ไม่เกิด duplicate record, ไม่เกิด duplicate processing

---

## Test 12: Shutdown

```bash
docker compose down
```

**Expected:** `docker ps` ไม่มี containers ของ HermesTranslate หลงเหลือ
