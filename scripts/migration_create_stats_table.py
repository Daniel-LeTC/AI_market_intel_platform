import duckdb
from pathlib import Path
import sys

# Add root
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scout_app.core.config import Settings

def migrate():
    # We need to apply this to BOTH Blue and Green DBs to be safe
    dbs = [Settings.DB_PATH_A, Settings.DB_PATH_B]
    
    for db_path in dbs:
        print(f"Applying migration to: {db_path}...")
        try:
            with duckdb.connect(str(db_path)) as conn:
                # 1. Create Table if not exists
                sql = """
                    CREATE TABLE IF NOT EXISTS product_stats (
                        asin VARCHAR PRIMARY KEY,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metrics_json JSON
                    );
                """
                conn.execute(sql)
                print(f"✅ Created 'product_stats' in {db_path.name}")
                
        except Exception as e:
            print(f"❌ Error migrating {db_path.name}: {e}")

if __name__ == "__main__":
    migrate()
