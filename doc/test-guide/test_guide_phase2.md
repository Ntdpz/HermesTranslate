# Manual Test Guide — HermesTranslate Phase 2

**ส่วนงาน:** Knowledge Base & Rule Management
**วันที่:** 1 กรกฎาคม 2026

---

## Prerequisites
- Docker Desktop ทำงานอยู่
- Port 5432, 8000, 5672, 15672 ว่าง
- Phase 1 services up (RabbitMQ + API)

---

## Test 1: Startup — PostgreSQL + RabbitMQ

```bash
cd D:\HermesTranslate\HermesTranslate
docker compose up -d postgres rabbitmq
```

รอ 15-20 วินาทีให้ PostgreSQL healthy:

```bash
docker compose ps
```

**Expected:**
```
NAME                         STATUS
hermestranslate-postgres-1   Up (healthy)
hermestranslate-rabbitmq-1   Up (healthy)
```

---

## Test 2: Alembic Migration — Status

```bash
cd D:\HermesTranslate\HermesTranslate
alembic current
```

**Expected:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
868d6fdbe851 (head)
```

---

## Test 3: Alembic — Create Initial Tables

หากยังไม่เคยรัน migration:

```bash
alembic upgrade head
```

**Expected:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> 868d6fdbe851, initial
```

---

## Test 4: Alembic — Verify Tables Exist

```bash
docker exec hermestranslate-postgres-1 psql -U hermes -d hermes_translate -c "\dt"
```

**Expected:**
```
       Name        | Type  | Owner
-------------------+-------+--------
 alembic_version   | table | hermes
 task_records      | table | hermes
 translation_rules | table | hermes
(3 rows)
```

---

## Test 5: translation_rules — Column Verification

```bash
docker exec hermestranslate-postgres-1 psql -U hermes -d hermes_translate -c "\d translation_rules"
```

**Expected:**

| Column | Type | Constraints |
|--------|------|-------------|
| id | uuid | NOT NULL, PK |
| keyword | character varying(255) | NOT NULL, UNIQUE INDEX |
| rule_text | text | NOT NULL |
| updated_at | timestamp with time zone | NOT NULL |

---

## Test 6: task_records — Column Verification

```bash
docker exec hermestranslate-postgres-1 psql -U hermes -d hermes_translate -c "\d task_records"
```

**Expected:**

| Column | Type | Constraints |
|--------|------|-------------|
| task_id | character varying(36) | NOT NULL, PK |
| status | character varying(20) | NOT NULL |
| retry_count | integer | NOT NULL |
| created_at | timestamp with time zone | NOT NULL |
| original_text | text | nullable |
| context_md | text | nullable |
| result_text | text | nullable |

---

## Test 7: Alembic — Downgrade / Upgrade Cycle

```bash
# ลบ tables ทั้งหมด
alembic downgrade -1

# ตรวจสอบว่า tables หายไป
docker exec hermestranslate-postgres-1 psql -U hermes -d hermes_translate -c "\dt"

# สร้าง tables กลับขึ้นมาใหม่
alembic upgrade head

# ตรวจสอบว่า tables กลับมา
docker exec hermestranslate-postgres-1 psql -U hermes -d hermes_translate -c "\dt"
```

**Expected after downgrade:** เหลือแค่ `alembic_version` (เนื่องจาก alembic เก็บ version ไว้เสมอ)
**Expected after upgrade:** ทั้ง 3 tables (`alembic_version`, `task_records`, `translation_rules`) กลับมา

---

## Test 8: Admin API — Create Rule

```bash
curl -s -X POST http://localhost:8000/admin/rules \
  -H "Content-Type: application/json" \
  -d '{"keyword": "test_keyword", "rule_text": "Translate this as TEST"}'
```

**Expected:** HTTP 201 — returns rule object with `id` (UUID), `keyword`, `rule_text`, `updated_at`

---

## Test 9: Admin API — List Rules

```bash
curl -s http://localhost:8000/admin/rules
```

**Expected:** HTTP 200 — array of rules, includes the rule created in Test 8

---

## Test 10: Admin API — Update Rule

```bash
# Replace <rule_id> with actual UUID from Test 8
curl -s -X PUT http://localhost:8000/admin/rules/<rule_id> \
  -H "Content-Type: application/json" \
  -d '{"keyword": "test_keyword", "rule_text": "Updated translation rule"}'
```

**Expected:** HTTP 200 — `rule_text` changed, `updated_at` refreshed

---

## Test 11: Admin API — Delete Rule

```bash
# Replace <rule_id> with actual UUID
curl -s -X DELETE http://localhost:8000/admin/rules/<rule_id>
```

**Expected:** HTTP 204 — rule removed from database

---

## Test 12: Aho-Corasick — Keyword Filtering

```bash
# สร้างกฎก่อน
curl -s -X POST http://localhost:8000/admin/rules \
  -H "Content-Type: application/json" \
  -d '{"keyword": "kotlin", "rule_text": "Use Java conventions for Kotlin"}'

# ทดสอบ filtering (ต้องมี endpoint หรือ script)
python -c "
import asyncio
from app.services.rule_engine import extract_rules
print(extract_rules('Kotlin is a modern language'))
"
```

**Expected:** คืนค่า rule ที่มี keyword `kotlin` (case-insensitive match ตาม implementation)

---

## Test 13: Shutdown

```bash
docker compose down
```

**Expected:** `docker ps` ไม่มี containers ของ HermesTranslate หลงเหลือ

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `alembic` command not found | `pip install alembic` |
| Connection refused (PostgreSQL) | รัน `docker compose up -d postgres` และรอ 15 วินาที |
| Migration ล้มเหลวเพราะ table มีอยู่แล้ว | รัน `alembic downgrade base` แล้ว `alembic upgrade head` ใหม่ |
| `docker compose` ไม่รู้จักคำสั่ง | ใช้ `docker-compose` (v1) หรืออัปเกรด Docker Desktop |
