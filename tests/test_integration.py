import time
import requests
import subprocess

BASE_URL = "http://localhost:8000"

def setup_module(module):
    print("\n[Test 8] Starting Docker Compose...")
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
    time.sleep(15)  # รอให้ Services (DB, RabbitMQ, Worker, API) พร้อมทำงาน

def teardown_module(module):
    print("\n[Test 12] Stopping Docker Compose...")
    subprocess.run(["docker", "compose", "down"], check=True)

def test_9_end_to_end_translation():
    # 1. เพิ่มกฎการแปล
    requests.post(f"{BASE_URL}/admin/rules", json={"keyword": "Hello", "rule_text": "Translate Hello to สวัสดี"})
    
    # 2. ส่งข้อความแปล
    res = requests.post(f"{BASE_URL}/translate/", json={"text": "Hello world"})
    task_id = res.json().get("task_id")
    
    # 3. รอ Worker ประมวลผล
    time.sleep(5)
    
    # 4. เช็คสถานะ
    status_res = requests.get(f"{BASE_URL}/status/{task_id}").json()
    assert status_res.get("status") == "completed", f"Expected completed but got {status_res}"
    assert "สวัสดี" in status_res.get("result_text", "")

def test_10_retry_scenario():
    # เพิ่มกฎที่จะทำให้ Validate ไม่ผ่านเสมอ
    requests.post(f"{BASE_URL}/admin/rules", json={"keyword": "testretry", "rule_text": "Keep as testretry"})
    
    res = requests.post(f"{BASE_URL}/translate/", json={"text": "testretry message"})
    task_id = res.json().get("task_id")
    
    # รอให้ Worker ทำงานครบ 4 รอบ (1 + 3 retries)
    time.sleep(25)
    
    status_res = requests.get(f"{BASE_URL}/status/{task_id}").json()
    assert status_res.get("status") == "failed", f"Expected failed but got {status_res}"
    assert status_res.get("retry_count") == 3

def test_11_idempotency():
    import json
    payload_str = json.dumps({"task_id": "SAME-ID-123", "text": "dup"})
    data = {
        "properties": {},
        "routing_key": "translation_tasks",
        "payload": payload_str,
        "payload_encoding": "string"
    }
    rabbitmq_url = "http://localhost:15672/api/exchanges/%2F/amq.default/publish"
    requests.post(rabbitmq_url, auth=("guest", "guest"), json=data)
    
    time.sleep(3)
    status_res = requests.get(f"{BASE_URL}/status/SAME-ID-123")
    assert status_res.status_code == 404 or status_res.json().get("status") != "completed"
