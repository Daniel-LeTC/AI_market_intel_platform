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
        # 1. Identify missing parents (ONLY those where products table confirms it's a parent)
        missing_query = """
            SELECT DISTINCT parent_asin 
            FROM products 
            WHERE parent_asin NOT IN (SELECT parent_asin FROM product_parents)
            AND parent_asin IN (SELECT asin FROM products WHERE asin = parent_asin)
        """
        missing_parents = [r[0] for r in conn.execute(missing_query).fetchall()]
        print(f"🔍 Found {len(missing_parents)} TRUE parent ASINs referenced in 'products' but missing in 'product_parents'.")

        if not missing_parents:
            print("✅ No missing parents found. Database is consistent.")
        else:
            # 2. Insert missing parents (using the definitions in products)
            insert_query = """
                INSERT OR IGNORE INTO product_parents (parent_asin, category, brand, title, niche)
                SELECT parent_asin, 'unclassified', MAX(brand), MAX(title), COALESCE(MAX(main_niche), 'unknown')
                FROM products
                WHERE parent_asin NOT IN (SELECT parent_asin FROM product_parents)
                AND parent_asin IN (SELECT asin FROM products WHERE asin = parent_asin)
                GROUP BY parent_asin
            """
            conn.execute(insert_query)
            print(f"✅ Synchronized {len(missing_parents)} records to 'product_parents'.")

        # 3. Standardize Niches/Categories for existing data
        print("🧹 Standardizing existing null categories/niches...")
        conn.execute("UPDATE product_parents SET category = 'unclassified' WHERE category IS NULL")
        conn.execute("UPDATE product_parents SET niche = 'unknown' WHERE niche IS NULL OR niche IN ('None', 'Non-defined')")

        # 4. Multi-Niche Backfill
        print("🔀 Backfilling 'Multi-Niche' labels for parents with divergent child niches...")
        multi_niche_query = """
            UPDATE product_parents 
            SET niche = 'Multi-Niche'
            WHERE parent_asin IN (
                SELECT parent_asin 
                FROM products 
                GROUP BY 1 
                HAVING COUNT(DISTINCT main_niche) > 1
            )
        """
        conn.execute(multi_niche_query)
        multi_count = conn.execute("SELECT count(*) FROM product_parents WHERE niche = 'Multi-Niche'").fetchone()[0]
        print(f"✅ Labeled {multi_count} ASINs as 'Multi-Niche'.")

        # 5. Stats
        total_parents = conn.execute("SELECT count(*) FROM product_parents").fetchone()[0]
        false_parents = conn.execute("SELECT count(*) FROM product_parents WHERE parent_asin IN (SELECT asin FROM products WHERE asin != parent_asin)").fetchone()[0]
        orphan_count = conn.execute("SELECT count(*) FROM products WHERE parent_asin NOT IN (SELECT parent_asin FROM product_parents)").fetchone()[0]
        
        print("\n--- HEALTH CHECK ---")
        print(f"Total product_parents: {total_parents}")
        print(f"False parents (children): {false_parents} (RETAINED as per policy)")
        print(f"Missing parents (orphaned products): {orphan_count}")
        print("--------------------")

    except Exception as e:
        print(f"❌ Error during sync: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    sync_missing()
