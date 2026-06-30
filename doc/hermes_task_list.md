# 📋 แผนงานสำหรับนักพัฒนา (Task List for Junior Developer)
**ส่วนงาน:** Hermes API Gateway & Message Queue (Phase 1)
**เป้าหมาย:** สร้างตัวรับ Request ด้วย FastAPI, คืนค่า Task ID ทันที (Asynchronous), และโยนงานลง Message Queue (RabbitMQ)

---

## 🛠 0. การเตรียมความพร้อม (Setup & Dependencies)

### 0.1 ติดตั้งไลบรารีที่จำเป็น (Dependencies)
รันคำสั่งนี้ใน Terminal เพื่อติดตั้งเครื่องมือหลัก:
```bash
pip install fastapi uvicorn pydantic aio-pika python-dotenv uuid
```

### 0.2 โครงสร้างโฟลเดอร์เริ่มต้น (Recommended Folder Structure)
ให้สร้างโฟลเดอร์ตามโครงสร้างนี้เพื่อความเป็นระเบียบ:
```text
hermes_project/
│
├── app/
│   ├── __init__.py
│   ├── main.py              # ตัวเปิดเซิร์ฟเวอร์ FastAPI
│   ├── schemas.py           # กำหนดรูปแบบข้อมูล (Pydantic)
│   ├── mq_publisher.py      # ตัวโยนข้อมูลลง RabbitMQ
│   └── config.py            # ดึงค่าจาก .env
│
├── requirements.txt         # รวมรายการไลบรารี
└── .env                     # ตั้งค่า Environment Variables (เช่น URL ของ RabbitMQ)
```

---

## 📝 รายการงาน (Tasks)

### Task 1: สร้าง API Endpoint พื้นฐาน (FastAPI)
**คำอธิบาย:** สร้าง API รับข้อมูลและคืนค่า `Task_ID` แบบทันที
1. [ ] สร้างไฟล์ `schemas.py` ใช้ **Pydantic** กำหนดรับข้อมูลที่มีฟิลด์ `text` (ข้อความที่ต้องการแปล)
2. [ ] สร้างไฟล์ `main.py` ตั้งค่า **FastAPI** 
3. [ ] สร้าง Endpoint `POST /translate/`
4. [ ] ภายใน Endpoint: เมื่อมีการยิง Request เข้ามา ให้ระบบสร้าง `Task_ID` (ใช้ `uuid.uuid4()`) 
5. [ ] **Definition of Done:** เมื่อยิง Request ผ่าน Postman หรือ Swagger ระบบต้องตอบกลับ HTTP 200/202 พร้อมกับ `{"task_id": "xxxx", "status": "pending"}` **ทันที**

### Task 2: เชื่อมต่อ Message Queue (RabbitMQ)
**คำอธิบาย:** เอาข้อมูลที่รับมา ไปโยนใส่คิวงานแบบเบื้องหลัง
1. [ ] สร้างไฟล์ `mq_publisher.py`
2. [ ] เขียนฟังก์ชัน `publish_task(task_id, text)` โดยใช้ไลบรารี **aio-pika** (เพื่อให้ทำงานแบบ Async ได้)
3. [ ] กลับไปที่ `main.py` นำฟังก์ชันนี้ไปเรียกใช้ภายใน `POST /translate/` (ต้องใช้ `await` ตอน Publish งานลงคิว)
4. [ ] **Definition of Done:** ยิง API แล้ว ข้อมูล `task_id` และ `text` ปรากฏในคิวของ RabbitMQ

### Task 3: สร้าง Docker สำหรับรันทดสอบ (Dockerization)
**คำอธิบาย:** แพคโปรเจกต์ลง Docker ให้ทำงานร่วมกับ RabbitMQ ได้
1. [ ] สร้างไฟล์ `Dockerfile` สำหรับรัน Python/FastAPI (ใช้ `uvicorn`)
2. [ ] สร้างไฟล์ `docker-compose.yml` ให้มี 2 Services:
   - `api`: โค้ด FastAPI ของเรา
   - `rabbitmq`: อิมเมจ `rabbitmq:3-management`
3. [ ] **Definition of Done:** สามารถรัน `docker compose up -d` แล้วทั้ง API และ RabbitMQ ทำงานได้โดยไม่ Error

---

## 🚨 ข้อควรระวังสำหรับ Junior (Gotchas! ห้ามพลาด)

> [!WARNING]
> **1. กฎเหล็ก Asynchronous:** 
> * ฟังก์ชันใน Endpoint หรือคิวงาน **ต้องใช้ `async def`** 
> * หากต้องการหน่วงเวลาตอนทดสอบโค้ด **ห้ามใช้ `time.sleep()` เด็ดขาด** เพราะจะทำให้เซิร์ฟเวอร์ค้าง (Blocking) ให้เปลี่ยนไปใช้ `await asyncio.sleep()` แทน

> [!IMPORTANT]
> **2. การตอบสนองทันที (Non-Blocking):**
> * API ตัวนี้มีหน้าที่แค่ "รับงาน -> สร้าง ID -> โยนลงคิว -> ตอบกลับผู้ใช้"
> * ห้ามเขียนโค้ดเพื่อรอให้ AI แปลผลเสร็จใน API Endpoint เด็ดขาด การรอผลลัพธ์เป็นหน้าที่ของระบบอื่น

> [!TIP]
> **3. การจัดการ Connection ของ Message Queue:**
> * การต่อ RabbitMQ ควรเปิด Connection ตอนเริ่มแอปพลิเคชัน (Startup event) และปิดตอนปิดแอป (Shutdown event) เพื่อป้องกันปัญหา Connection ค้างในระบบ
