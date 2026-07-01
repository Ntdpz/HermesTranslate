# 📋 แผนงานสำหรับนักพัฒนา (Task List for Junior Developer)
**ส่วนงาน:** Multi-Agent System Engine (Phase 3)
**เป้าหมาย:** สร้าง Worker คอยดึงงานจาก Message Queue, รันกระบวนการ 3 Agents (Orchestrator -> Creator -> Validator) ผ่าน MD Template, และทำระบบตีกลับ (Retry)

---

## 🛠 0. การเตรียมความพร้อม (Setup & Dependencies)

### 0.1 ติดตั้งไลบรารีที่จำเป็น
รันคำสั่งนี้ใน Terminal เพื่อติดตั้งเครื่องมือสำหรับ AI และ Template:
```bash
pip install openai langchain jinja2 aio-pika
```

### 0.2 โครงสร้างโฟลเดอร์เริ่มต้น (Recommended Folder Structure)
ส่วนนี้จะทำงานแยกเป็น Worker (รันอยู่เบื้องหลัง) ไม่ได้ผูกกับ FastAPI:
```text
hermes_project/
│
├── worker/
│   ├── mq_consumer.py         # ตัวรอรับงานจาก RabbitMQ
│   ├── agents/
│   │   ├── main_agent.py      # Orchestrator
│   │   ├── translate_agent.py # Creator
│   │   └── validate_agent.py  # Validator
│   └── templates/
│       └── instruction.md     # MD Template แม่แบบ
```

---

## 📝 รายการงาน (Tasks)

### Task 1: สร้าง Consumer ดึงงานจาก RabbitMQ
**คำอธิบาย:** ระบบที่คอยนั่งเฝ้าว่ามีงานใหม่เข้ามาในคิวหรือไม่
1. [x] สร้างไฟล์ `mq_consumer.py` ใช้ไลบรารี `aio-pika` 
2. [x] กำหนดให้รันแบบวนลูป (Event loop) รอรับข้อความ เมื่อได้ข้อความ ให้ดึง `task_id` และ `text` ออกมา
3. [x] **Definition of Done:** เมื่อลองรัน `python mq_consumer.py` มันจะต้องดึงข้อความที่ส่งค้างไว้ในคิว (จาก Phase 1) ออกมาปริ้นท์ (Print) โชว์บนหน้าจอได้

### Task 2: ประกอบร่างระบบ Multi-Agent
**คำอธิบาย:** สร้าง Agent 3 ตัวเพื่อรับส่งงานกัน
1. [x] **Main Agent:** เขียนโค้ดรับ `text` แล้วไปดึงกฎจาก `rule_engine` (จาก Phase 2) นำมาแทรกใส่ `instruction.md` (ใช้ `jinja2`)
2. [x] **Translate Agent:** นำไฟล์ MD Template ที่เติมข้อมูลแล้ว ยิงคำสั่งไปหา LLM (เช่น OpenAI API) เพื่อให้ทำการแปล
3. [x] **Validate Agent:** นำผลลัพธ์การแปล กลับไปถาม LLM อีกรอบ โดยอิงจากกฎเดิม ว่านักแปลทำงานถูกต้องตามกฎหรือไม่
4. [x] **Definition of Done:** ระบบสามารถรันต่อเนื่องตั้งแต่ Main -> Translate -> Validate และได้ผลลัพธ์การประเมินสุดท้ายออกมา

### Task 3: สร้างระบบ Fail-safes (Retry Logic)
**คำอธิบาย:** ระบบป้องกันความพินาศหาก AI แปลผิด
1. [x] เขียนลอจิกในฝั่ง Validate Agent: หากผลประเมินคือ "ไม่ผ่าน" ให้วนลูปกลับไปสั่ง Translate Agent ทำงานใหม่
2. [x] สร้างตัวนับ (Counter) จำวนครั้งที่แก้ไข
3. [x] หากครบ 3 ครั้งแล้วยังไม่ผ่าน ให้หยุดการทำงาน แล้วอัปเดตสถานะของ `task_id` ในฐานข้อมูลเป็น `Failed / Manual Review`
4. [x] **Definition of Done:** จำลองให้แปลผิดเสมอ ระบบจะต้องวนทำงานแค่ 3 รอบแล้วหยุดทันที

---

## 🚨 ข้อควรระวังสำหรับ Junior (Gotchas! ห้ามพลาด)

> [!WARNING]
> **1. ป้องกันวงจรอุบาทว์ (Infinite Loop):**
> * ลอจิกการนับรอบ Retry สำคัญมาก ห้ามลืมเพิ่มค่าตัวแปร `retry_count += 1` เด็ดขาด มิฉะนั้นระบบจะกินเงิน API ไม่หยุดจนกว่าเงินจะหมด (Token exhaustion)

> [!IMPORTANT]
> **2. การออกแบบ MD Template:**
> * ตัว Template ควรเขียนในรูปแบบที่ชัดเจนและแยกส่วน เช่น `<Rule>` และ `<Input>` เพื่อให้ AI ทำงานได้ง่าย ไม่สับสนข้อมูล
> * ให้พิมพ์บริบท (Context) เท่าที่จำเป็น เพื่อเป็นการประหยัด Token

> [!TIP]
> **3. การป้องกันการทำงานซ้ำ (Idempotency):**
> * ก่อนที่ Consumer จะเริ่มรันงาน ควรอ่าน Database เช็คดูก่อนว่า `task_id` นี้ถูกประมวลผลไปแล้วหรือยัง เพื่อป้องกันระบบรันซ้ำกรณีที่เน็ตเวิร์คกระตุก
