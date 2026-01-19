import duckdb
from config import Settings
import uuid

def migrate_gatekeeper():
    """
    Initialize 'scrape_queue' table on BOTH Blue and Green databases.
    This ensures requests are persisted regardless of the active DB state.
    """
    databases = [Settings.DB_PATH_A, Settings.DB_PATH_B]
    
    sql_create_table = """
        CREATE TABLE IF NOT EXISTS scrape_queue (
            request_id VARCHAR PRIMARY KEY,
            asin VARCHAR,
            status VARCHAR DEFAULT 'PENDING_APPROVAL',
            requested_by VARCHAR DEFAULT 'user',
            priority INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            note VARCHAR
        );
    """
    
    print("🛡️ Gatekeeper Migration Started...")
    
    for db_path in databases:
        if not db_path.parent.exists():
            continue
            
        try:
            print(f"   -> Migrating {db_path.name}...")
            with duckdb.connect(str(db_path)) as conn:
                conn.execute(sql_create_table)
                # Check if we need to add columns if table exists but old schema? 
                # For now assume fresh or compatible.
        except Exception as e:
            print(f"   ❌ Error migrating {db_path.name}: {e}")

    print("✅ Gatekeeper Migration Completed.")

if __name__ == "__main__":
    migrate_gatekeeper()
