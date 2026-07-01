# 🎯 กระดานสรุปความคืบหน้าโครงการ (Master Checklist)
**โครงการ:** ระบบแปลภาษาและจัดการเนื้อหาอัตโนมัติ (HermesTranslate)
**อ้างอิงจาก:** เอกสารข้อกำหนดความต้องการ (req.md / srs.md)

ตารางนี้ใช้สำหรับ **Project Manager หรือ Senior Developer** ในการติดตามและตรวจสอบความสำเร็จของระบบภาพรวม ว่าทำครบตาม Requirement ทุกข้อแล้วหรือยัง

---

## 🟢 Phase 1: API Gateway & Message Queue (Hermes Core)
- [x] **FR-01:** ระบบมี API (FastAPI) รองรับ Request ด้วยความเร็วสูง (Asynchronous)
- [x] **FR-01:** API สามารถสร้าง `Task_ID` (UUID) และคืนค่าให้ Client ได้ทันทีโดยไม่บล็อคระบบ
- [x] **FR-01:** ระบบโยนข้อมูลที่รับมา (Payload + Task_ID) ลง Message Queue (RabbitMQ) ได้สำเร็จ

## 🔵 Phase 2: Knowledge Base & Rule Management
- [x] **FR-02:** มีฐานข้อมูล PostgreSQL สำหรับเก็บข้อมูลกฎการแปล 
- [x] **TR-03 (Infrastructure):** เพิ่มเซอร์วิส PostgreSQL ใน docker-compose.yml พร้อมตั้งค่า Volumes ป้องกันข้อมูลสูญหาย และ Healthcheck
- [x] **FR-02:** มี API (Admin Routes) ให้ผู้ดูแลระบบสามารถเพิ่ม / ลด / แก้ไข กฎได้ (CRUD)
- [x] **FR-03:** มีฟังก์ชันคัดกรองคำโดยใช้อัลกอริทึม **Aho-Corasick** (สามารถจับ Exact Match และลด Token ได้จริง)
- [x] **FR-02 (Conflict):** หากพบกฎที่ขัดแย้งกัน ระบบเลือกใช้กฎที่มี Timestamp ล่าสุดเสมอ

## 🟠 Phase 3: Multi-Agent System Engine
- [x] **FR-04:** มี Worker Consumer คอยเฝ้าดึงงานจาก RabbitMQ มาทำงานเบื้องหลังตลอดเวลา
- [x] **FR-04:** โค้ดส่วน **Main Agent** สามารถเตรียมบริบท (Context) ใส่ใน MD Template ได้
- [x] **FR-04:** โค้ดส่วน **Translate Agent** สามารถแปลผลจาก MD Template ได้
- [x] **FR-04:** โค้ดส่วน **Validate Agent** สามารถตรวจสอบความถูกต้องเทียบกับกฎได้
- [x] **NFR-01 (Idempotency):** มีการเช็ค `Task_ID` ก่อนเริ่มงานทุกครั้ง ป้องกันการรัน AI เบิ้ล/ซ้ำซ้อน
- [x] **FR-04 (Max Retries):** หาก Validate ไม่ผ่าน ระบบสั่ง Retry ได้ และเมื่อครบ 3 ครั้งจะหยุด พร้อมเปลี่ยนสถานะเป็น "Failed / Manual Review" ทันที (ป้องกัน Infinite Loop)

## 🟣 Phase 4: Integration & Full Deployment
- [x] **FR-01 (Polling):** มี API `GET /status/{task_id}` ให้ Client สามารถดึงผลลัพธ์สุดท้ายหรือเช็คสถานะการทำงานได้
- [x] **TR-02 (Docker):** ระบบทั้งหมดสามารถรันร่วมกันได้สมบูรณ์ผ่านคำสั่ง `docker-compose up`
- [x] **NFR-01 (Reliability):** เมื่อ RabbitMQ หรือ API ดับไประยะสั้นๆ ระบบสามารถกลับมาทำงานต่อได้โดยที่ข้อมูลในคิวไม่สูญหาย

## 🟡 Phase Add-on: Web UI (Tester + Monitor)
- [x] **UI-01 (Tester):** หน้าเว็บ tester.html สำหรับกรอกข้อความภาษาไทยและส่งแปลผ่าน API — แสดง Task ID + Status
- [x] **UI-02 (Monitor):** หน้าเว็บ monitor.html สำหรับดูสถานะคิวงานแบบ Real-time (Polling ทุก 2 วินาที) — แสดง 6-card dashboard
- [x] **UI-03 (CORS):** ตั้งค่า CORS Middleware ให้ Browser-based UI ยิง API ข้าม origin ได้
- [x] **UI-04 (Static):** FastAPI serve static HTML files ผ่าน `/static/` mount
- [x] **UI-05 (Queue API):** API endpoint `GET /queue/stats` สำหรับ query RabbitMQ queue statistics
- [x] **UI-06 (WS + Live Result):** หน้า tester แสดงผลแปล AI (original/translated) ผ่าน WebSocket real-time + fallback HTTP polling + progress bar
- [x] **UI-07 (Cancel):** ปุ่มยกเลิก task ระหว่างแปล + API `POST /cancel/{task_id}`
- [x] **UI-08 (History):** localStorage history 20 รายการ + API `GET /history` — คลิกเรียกดู/โหลดซ้ำรายการเก่าได้
- [x] **BUG-001:** แก้ไข Admin CRUD ResponseValidationError — UUID/datetime type mismatch ใน `schemas.py:RuleResponse`
- [x] **BUG-002:** แก้ไข Worker automaton ไม่โหลด rules — restart worker + `start_bg_refresh` initialization
- [x] **UI-09 (Agent Console):** หน้าเว็บ agents.html สำหรับทดสอบ Agent ทั้ง 3 ตัว (Main/Translate/Validate) แบบ interactive console — 3 แท็บ + API `POST /agent/chat`
- [x] **UI-10 (LLM Agents):** เปลี่ยน Agent ทั้ง 3 เป็น LLM-powered ผ่าน Hermes Agent CLI + สร้าง 3 skills (translate-main/worker/checker) + fallback rule-based อัตโนมัติเมื่อไม่มี Hermes
- [x] **UI-11 (Teach):** ปุ่มสอน Agent ผ่าน UI + API `POST /agent/teach` — บันทึก feedback + สร้างกฎแปลใหม่ลง DB อัตโนมัติ

## 🟤 Phase Add-on: Hermes Agent Manager Dashboard
- [x] **MG-01 (Profiles):** สร้าง 3 Hermes profiles — `ht-main`, `ht-translate`, `ht-validate` — clone จาก default สำหรับจัดการแยก agent
- [x] **MG-02 (API):** สร้าง `app/hermes_manager.py` — 10 endpoints จัดการ dashboard lifecycle (start/stop/status/open), config (read/write), skills (list/install), chat
- [x] **MG-03 (Frontend):** สร้าง `static/hermes-manager.html` — SPA จัดการ 3 agents: start/stop dashboard, เปลี่ยน model, ดู/ติดตั้ง skills, แชทกับ agent
- [x] **MG-04 (Integration):** Register router ใน `app/main.py` + ทดสอบ end-to-end (start/stop/status/config/chat ผ่าน API)

**Status: All items complete (1 July 2026)**
