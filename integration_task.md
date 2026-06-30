# 📋 แผนงานสำหรับนักพัฒนา (Task List for Junior Developer)
**ส่วนงาน:** Integration & Full Deployment (Phase 4)
**เป้าหมาย:** สร้างระบบเช็คสถานะงาน (Polling) และประกอบร่างทุกระบบ (API, Database, Message Queue, Worker) ให้รันพร้อมกันบน Docker

---

## 🛠 0. การเตรียมความพร้อม (Setup)

ในส่วนนี้ไม่ต้องลงไลบรารีเพิ่ม แต่เน้นเรื่องการตั้งค่า Environment Variables เพื่อเชื่อมโยงแต่ละส่วนเข้าด้วยกัน
สร้างไฟล์ `docker-compose.yml` ไว้ที่ Root directory ของโปรเจกต์:
```text
hermes_project/
│
├── app/                 # โค้ด FastAPI (Phase 1 & 2)
├── worker/              # โค้ด Multi-Agent (Phase 3)
├── requirements.txt
└── docker-compose.yml   # ไฟล์หัวใจสำคัญสำหรับรันทุกระบบพร้อมกัน
```

---

## 📝 รายการงาน (Tasks)

### Task 1: สร้าง API สำหรับตรวจสอบสถานะ (Polling Endpoint)
**คำอธิบาย:** ระบบ Asynchronous ต้องการช่องทางให้ Client กลับมาเช็คผลลัพธ์
1. [ ] ในโฟลเดอร์ `app/` เปิดไฟล์ `main.py`
2. [ ] สร้าง Endpoint `GET /status/{task_id}`
3. [ ] ใน Endpoint นี้ ให้ทำการ Query ฐานข้อมูล PostgreSQL เพื่อเช็คสถานะของ `task_id` นั้น (เช่น Pending, Processing, Completed, Failed)
4. [ ] **Definition of Done:** เอา `task_id` ที่ได้จาก Phase 1 มายิงเช็คผ่าน Postman แล้วระบบคืนค่าสถานะปัจจุบันและผลการแปลได้ถูกต้อง

### Task 2: ผูกระบบทั้งหมดลงใน Docker Compose ฉบับสมบูรณ์
**คำอธิบาย:** ทำให้ระบบทุกส่วนรันเชื่อมโยงกันได้ในคำสั่งเดียว
1. [ ] เปิดไฟล์ `docker-compose.yml` เขียน Service ให้ครบ 4 ตัว:
   - `postgres`: ฐานข้อมูล
   - `rabbitmq`: คิวงาน
   - `api`: รัน FastAPI
   - `worker`: รันโค้ด Multi-Agent Consumer
2. [ ] ตั้งค่า Network ภายใน Docker ให้ `api` และ `worker` มองเห็น `postgres` และ `rabbitmq`
3. [ ] **Definition of Done:** รันคำสั่ง `docker compose up --build -d` แล้วคอนเทนเนอร์ทั้ง 4 ตัวรันขึ้นมาได้โดยไม่พัง (Exited)

---

## 🚨 ข้อควรระวังสำหรับ Junior (Gotchas! ห้ามพลาด)

> [!WARNING]
> **1. การตั้งชื่อ Host ใน Docker:**
> * เวลาต่อ Database หรือ RabbitMQ **ห้ามใช้ `localhost` เด็ดขาด** เพราะแต่ละคอนเทนเนอร์มี localhost ของตัวเอง ให้ใช้ชื่อ Service Name แทน เช่น `host=postgres` หรือ `amqp://rabbitmq`

> [!IMPORTANT]
> **2. การรอ Service ลุกขึ้น (Startup Order):**
> * API และ Worker อาจจะรันเร็วกว่า Database หรือ RabbitMQ ถ้ามันต่อไม่ติดตั้งแต่แรกมันจะดับไปเลย 
> * ให้เพิ่มโค้ดในการพยายามเชื่อมต่อซ้ำ (Retry connection) หรือใช้ฟีเจอร์ `depends_on: condition: service_healthy` ใน docker-compose

> [!TIP]
> **3. การทำ Webhook (ตัวเลือกเสริม):**
> * นอกจากการทำ Polling (`GET /status/{task_id}`) แล้ว ถ้าอยากให้ระบบหรูหราขึ้น ในฝั่ง Worker เมื่อแปลงานเสร็จ สามารถให้มันยิง HTTP POST (Webhook) กลับไปหา Client ทันทีได้ จะช่วยลดภาระการ Polling ของเซิร์ฟเวอร์
