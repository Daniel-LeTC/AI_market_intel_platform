import sys
import os
import duckdb
from pathlib import Path
import time
import json

# Add root to sys.path
sys.path.append(os.getcwd())

from scout_app.core.wallet import WalletGuard
from scout_app.core.config import Settings
from scout_app.routers.social import run_social_task, SocialRequest
from scout_app.core.social_scraper import SocialScraper

# Force Mock Mode for Scraper
# We monkeypatch the init or just ensure we don't need real API key if mock_mode is passed
# But SocialScraper in routers/social.py is instantiated inside the function.
# For testing, we can temporarily set env var or just rely on the fact that if no API key, it warns.
# Better: Let's trust the logic wrapper but we need to ensure it uses mock.
# The `run_social_task` in router instantiates SocialScraper(). 
# To force mock without changing router code, we can set env var APIFY_TOKEN to empty if not set?
# Actually, SocialScraper defaults to mock_mode=True if no key.
# Let's ensure APIFY_TOKEN is unset for this test process if we want mock.
if "APIFY_TOKEN" in os.environ:
    del os.environ["APIFY_TOKEN"]

DB_PATH = str(Settings.SYSTEM_DB)
TEST_USER = "u_wallet_test"

def setup_test_user():
    print(f"🛠️ Setting up test user: {TEST_USER}...")
    with duckdb.connect(DB_PATH) as conn:
        # Reset if exists
        conn.execute("DELETE FROM user_wallets WHERE user_id = ?", [TEST_USER])
        conn.execute("DELETE FROM users WHERE user_id = ?", [TEST_USER])
        
        # Create
        conn.execute("INSERT INTO users (user_id, username, role, monthly_budget) VALUES (?, 'wallet_tester', 'USER', 5.0)", [TEST_USER])
        conn.execute("INSERT INTO user_wallets (user_id, current_spend) VALUES (?, 0.0)", [TEST_USER])

def check_balance(expected_spend):
    with duckdb.connect(DB_PATH, read_only=True) as conn:
        spend = conn.execute("SELECT current_spend FROM user_wallets WHERE user_id = ?", [TEST_USER]).fetchone()[0]
        print(f"💰 Current Spend: ${spend} (Expected: ${expected_spend})")
        return abs(spend - expected_spend) < 0.01

def test_wallet_flow():
    setup_test_user()
    
    # 1. Test Success Case (Cost $1.0)
    print("\n🧪 TEST 1: Affordable Task ($1.0)")
    req = SocialRequest(
        keywords=["test_cheap"],
        platform="tiktok",
        limit=10,
        user_id=TEST_USER
    )
    # We simulate cost manually since we call the internal function
    est_cost = 1.0
    
    # Run Task (This should pass wallet check and deduct money)
    # Note: run_social_task catches exceptions, so we watch logs
    run_social_task(req, est_cost)
    
    if check_balance(1.0):
        print("✅ TEST 1 PASSED: Money deducted correctly.")
    else:
        print("❌ TEST 1 FAILED: Balance mismatch.")

    # 2. Test Insufficient Funds (Cost $10.0, Budget $5.0, Spent $1.0 -> Remaining $4.0)
    print("\n🧪 TEST 2: Expensive Task ($10.0)")
    req_expensive = SocialRequest(
        keywords=["test_expensive"],
        platform="tiktok",
        limit=100,
        user_id=TEST_USER
    )
    est_cost_expensive = 10.0
    
    run_social_task(req_expensive, est_cost_expensive)
    
    if check_balance(1.0): # Spend should remain 1.0
        print("✅ TEST 2 PASSED: Task blocked, no money deducted.")
    else:
        print("❌ TEST 2 FAILED: Money was deducted for blocked task!")

    # 3. Verify Logs
    print("\n📜 Verifying JSONL Logs...")
    log_dir = Settings.LOGS_BUFFER_DIR
    # Find latest scrape_audit log
    logs = sorted(list(log_dir.glob("scrape_audit_*.jsonl")))
    if not logs:
        print("❌ No scrape_audit log found!")
        return

    latest_log = logs[-1]
    print(f"Reading {latest_log.name}...")
    found_success = False
    with open(latest_log, "r") as f:
        for line in f:
            entry = json.loads(line)
            if entry.get("user_id") == TEST_USER:
                print(f" -> Found Log: {entry.get('status')} | Cost: {entry.get('cost_usd')}")
                if entry.get("status") == "SUCCESS" and entry.get("cost_usd") == 1.0:
                    found_success = True
    
    if found_success:
        print("✅ TEST 3 PASSED: Audit Log entry confirmed.")
    else:
        print("❌ TEST 3 FAILED: Could not find success log for test user.")

if __name__ == "__main__":
    test_wallet_flow()
