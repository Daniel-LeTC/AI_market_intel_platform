import duckdb
import sys
from pathlib import Path

# Ensure root is in path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scout_app.core.config import Settings

def sync_missing():
    db_path = Settings.get_active_db_path()
    print(f"🔗 Connecting to database: {db_path}")
    conn = duckdb.connect(str(db_path))

    try:
        # 1. Identify missing parents
        missing_query = """
            SELECT DISTINCT parent_asin 
            FROM products 
            WHERE parent_asin NOT IN (SELECT parent_asin FROM product_parents)
        """
        missing_parents = [r[0] for r in conn.execute(missing_query).fetchall()]
        print(f"🔍 Found {len(missing_parents)} parent ASINs referenced in 'products' but missing in 'product_parents'.")

        if not missing_parents:
            print("✅ No missing parents found. Database is consistent.")
            return

        # 2. Insert missing parents as 'unclassified' (using INSERT OR IGNORE for safety)
        insert_query = """
            INSERT OR IGNORE INTO product_parents (parent_asin, category, brand, title, niche)
            SELECT parent_asin, 'unclassified', MAX(brand), MAX(title), 'unknown'
            FROM products
            WHERE parent_asin NOT IN (SELECT parent_asin FROM product_parents)
            GROUP BY parent_asin
        """
        conn.execute(insert_query)
        print(f"✅ Synchronized {len(missing_parents)} records to 'product_parents'.")

        # 3. Stats
        total_parents = conn.execute("SELECT count(*) FROM product_parents").fetchone()[0]
        orphan_count = conn.execute("SELECT count(*) FROM products WHERE parent_asin NOT IN (SELECT parent_asin FROM product_parents)").fetchone()[0]
        
        print("\n--- HEALTH CHECK ---")
        print(f"Total product_parents: {total_parents}")
        print(f"Orphaned products: {orphan_count}")
        print("--------------------")

    except Exception as e:
        print(f"❌ Error during sync: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    sync_missing()
