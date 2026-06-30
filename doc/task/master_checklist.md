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
- [ ] **FR-02:** มีฐานข้อมูล PostgreSQL สำหรับเก็บข้อมูลกฎการแปล 
- [ ] **TR-03 (Infrastructure):** เพิ่มเซอร์วิส PostgreSQL ใน docker-compose.yml พร้อมตั้งค่า Volumes ป้องกันข้อมูลสูญหาย และ Healthcheck
- [ ] **FR-02:** มี API (Admin Routes) ให้ผู้ดูแลระบบสามารถเพิ่ม / ลด / แก้ไข กฎได้ (CRUD)
- [ ] **FR-03:** มีฟังก์ชันคัดกรองคำโดยใช้อัลกอริทึม **Aho-Corasick** (สามารถจับ Exact Match และลด Token ได้จริง)
- [ ] **FR-02 (Conflict):** หากพบกฎที่ขัดแย้งกัน ระบบเลือกใช้กฎที่มี Timestamp ล่าสุดเสมอ

## 🟠 Phase 3: Multi-Agent System Engine
- [ ] **FR-04:** มี Worker Consumer คอยเฝ้าดึงงานจาก RabbitMQ มาทำงานเบื้องหลังตลอดเวลา
- [ ] **FR-04:** โค้ดส่วน **Main Agent** สามารถเตรียมบริบท (Context) ใส่ใน MD Template ได้
- [ ] **FR-04:** โค้ดส่วน **Translate Agent** สามารถแปลผลจาก MD Template ได้
- [ ] **FR-04:** โค้ดส่วน **Validate Agent** สามารถตรวจสอบความถูกต้องเทียบกับกฎได้
- [ ] **NFR-01 (Idempotency):** มีการเช็ค `Task_ID` ก่อนเริ่มงานทุกครั้ง ป้องกันการรัน AI เบิ้ล/ซ้ำซ้อน
- [ ] **FR-04 (Max Retries):** หาก Validate ไม่ผ่าน ระบบสั่ง Retry ได้ และเมื่อครบ 3 ครั้งจะหยุด พร้อมเปลี่ยนสถานะเป็น "Failed / Manual Review" ทันที (ป้องกัน Infinite Loop)

## 🟣 Phase 4: Integration & Full Deployment
- [ ] **FR-01 (Polling):** มี API `GET /status/{task_id}` ให้ Client สามารถดึงผลลัพธ์สุดท้ายหรือเช็คสถานะการทำงานได้
- [ ] **TR-02 (Docker):** ระบบทั้งหมดสามารถรันร่วมกันได้สมบูรณ์ผ่านคำสั่ง `docker-compose up`
- [ ] **NFR-01 (Reliability):** เมื่อ RabbitMQ หรือ API ดับไประยะสั้นๆ ระบบสามารถกลับมาทำงานต่อได้โดยที่ข้อมูลในคิวไม่สูญหาย
