# 📝 QA Review Feedback — HermesTranslate (Phase 1-4)

**วันที่:** 1 กรกฎาคม 2026
**ผลการตรวจ:** ❌ **ไม่ผ่าน (FAIL)**

จากการตรวจสอบ Source Code เชิงลึกแบบไม่เข้าข้าง (Strict Review) เทียบกับคู่มือ QA Report พบว่ามี Logical Bugs ร้ายแรง 3 จุดที่ทำให้ระบบ Multi-Agent Pipeline ไม่สามารถทำงานได้จริงตามที่เคลมไว้ในเทสเคส

## ข้อผิดพลาดที่พบ (Critical Bugs)

### 1. Worker Process ไม่มีข้อมูลกฎ (Automaton is None)
- **ไฟล์:** `app/worker.py`
- **ปัญหา:** ตัว Worker ถูกออกแบบมาให้รันแยกเป็นคนละ Process กับ API แต่โค้ดกลับไม่มีการสั่งโหลดข้อมูลกฎจาก Database (`await reload()`) ในตอนเริ่มต้นเลย
- **ผลกระทบ:** ทำให้ตัวแปร `_automaton` ภายใน `rule_engine.py` เป็น `None` ตลอดเวลาสำหรับฝั่ง Worker เมื่อ Worker ดึงงานมาทำ ฟังก์ชัน `extract_rules()` จะคืนค่า `[]` (ไม่พบกฎ) เสมอ (ส่งผลให้ Main Agent ไม่ได้รับชุดกฎไปแปล และ Validate Agent ก็จะคิดว่าไม่มีกฎฝ่าฝืนแล้วคืนค่าผ่านตลอด)

### 2. First Load Delay (หน่วงเวลาโหลดครั้งแรก)
- **ไฟล์:** `app/services/rule_engine.py` (ในฟังก์ชัน `_bg_refresh`)
- **ปัญหา:** มีการรันคำสั่ง `await asyncio.sleep(interval)` (60 วินาที) **ก่อน** ที่จะทำการ `await reload()` ในการเข้าลูปครั้งแรก
- **ผลกระทบ:** ทำให้ช่วง 60 วินาทีแรกหลังจากเปิดระบบ (เช่น ตอนรัน docker-compose up) ระบบจะยังไม่มีข้อมูล Automaton ใน Memory เลย ทำให้ไม่สามารถสกัดกฎใดๆ ได้จนกว่าจะผ่านไป 1 นาที หรือจนกว่าจะมีการยิง API อัปเดตกฎเพื่อกระตุ้นให้โหลด

### 3. Regex สกัดคำแปลไม่สอดคล้องกับคู่มือทดสอบ (Test Guide)
- **ไฟล์:** `app/agents/translate_agent.py`
- **ปัญหา:** Regex ในการดึงคำแปลเป้าหมายเขียนไว้เป็น `r"to ['\"](.+?)['\"]"` ซึ่งแปลว่าบังคับให้เป้าหมายต้องมีเครื่องหมายคำพูด (Quote) ล้อมรอบ เช่น `to "xin chao"`
- **ผลกระทบ:** แต่ในตัวอย่างที่เขียนใน `test_guide_final.md` คือ `"Translate hello to xin chao"` (ไม่มี Quote) ทำให้ Regex ทำงานไม่ตรงกัน ไม่สามารถสกัดคำว่า "xin chao" ออกมาได้ ส่งผลให้การแปลไม่เกิดการแทนที่คำในข้อความจริงๆ

## แนวทางแก้ไขแนะนำตาม Ponytail Principle (Option B - Sustainable Fix)
1. **Worker Initialization:** ปรับให้ฟังก์ชันดึงกฎเป็น Lazy Loading หรือ Async Loading เพื่อการันตีว่าถ้า Automaton ยังเป็น None อยู่ จะต้องไปดึงฐานข้อมูลก่อนเสมอ หรืออย่างน้อยที่สุดต้องเพิ่มการเรียก `await reload()` ไว้ตอนเริ่มต้นรัน `worker.py`
2. **Immediate Load:** สลับการทำงานใน `_bg_refresh` ให้เรียก `await reload()` ก่อนสั่ง `await asyncio.sleep(interval)`
3. **Regex Flexibility:** ปรับให้ Regex รองรับทั้งแบบมี Quote และไม่มี Quote เพื่อลดความผิดพลาดจากคนกรอกข้อมูล หรืออัปเดตคู่มือให้บังคับพิมพ์ Quote ตลอดเวลา
