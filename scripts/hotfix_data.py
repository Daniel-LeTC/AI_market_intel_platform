import duckdb
from pathlib import Path

DB_FILES = [
    "scout_app/database/scout_a.duckdb",
    "scout_app/database/scout_b.duckdb"
]

def hotfix():
    for db_path in DB_FILES:
        if not Path(db_path).exists():
            print(f"⏩ Skipping {db_path} (not found)")
            continue
            
        print(f"🛠️ Patching {db_path}...")
        conn = duckdb.connect(db_path)
        try:
            # 1. Category Fix: Move mislabeled comforters/unclassified to tumbler
            res = conn.execute("""
                UPDATE product_parents 
                SET category = 'tumbler' 
                WHERE (niche IN ('Tumblers', 'Tumblers & Water Glasses', 'Thermoses')
                   OR title ILIKE '%Tumbler%' 
                   OR title ILIKE '%Water Bottle%')
                  AND category != 'tumbler'
            """)
            print(f"   ✅ Fixed {res.rowcount} tumbler categories")

            # 2. Specific fix for B0DCFRR5X1
            conn.execute("UPDATE product_parents SET category = 'tumbler' WHERE parent_asin = 'B0DCFRR5X1'")

            # 3. Brand cleanup
            conn.execute("UPDATE product_parents SET brand = REPLACE(brand, 'Brand: ', '') WHERE brand LIKE 'Brand: %'")
            conn.execute("UPDATE product_parents SET brand = REPLACE(brand, 'Visit the ', '') WHERE brand LIKE 'Visit the %'")
            conn.execute("UPDATE product_parents SET brand = REPLACE(brand, ' Store', '') WHERE brand LIKE '% Store'")
            print("   ✅ Cleaned brand names")

            # 4. Book Niche standardization
            res_books = conn.execute("""
                UPDATE product_parents 
                SET niche = 'Drawing Books' 
                WHERE category = 'book' 
                  AND (niche = 'unknown' OR niche IS NULL) 
                  AND title ILIKE '%Draw%'
            """)
            print(f"   ✅ Updated {res_books.rowcount} book niches")

            # 5. DNA Enrichment (Common Sense fills)
            # Tumblers
            conn.execute("""
                UPDATE products 
                SET material = 'Stainless Steel' 
                WHERE material IS NULL 
                  AND (title ILIKE '%Stainless%' OR title ILIKE '%Steel%')
                  AND parent_asin IN (SELECT parent_asin FROM product_parents WHERE category = 'tumbler')
            """)
            # Books
            conn.execute("""
                UPDATE products 
                SET material = 'Paper', target_audience = 'Kids'
                WHERE (title ILIKE '%Kids%' OR title ILIKE '%Children%')
                  AND (material IS NULL OR target_audience IS NULL)
                  AND parent_asin IN (SELECT parent_asin FROM product_parents WHERE category = 'book')
            """)
            print("   ✅ Enriched Product DNA fields")

            # 6. Clean Brand names in products table too
            conn.execute("UPDATE products SET brand = REPLACE(brand, 'Brand: ', '') WHERE brand LIKE 'Brand: %'")
            conn.execute("UPDATE products SET brand = REPLACE(brand, 'Visit the ', '') WHERE brand LIKE 'Visit the %'")
            conn.execute("UPDATE products SET brand = REPLACE(brand, ' Store', '') WHERE brand LIKE '% Store'")
            print("   ✅ Cleaned brands in products table")

            # 7. Sync Niche back to products table
            conn.execute("""
                UPDATE products 
                SET main_niche = pp.niche 
                FROM product_parents pp 
                WHERE products.parent_asin = pp.parent_asin
            """)
            print("   ✅ Synced niches to products table")

            # 8. Summary
            stats = conn.execute("SELECT category, count(*) FROM product_parents GROUP BY 1").fetchall()
            print(f"📊 Final Stats: {stats}")

        except Exception as e:
            print(f"💥 Error on {db_path}: {e}")
        finally:
            conn.close()

if __name__ == '__main__':
    hotfix()
