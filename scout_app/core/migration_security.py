import duckdb
from pathlib import Path
import os

# --- Config Paths ---
# Hardcoded relative to this script for independence
DB_DIR = Path(__file__).resolve().parent.parent / "database"
SYSTEM_DB = DB_DIR / "system.duckdb"
LOGS_DB = DB_DIR / "logs.duckdb"

def init_security_dbs():
    """
    Initialize System (Auth/Budget) and Logs (Audit/History) databases.
    """
    os.makedirs(DB_DIR, exist_ok=True)

    # 1. System DB Initialization
    print(f"🔐 Initializing System DB: {SYSTEM_DB.name}...")
    with duckdb.connect(str(SYSTEM_DB)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR PRIMARY KEY,
                username VARCHAR UNIQUE,
                password_hash VARCHAR,
                role VARCHAR DEFAULT 'USER',
                monthly_budget DOUBLE DEFAULT 20.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_wallets (
                user_id VARCHAR PRIMARY KEY,
                current_spend DOUBLE DEFAULT 0.0,
                last_topup_date TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                pin_id VARCHAR PRIMARY KEY,
                user_id VARCHAR,
                asin VARCHAR,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)
    
    # 2. Logs DB Initialization
    print(f"📜 Initializing Logs DB: {LOGS_DB.name}...")
    with duckdb.connect(str(LOGS_DB)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scrape_audit_logs (
                log_id VARCHAR PRIMARY KEY,
                user_id VARCHAR,
                platform VARCHAR,
                task_type VARCHAR,
                target VARCHAR,
                item_count INTEGER,
                cost_usd DOUBLE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                chat_id VARCHAR PRIMARY KEY,
                user_id VARCHAR,
                asin_context VARCHAR,
                user_query VARCHAR,
                ai_response VARCHAR,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    print("✅ Security & Audit Databases Ready.")

if __name__ == "__main__":
    init_security_dbs()
