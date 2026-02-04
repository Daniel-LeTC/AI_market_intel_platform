import duckdb
from pathlib import Path

DB_PATH = "scout_b.duckdb"

def fix_mapping(old_parent: str, new_parent: str, db_path: str = DB_PATH):
    """
    Moves all products and reviews from old_parent back to new_parent.
    Also ensures new_parent exists in product_parents.
    """
    if not Path(db_path).exists():
        print(f"❌ DB not found at {db_path}")
        return

    conn = duckdb.connect(db_path)
    try:
        print(f"🔄 Relinking data from {old_parent} -> {new_parent}...")
        
        # 1. Ensure new_parent has a record in product_parents if it came from old_parent
        # (This avoids FK issues if we delete old_parent later)
        conn.execute("""
            INSERT OR IGNORE INTO product_parents (parent_asin, category, niche, title, brand, image_url)
            SELECT ?, category, niche, title, brand, image_url
            FROM product_parents WHERE parent_asin = ?
        """, [new_parent, old_parent])

        # 2. Update products table
        res_prod = conn.execute("UPDATE products SET parent_asin = ? WHERE parent_asin = ?", [new_parent, old_parent])
        print(f"✅ Updated {res_prod.rowcount} records in 'products'")

        # 3. Update reviews table
        res_rev = conn.execute("UPDATE reviews SET parent_asin = ? WHERE parent_asin = ?", [new_parent, old_parent])
        print(f"✅ Updated {res_rev.rowcount} records in 'reviews'")

        # 4. Optional: Remove the "Grandparent" if it's now orphaned
        # Only delete if no products are left pointing to it
        remaining = conn.execute("SELECT count(*) FROM products WHERE parent_asin = ?", [old_parent]).fetchone()[0]
        if remaining == 0:
            conn.execute("DELETE FROM product_parents WHERE parent_asin = ?", [old_parent])
            print(f"🗑️ Removed orphaned parent {old_parent}")

        print("✨ Mapping fix completed successfully.")
        
    except Exception as e:
        print(f"💥 Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    db_to_fix = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    # SPECIFIC FIX FOR THE TUMBLER ISSUE
    # CJ5 (Grandparent) -> 5X1 (User's Parent)
    fix_mapping("B0DCFZZCJ5", "B0DCFRR5X1", db_to_fix)
