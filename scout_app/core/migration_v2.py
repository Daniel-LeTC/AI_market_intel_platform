import duckdb
from .config import Settings

def migrate_v2_social_wallet():
    """
    Initialize Database Tables for Social Scout (Wallet Guard System).
    """
    db_path = str(Settings.DB_PATH)
    conn = duckdb.connect(db_path)
    
    try:
        # 1. User Budget Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users_budget (
                user_id VARCHAR PRIMARY KEY,
                monthly_cap FLOAT DEFAULT 20.0,
                current_spend FLOAT DEFAULT 0.0,
                is_locked BOOLEAN DEFAULT FALSE,
                last_reset DATE DEFAULT CURRENT_DATE
            )
        """)

        # 2. Scrape Transactions Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scrape_transactions (
                trans_id UUID PRIMARY KEY DEFAULT uuid(),
                user_id VARCHAR,
                platform VARCHAR,
                target TEXT,
                item_count INTEGER,
                estimated_cost FLOAT,
                actual_cost FLOAT,
                status VARCHAR, -- 'PENDING', 'SUCCESS', 'FAILED'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Social Case Studies Table (The Knowledge Base)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS social_case_studies (
                case_id UUID PRIMARY KEY DEFAULT uuid(),
                trans_id UUID,
                platform VARCHAR,
                target TEXT,
                raw_file_path TEXT,
                ai_analysis_json JSON,
                created_by VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Init default admin user if empty
        res = conn.execute("SELECT count(*) FROM users_budget").fetchone()[0]
        if res == 0:
            conn.execute("INSERT INTO users_budget (user_id, monthly_cap) VALUES ('admin', 100.0)")
            conn.execute("INSERT INTO users_budget (user_id, monthly_cap) VALUES ('sếp', 100.0)")
            conn.execute("INSERT INTO users_budget (user_id, monthly_cap) VALUES ('marketing_team', 50.0)")

        print("✅ Migration V2 (Social Wallet) completed.")
        
    except Exception as e:
        print(f"❌ Migration V2 Failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_v2_social_wallet()
