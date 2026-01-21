import duckdb
from pathlib import Path
import sys

# Add root to sys.path to find core
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scout_app.core.config import Settings

def migrate_db(db_path: Path):
    if not db_path.exists():
        print(f"⚠️ DB not found at {db_path}, skipping.")
        return

    print(f"🔄 Migrating {db_path}...")
    try:
        with duckdb.connect(str(db_path)) as conn:
            # Check existing columns first to avoid ugly try/except blocks if possible, 
            # but try/catch ALTER is standard for DuckDB migration scripts to be idempotent.
            
            # 1. Add real_average_rating
            try:
                conn.execute("ALTER TABLE products ADD COLUMN real_average_rating DOUBLE")
                print("   ✅ Added column: real_average_rating")
            except Exception:
                print("   ℹ️ Column real_average_rating likely exists.")

            # 2. Add real_total_ratings
            try:
                conn.execute("ALTER TABLE products ADD COLUMN real_total_ratings INTEGER")
                print("   ✅ Added column: real_total_ratings")
            except Exception:
                print("   ℹ️ Column real_total_ratings likely exists.")

            # 3. Add rating_breakdown (JSON)
            try:
                conn.execute("ALTER TABLE products ADD COLUMN rating_breakdown JSON")
                print("   ✅ Added column: rating_breakdown")
            except Exception:
                print("   ℹ️ Column rating_breakdown likely exists.")

    except Exception as e:
        print(f"❌ Critical Error migrating {db_path}: {e}")

if __name__ == "__main__":
    print("🚀 Starting Migration V3: Adding Product Metadata Columns...")
    # Migrate Active DB
    migrate_db(Settings.DB_PATH_A)
    # Migrate Standby DB (if exists/different)
    migrate_db(Settings.DB_PATH_B)
    
    print("\n✅ Migration V3 (Metadata) Complete.")
