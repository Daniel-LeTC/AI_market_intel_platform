import duckdb
from .config import Settings

def migrate_gatekeeper():
    """
    Initialize 'scrape_queue' table on BOTH Blue and Green databases.
    """
    databases = [Settings.DB_PATH_A, Settings.DB_PATH_B]
    
    sql = """
        CREATE TABLE IF NOT EXISTS scrape_queue (
            request_id VARCHAR PRIMARY KEY,
            asin VARCHAR,
            status VARCHAR DEFAULT 'PENDING_APPROVAL', -- PENDING, APPROVED, PROCESSING, COMPLETED, FAILED
            requested_by VARCHAR,
            note VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS product_parents (
            parent_asin VARCHAR PRIMARY KEY,
            category VARCHAR,
            niche VARCHAR,
            title VARCHAR,
            brand VARCHAR,
            image_url VARCHAR,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    
    print("🚧 Gatekeeper Migration Started...")
    
    for db_path in databases:
        if not db_path.parent.exists():
            continue
            
        try:
            print(f"   -> Migrating {db_path.name}...")
            with duckdb.connect(str(db_path)) as conn:
                conn.execute(sql)
        except Exception as e:
            print(f"   ❌ Error migrating {db_path.name}: {e}")

    print("✅ Gatekeeper Migration Completed.")

if __name__ == "__main__":
    migrate_gatekeeper()
