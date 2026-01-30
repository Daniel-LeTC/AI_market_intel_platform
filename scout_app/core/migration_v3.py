import duckdb
from .config import Settings

def migrate_v3_product_parents():
    """
    Initialize product_parents table for reference and metadata enrichment.
    """
    db_path = str(Settings.get_active_db_path())
    print(f"🚀 Running Migration V3 on {db_path}...")
    conn = duckdb.connect(db_path)
    
    try:
        # Create product_parents table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS product_parents (
                parent_asin VARCHAR PRIMARY KEY,
                category VARCHAR,
                niche VARCHAR,
                title VARCHAR,
                brand VARCHAR,
                image_url VARCHAR,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        print("✅ Migration V3 (Product Parents) completed.")
        
    except Exception as e:
        print(f"❌ Migration V3 Failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_v3_product_parents()
