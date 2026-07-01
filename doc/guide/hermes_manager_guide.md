# 📖 User Guide — Hermes Agent Manager

**ส่วนงาน:** จัดการ 3 Hermes Agent dashboards (Main / Translate / Validate)  
**วันที่:** 1 กรกฎาคม 2026

---

## ภาพรวม

Hermes Agent Manager ช่วยให้คุณควบคุม Hermes Agent ทั้ง 3 ตัวแยกจากกันผ่าน Web UI ตัวเดียว — start/stop dashboard, เปลี่ยน model, ดู skills, คุยกับ agent — โดยไม่ต้องเปิด terminal

| Agent | Profile | Port | Dashboard URL |
|---|---|---|---|
| Main | ht-main | 9120 | http://127.0.0.1:9120 |
| Translate | ht-translate | 9121 | http://127.0.0.1:9121 |
| Validate | ht-validate | 9122 | http://127.0.0.1:9122 |

---

## วิธีเปิดใช้งาน

### Step 1: Restart API Server (ครั้งแรก)

หลังจาก deploy ครั้งแรก routes `/hermes/*` ยังไม่โหลด ต้อง restart:

```bash
cd D:\HermesTranslate\HermesTranslate

# ถ้าใช้ Docker
docker compose restart api

# ถ้ารัน local
# Ctrl+C แล้ว start ใหม่:
uvicorn app.main:app --reload --port 8000
```

### Step 2: เปิด UI

Browser: `http://localhost:8000/static/hermes-manager.html`

---

## ฟีเจอร์ทั้งหมด

### 1. Start/Stop Dashboard

| ปุ่ม | ฟังก์ชัน |
|---|---|
| **[Start]** | เริ่ม dashboard บน port ของ agent นั้น (9120/9121/9122) |
| **[Stop]** | หยุด dashboard |
| **[Open]** | เปิด tab ใหม่ไปยัง dashboard URL |

สถานะอัปเดต auto ทุก 4 วินาที:
- 🟢 **Running** — dashboard พร้อมใช้งาน
- 🔴 **Stopped** — dashboard หยุดทำงาน

### 2. เปลี่ยน Model

1. กด **[Change Model]**
2. เลือก model จาก dropdown (deepseek, claude, gpt-4o, gemini, ฯลฯ)
3. (optional) แก้ provider
4. กด **Save**

⚠️ ต้อง restart dashboard ถึงจะใช้ model ใหม่

### 3. Skills

1. กด **[Skills]**
2. ดูรายชื่อ skills ทั้งหมดที่ติดตั้งอยู่
3. พิมพ์ skill ID ในช่อง → กด **Install** เพื่อติดตั้ง skill ใหม่

### 4. Chat กับ Agent

1. กด **[Chat]**
2. พิมพ์ข้อความ → กด **Send** (หรือ Ctrl+Enter)
3. อ่านผลลัพธ์ใน terminal output

---

## API Endpoints (สำหรับ Developer)

| Method | Path | คำอธิบาย |
|---|---|---|
| GET | `/hermes/dashboard/status` | สถานะทั้ง 3 dashboard |
| POST | `/hermes/dashboard/start/{agent}` | start dashboard (main/translate/validate) |
| POST | `/hermes/dashboard/stop/{agent}` | stop dashboard |
| POST | `/hermes/dashboard/open/{agent}` | return URL dashboard |
| GET | `/hermes/config/{agent}` | อ่าน config (model, provider) |
| POST | `/hermes/config/{agent}` | แก้ config `{"model":"...","provider":"..."}` |
| GET | `/hermes/config/{agent}/models` | list models ที่รู้จัก |
| GET | `/hermes/skills/{agent}` | list skills ทั้งหมด |
| POST | `/hermes/skills/{agent}/install` | install skill `{"skill_id":"..."}` |
| POST | `/hermes/chat/{agent}` | คุยกับ agent `{"text":"..."}` |

### ตัวอย่าง curl

```bash
# ดูสถานะ
curl http://localhost:8000/hermes/dashboard/status

# start main dashboard
curl -X POST http://localhost:8000/hermes/dashboard/start/main

# เปลี่ยน model ของ Translate Agent
curl -X POST http://localhost:8000/hermes/config/translate \
  -H "Content-Type: application/json" \
  -d '{"model":"anthropic/claude-sonnet-4"}'

# คุยกับ Main Agent
curl -X POST http://localhost:8000/hermes/chat/main \
  -H "Content-Type: application/json" \
  -d '{"text":"ขอ Rule ที่ใช้แปลทั้งหมด"}'
```

---

## Profiles — ภายใน

3 profiles เก็บที่ `%APPDATA%\hermes\profiles\`:

```
ht-main\       → config.yaml, .env, SOUL.md, skills/
ht-translate\  → config.yaml, .env, SOUL.md, skills/
ht-validate\   → config.yaml, .env, SOUL.md, skills/
```

แต่ละ profile ตั้งค่า model, API key, toolsets แยกจากกันได้อิสระ

### ตรวจสอบ profiles

```bash
hermes profile list
```

### แก้ config โดยตรง

```bash
# ผ่าน CLI
hermes -p ht-main config set model.default "anthropic/claude-sonnet-4"

# หรือแก้ไฟล์ตรงๆ
notepad %APPDATA%\hermes\profiles\ht-main\config.yaml
```

---

## Troubleshooting

| ปัญหา | วิธีแก้ |
|---|---|
| หน้า UI ว่าง / ไม่มีอะไรแสดง | เป็นที่ browser block `file://` origin → เปิดผ่าน `http://localhost:8000/static/hermes-manager.html` |
| กด Start แล้วพัง | เช็ค `hermes` CLI มีอยู่ใน PATH หรือไม่: `hermes --version` |
| Port 9120-9122 busy | ฆ่า process เก่า: `hermes dashboard --stop` หรือเปลี่ยน port ใน `app/hermes_manager.py` |
| Chat ไม่ตอบ | เช็ค `hermes_available()` — ต้องมี `hermes` CLI + API key ใน `~/.hermes/.env` |
| Config ไม่เปลี่ยน | ต้อง restart dashboard หลังจาก save config |
| Skills list ไม่โหลด | hermes CLI อาจไม่มีใน Docker container — ปกติ (routes ทำงานบน host) |

---

## ไฟล์ที่เกี่ยวข้อง

| ไฟล์ | หน้าที่ |
|---|---|
| `app/hermes_manager.py` | Backend API + process manager |
| `app/main.py` | Router registration (line 11, 48) |
| `static/hermes-manager.html` | Frontend SPA |
| `doc/task/master_checklist.md` | Checklist MG-01 ถึง MG-04 |
