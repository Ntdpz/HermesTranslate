# 📖 Manual Test Guide — HermesTranslate UI (Tester + Monitor)

> **DEPRECATED (2026-07-01):** `tester.html` และ `monitor.html` ถูกลบออกจากโปรเจคแล้ว Tests 1-8 และ 12 ไม่สามารถรันได้อีกต่อไป Tests 9-11, 13 ยังคง valid

**ส่วนงาน:** Web UI — Translation Tester & Queue Monitor
**วันที่:** 1 กรกฎาคม 2026 (Updated: 1 กรกฎาคม 2026 — UI files removed)

---

## Prerequisites

- Phase 1-4 ทำงานได้สมบูรณ์ (API + RabbitMQ + PostgreSQL + Worker)
- Docker Desktop ทำงานอยู่
- เบราว์เซอร์ที่รองรับ JavaScript (Chrome/Firefox/Edge)
- Port 8000, 15672 ว่าง
- รันจาก root directory: `D:\HermesTranslate\HermesTranslate`

---

## Test 1: Translation Tester — ส่งข้อความแปล

เปิด Browser: `http://localhost:8000/static/tester.html`

1. ใส่ข้อความใน textarea เช่น `สวัสดีชาวโลก`
2. กดปุ่ม "แปลภาษา"

**Expected:**
- ปุ่มเปลี่ยนเป็น "กำลังส่ง..." (disabled)
- หลังเสร็จ → แสดง Card ผลลัพธ์:
  - Task ID: UUID v4 (เช่น `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
  - Status: `pending`
- ปุ่มกลับมาเป็น "แปลภาษา" (enabled)

---

## Test 2: Translation Tester — Validation (Input ว่าง)

เปิด Browser: `http://localhost:8000/static/tester.html`

1. ปล่อย textarea ว่าง
2. กดปุ่ม "แปลภาษา"

**Expected:**
- แสดง error สีแดง: "กรุณากรอกข้อความก่อนกดแปล"
- ไม่มีการยิง API (ตรวจสอบจาก Network tab)

---

## Test 3: Translation Tester — ส่งผ่าน Ctrl+Enter

เปิด Browser: `http://localhost:8000/static/tester.html`

1. ใส่ข้อความใน textarea
2. กด `Ctrl+Enter` (หรือ `Cmd+Enter` บน Mac)

**Expected:** ทำงานเหมือนกดปุ่ม — แสดง Task ID และ Status

---

## Test 4: Translation Tester — API Error Handling

1. หยุด api container: `docker compose stop api`
2. รีเฟรช `tester.html` ใน Browser
3. ใส่ข้อความแล้วกด "แปลภาษา"

**Expected:** แสดง error "เกิดข้อผิดพลาด: Failed to fetch" (หรือคล้ายกัน)
- ไม่แสดง Task ID การ์ด

4. เริ่ม api ใหม่: `docker compose start api`
5. ทดสอบส่งอีกครั้ง — ต้องทำงานปกติ

---

## Test 5: Monitor Dashboard — โหลดหน้าเว็บ

เปิด Browser: `http://localhost:8000/static/monitor.html`

**Expected:**
- Header: "HermesTranslate Queue Monitor"
- จุดสถานะสีเขียว + "เชื่อมต่ออยู่"
- การ์ด 6 ใบ:
  - Total Messages
  - Ready (Pending)
  - Unacked (Processing)
  - Consumer (Worker)
  - Publish Rate (msg/s)
  - Deliver Rate (msg/s)
- Footer: "Last update: HH:MM:SS"

---

## Test 6: Monitor Dashboard — Consumer Active

**Expected:**
- การ์ด Consumer → ตัวเลขสีเขียว (≥ 1)
- ข้อความ "Worker ทำงานปกติ (active)"

---

## Test 7: Monitor Dashboard — No Worker

1. หยุด worker: `docker compose stop worker`
2. รอดูหน้า Monitor (refresh อัตโนมัติทุก 2 วิ)

**Expected:**
- การ์ด Consumer → ตัวเลขสีแดง (0)
- ข้อความ "ไม่มี Worker — ตรวจสอบ docker-compose"

3. เริ่ม worker ใหม่: `docker compose start worker`
4. ภายใน 2 วิ → กลับเป็นสีเขียว

---

## Test 8: Monitor Dashboard — Message Flow

1. เปิด `monitor.html` และ `tester.html` คนละแท็บ
2. ยิงแปลหลายๆครั้งใน tester.html
3. สังเกต monitor.html

**Expected:**
- Ready → เพิ่มขึ้นตอนส่งงาน
- Ready → ลดลงเมื่อ worker consume
- Unacked → เพิ่มชั่วคราวตอน worker กำลังทำงาน
- Publish Rate / Deliver Rate → มีค่าตามจริง

---

## Test 9: GET /queue/stats — Direct API

```bash
curl -s http://localhost:8000/queue/stats | python -m json.tool
```

**Expected:**
```json
{
    "queue_name": "translation_tasks",
    "messages_ready": 0,
    "messages_unacked": 0,
    "messages_total": 0,
    "consumers": 1,
    "publish_rate": 0.0,
    "deliver_rate": 0.0
}
```

Response มีครบ 7 fields — `consumers` ≥ 1 เมื่อ worker รันอยู่

---

## Test 10: GET /queue/stats — RabbitMQ Down (Graceful)

```bash
# 1. หยุด RabbitMQ
docker compose stop rabbitmq

# 2. ยิง API
curl -s -w "\nHTTP:%{http_code}\n" http://localhost:8000/queue/stats
```

**Expected:**
```json
{"detail": "Unable to reach RabbitMQ Management API"}
HTTP:502
```

ระบบไม่ crash — ตอบ 502 พร้อม error message

```bash
docker compose start rabbitmq
```

---

## Test 11: CORS — Cross-Origin Allowed

```bash
curl -s -I -X OPTIONS http://localhost:8000/translate/ \
  -H "Origin: http://example.com" \
  -H "Access-Control-Request-Method: POST"
```

**Expected:**
```
HTTP/1.1 200 OK
access-control-allow-origin: *
access-control-allow-methods: *
```

---

## Test 12: Static Files — Both Pages Accessible

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/static/tester.html
# Expected: 200

curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/static/monitor.html
# Expected: 200
```

---

## Test 13: OpenAPI Schema — Includes New Endpoint

```bash
curl -s http://localhost:8000/openapi.json | python -c "import sys,json; print([p for p in json.load(sys.stdin)['paths']])"
```

**Expected:** `['/admin/rules/', '/admin/rules/{rule_id}', '/translate/', '/status/{task_id}', '/queue/stats']`

มี `/queue/stats` เพิ่มมาจาก Phase 4

---

## Quick Smoke Test (One-liner)

```bash
cd D:\HermesTranslate\HermesTranslate && \
echo "=== Tester ===" && \
curl -s -o /dev/null -w "tester.html HTTP:%{http_code}\n" http://localhost:8000/static/tester.html && \
echo "=== Monitor ===" && \
curl -s -o /dev/null -w "monitor.html HTTP:%{http_code}\n" http://localhost:8000/static/monitor.html && \
echo "=== Queue Stats ===" && \
curl -s http://localhost:8000/queue/stats | python -c "import sys,json; d=json.load(sys.stdin); print(f'consumers={d[\"consumers\"]}, queue={d[\"queue_name\"]}')" && \
echo "=== Translate ===" && \
curl -s -X POST http://localhost:8000/translate/ -H "Content-Type: application/json" -d '{"text":"smoke"}' && echo "" && \
echo "=== All Pass ==="
```

**Expected:** HTTP 200 ทั้งคู่, consumers ≥ 1, translate ตอบ 202
