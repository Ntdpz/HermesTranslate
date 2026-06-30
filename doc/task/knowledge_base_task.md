# 📋 แผนงานสำหรับนักพัฒนา (Task List for Junior Developer)
**ส่วนงาน:** Knowledge Base & Rule Management (Phase 2)
**เป้าหมาย:** สร้างระบบฐานข้อมูล PostgreSQL สำหรับเก็บกฎการแปล, สร้าง API สำหรับ Admin, และเขียนลอจิกคัดกรองคำด้วย Aho-Corasick

---

## 🛠 0. การเตรียมความพร้อม (Setup & Dependencies)

### 0.1 ติดตั้งไลบรารีที่จำเป็น
รันคำสั่งนี้ใน Terminal เพื่อติดตั้งเครื่องมือสำหรับ Database และ Algorithm:
```bash
pip install asyncpg sqlalchemy alembic ahocorasick-python
```

### 0.2 โครงสร้างโฟลเดอร์เริ่มต้น (Recommended Folder Structure)
ทำต่อยอดจากโปรเจกต์เดิม โดยเพิ่มส่วนของ Database และ Rule Engine:
```text
hermes_project/
│
├── app/
│   ├── api/
│   │   └── admin_routes.py    # API สำหรับให้ Admin เพิ่ม/ลด กฎ
│   ├── db/
│   │   ├── database.py        # โค้ดเชื่อมต่อ PostgreSQL
│   │   └── models.py          # กำหนด Schema โครงสร้างตาราง
│   └── services/
│       └── rule_engine.py     # อัลกอริทึม Aho-Corasick สำหรับคัดกรองคำ
```

---

## 📝 รายการงาน (Tasks)

### Task 1: ตั้งค่าการเชื่อมต่อฐานข้อมูล (PostgreSQL)
**คำอธิบาย:** สร้างตารางเพื่อเก็บข้อมูล "กฎการแปลและคำศัพท์"
1. [ ] เพิ่มเซอร์วิส PostgreSQL ลงใน docker-compose.yml โดยต้องตั้งค่า volumes (เก็บข้อมูลถาวร) และ healthcheck (รอ DB พร้อม)
2. [ ] ในไฟล์ `models.py` สร้างตาราง `TranslationRule` (ต้องมีฟิลด์: `id`, `keyword`, `rule_text`, `updated_at`)
3. [ ] ในไฟล์ `database.py` เขียนฟังก์ชันเชื่อมต่อ DB แบบ Asynchronous (ใช้ `SQLAlchemy` + `asyncpg`)
4. [ ] **Definition of Done:** สามารถใช้คำสั่งสร้างตาราง (Migration/Alembic) ลง PostgreSQL ได้สำเร็จ

### Task 2: สร้าง API สำหรับ Administrator (CRUD)
**คำอธิบาย:** ทำช่องทางให้ Admin สามารถเข้ามาแก้ไขกฎได้
1. [ ] สร้าง Endpoint `POST /admin/rules` สำหรับเพิ่มกฎใหม่
2. [ ] สร้าง Endpoint `GET /admin/rules` สำหรับดูรายการกฎทั้งหมด
3. [ ] สร้าง Endpoint `PUT /admin/rules/{id}` สำหรับแก้ไขกฎ
4. [ ] **Definition of Done:** ยิง API ผ่าน Postman เพื่อเพิ่ม แก้ไข และดึงข้อมูลกฎจากตารางได้ถูกต้อง

### Task 3: ระบบคัดกรองคำ (Aho-Corasick Filtering)
**คำอธิบาย:** นำประโยคของ User มาแสกนหากฎที่ตรงกันอย่างรวดเร็ว
1. [ ] ในไฟล์ `rule_engine.py` เขียนคลาสหรือฟังก์ชันที่โหลดข้อมูลกฎจาก Database เข้ามาสร้างเป็น `Automaton` (จากไลบรารี `ahocorasick`)
2. [ ] เขียนฟังก์ชัน `extract_rules(text)` ที่รับข้อความยาวๆ แล้วรีเทิร์นกลับมาเฉพาะกฎที่มี Keyword ปรากฏในข้อความ (Exact Match)
3. [ ] **Definition of Done:** เขียนสคริปต์เทสสั้นๆ ลองโยนประโยคยาวๆ เข้าไป ฟังก์ชันต้องคืนค่ากฎที่เกี่ยวข้องออกมาได้ถูกต้องและรวดเร็ว

---

## 🚨 ข้อควรระวังสำหรับ Junior (Gotchas! ห้ามพลาด)

> [!WARNING]
> **1. การเชื่อมต่อ Database แบบ Async:**
> * การ Query ข้อมูลใน FastAPI **ต้องใช้ Async Session** ห้ามใช้ Sync Session ปกติเพราะจะทำให้ระบบช้าและเกิดคอขวด (Bottleneck)

> [!IMPORTANT]
> **2. กฎเกณฑ์ที่ขัดแย้งกัน (Conflict Resolution):**
> * หากแสกนแล้วพบว่า Keyword 2 ตัวดึงกฎที่ขัดแย้งกันมา ให้ยึดกฎที่มีค่า `updated_at` (Timestamp) ล่าสุดเป็นหลักเสมอ

> [!TIP]
> **3. การโหลด Aho-Corasick:**
> * อัลกอริทึม Aho-Corasick จะทำงานเร็วก็ต่อเมื่อสร้าง Automaton ไว้ล่วงหน้าในหน่วยความจำ ไม่ควรดึงข้อมูลจาก DB มาสร้าง Automaton ใหม่ทุกครั้งที่มี Request เข้ามา (ควรทำเป็น In-memory Cache และอัปเดตเมื่อ Admin แก้กฎ)
