import time
import requests
import subprocess
import pytest
from sqlalchemy import create_engine, inspect

BASE_URL = "http://localhost:8000"
DB_URL = "postgresql://hermes:secret@localhost:5432/hermes_translate"

def setup_module(module):
    print("\n[Phase 2] Starting Docker Compose...")
    subprocess.run(["docker", "compose", "up", "-d", "postgres", "rabbitmq", "api"], check=True)
    # Wait for services to be healthy
    time.sleep(15)

def teardown_module(module):
    print("\n[Phase 2] Stopping Docker Compose...")
    subprocess.run(["docker", "compose", "down"], check=True)

def test_1_alembic_migration():
    # ตรวจสอบสถานะ Alembic
    res = subprocess.run(["alembic", "current"], capture_output=True, text=True)
    assert res.returncode == 0
    
    # ดำเนินการ Downgrade ลบ Table
    subprocess.run(["alembic", "downgrade", "base"], check=True)
    
    # ตรวจสอบว่าตารางหายไป
    engine = create_engine(DB_URL)
    inspector = inspect(engine)
    tables_after_downgrade = inspector.get_table_names()
    assert "translation_rules" not in tables_after_downgrade
    
    # อัปเกรดกลับมาใหม่
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    
def test_2_verify_tables():
    engine = create_engine(DB_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    assert "alembic_version" in tables
    assert "task_records" in tables
    assert "translation_rules" in tables
    
    # Verify columns in translation_rules
    columns = {col['name']: col for col in inspector.get_columns('translation_rules')}
    assert "id" in columns
    assert "keyword" in columns
    assert "rule_text" in columns
    assert "updated_at" in columns
    
    # Verify columns in task_records
    task_columns = {col['name']: col for col in inspector.get_columns('task_records')}
    assert "task_id" in task_columns
    assert "status" in task_columns
    assert "retry_count" in task_columns
    
def test_3_admin_api_crud():
    # 1. Create (POST)
    payload = {"keyword": "test_phase2", "rule_text": "This is a test rule"}
    create_res = requests.post(f"{BASE_URL}/admin/rules", json=payload)
    assert create_res.status_code == 201
    created_rule = create_res.json()
    assert created_rule["keyword"] == "test_phase2"
    rule_id = created_rule["id"]
    
    # 2. List (GET)
    list_res = requests.get(f"{BASE_URL}/admin/rules")
    assert list_res.status_code == 200
    rules = list_res.json()
    assert any(r["id"] == rule_id for r in rules)
    
    # 3. Update (PUT)
    update_payload = {"keyword": "test_phase2", "rule_text": "Updated test rule"}
    update_res = requests.put(f"{BASE_URL}/admin/rules/{rule_id}", json=update_payload)
    assert update_res.status_code == 200
    assert update_res.json()["rule_text"] == "Updated test rule"
    
    # 4. Delete (DELETE)
    delete_res = requests.delete(f"{BASE_URL}/admin/rules/{rule_id}")
    assert delete_res.status_code == 204
    
    # Verify Deletion
    list_res_after = requests.get(f"{BASE_URL}/admin/rules")
    rules_after = list_res_after.json()
    assert not any(r["id"] == rule_id for r in rules_after)

def test_4_ahocorasick_filtering():
    from app.services.rule_engine import extract_rules
    # Create a rule specifically for this test
    requests.post(f"{BASE_URL}/admin/rules", json={"keyword": "specific_keyword", "rule_text": "Found it"})
    
    # Wait briefly just in case cache takes time
    time.sleep(2)
    
    import asyncio
    
    if asyncio.iscoroutinefunction(extract_rules):
        rules = asyncio.run(extract_rules("This is a specific_keyword test"))
    else:
        rules = extract_rules("This is a specific_keyword test")
        
    assert len(rules) > 0, "No rules matched!"
    # Check if we get something that resembles the rule we added
    match_found = False
    for r in rules:
        if isinstance(r, dict) and "keyword" in r and r["keyword"] == "specific_keyword":
            match_found = True
            break
        elif hasattr(r, "keyword") and getattr(r, "keyword") == "specific_keyword":
            match_found = True
            break
        elif "specific_keyword" in str(r):
            match_found = True
            break
    assert match_found, f"Did not find specific_keyword in {rules}"
