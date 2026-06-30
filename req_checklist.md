# HermesTranslate - Requirements Checklist

อ้างอิงจากข้อมูลจำเพาะระบบในไฟล์ `req.md`

## 1. System Infrastructure (โครงสร้างพื้นฐานและเทคโนโลยี)
- [ ] **API Gateway:** พัฒนาตัวรับ Request ด้วยภาษา Python โดยใช้ Asynchronous Framework (เช่น FastAPI)
- [ ] **Deployment:** จัดเตรียมและรัน `Hermes Main Agent` และ Worker ทั้งหมดบน Docker
- [ ] **Database:** ติดตั้งและตั้งค่า PostgreSQL สำหรับจัดเก็บสถานะงานและกฎการแปล

## 2. Core Workflow (การไหลของข้อมูลแบบ Asynchronous)
- [ ] **ระบบ Asynchronous API:** ตรวจสอบให้แน่ใจว่า API ไม่มีการทำงานแบบรอผลลัพธ์หน้าจอ (Non-blocking)
- [ ] **Step 1:** สร้าง Endpoint ให้หน้าบ้านส่งข้อมูลเข้า API
- [ ] **Step 2:** API สามารถคืนค่า `Task_ID` กลับให้หน้าบ้านได้ทันที
- [ ] **Step 2 (Queue):** API สามารถส่งข้อมูลงานลง Message Queue (เช่น RabbitMQ) ได้สำเร็จ
- [ ] **Step 3 (Polling/Webhook):** พัฒนาระบบให้หน้าบ้านนำ `Task_ID` มา Polling ถามสถานะ หรือรับการแจ้งเตือนผ่าน Webhook

## 3. Knowledge Base & Rule Management (ระบบสมองและกฎการสอน AI)
- [ ] **UI & DB:** สร้างหน้า Backoffice ให้ Admin จัดการ (เพิ่ม/ลด/แก้ไข) กฎเฉพาะทาง
- [ ] **DB Store:** จัดเก็บข้อมูลกฎทั้งหมดลงในฐานข้อมูล PostgreSQL
- [ ] **Rule Filtering:** ติดตั้งและใช้งานอัลกอริทึม Aho-Corasick สำหรับสแกนหาคำ (Exact Match) ในประโยค
- [ ] **Rule Filtering (Prompt):** ระบบสามารถดึงเฉพาะกฎที่ค้นพบเจอ ไปต่อท้ายใน Prompt เพื่อประหยัด Token
- [ ] **Conflict Resolution:** สร้างเงื่อนไขการจัดการข้อขัดแย้งของกฎ โดยให้ยึดกฎที่ถูกอัปเดตล่าสุด (Timestamp ล่าสุด) เป็นหลักเสมอ

## 4. Multi-Agent System Engine (กลไกการทำงานด้วย LangGraph)
- [ ] **LangGraph Setup:** กำหนดค่าและสร้าง State Machine ผ่าน LangGraph เพื่อใช้เป็นศูนย์กลางการทำงานของ Agent
- [ ] **Step 4.1 (Orchestrator):** `Hermes Main Agent` สามารถดึงงานจาก Message Queue ได้
- [ ] **Step 4.1 (Aho-Corasick):** `Hermes Main Agent` นำข้อความมาสแกนด้วย Aho-Corasick และทำ Dynamic Prompt Injection
- [ ] **Step 4.1 (Update State):** `Hermes Main Agent` สามารถอัปเดตสถานะงานลงใน LangGraph State
- [ ] **Step 4.2 (Creator):** `Sun Agent` รับคำสั่งจาก State และสร้างเนื้อหาออกมาในรูปแบบ Structured JSON ตาม Schema ที่กำหนดเป๊ะๆ
- [ ] **Step 4.3 (Validator):** `CheckWordAgent` ดึง JSON จาก State มาตรวจสอบความถูกต้อง โดยใช้กฎชุดเดียวกับ Hermes

## 5. Fail-safes & Fallback (ระบบป้องกันความพินาศ)
- [ ] **Max Retries (LangGraph):** หาก `CheckWordAgent` ตรวจพบข้อผิดพลาด จะต้องส่ง State กลับไปหา `Sun Agent` เพื่อให้แก้ไขใหม่
- [ ] **Max Retries (Limit):** จำกัดการส่งกลับไปแก้ไขให้ `Sun Agent` สูงสุดที่ 3 รอบเท่านั้น เพื่อป้องกัน Infinite Loop
- [ ] **Failed State:** หากต้องแก้ไขเกิน 3 รอบ ระบบจะต้องหยุดการทำงานทันที และเปลี่ยนสถานะเป็น "Failed/Manual Review"
- [ ] **Idempotency:** สร้างระบบตรวจเช็คความซ้ำซ้อนของ `Task_ID` ในทุกๆ Request เพื่อป้องกันการสั่งรัน Agent เบิ้ลเมื่อเกิดปัญหา Network
