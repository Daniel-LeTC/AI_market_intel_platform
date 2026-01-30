import polars as pl
import duckdb
import json
import os
import sys
from pathlib import Path

# Ensure root is in path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scout_app.core.config import Settings

SOURCES = {
    "excel": "Kid Comforter Set_Thoai RnD_19-12-2025.xlsx",
    "tumbler": "/app/staging_data_local/20260129_data/new_product_metadata/39_asin.jsonl",
    "books_1": "/app/staging_data_local/20260129_data/new_product_metadata/dataset_amazon-product-details-scraper_2026-01-29_03-21-49-183.jsonl",
    "books_2": "/app/staging_data_local/20260129_data/new_product_metadata/dataset_amazon-product-details-scraper_2026-01-29_03-23-57-967.jsonl"
}

def reset_and_sync():
    db_path = Settings.get_active_db_path()
    print(f"🔗 Connecting to database: {db_path}")
    conn = duckdb.connect(str(db_path))

    try:
        # 1. Collect all Valid Parents and Mappings
        valid_parents = [] # list of (parent_asin, category, brand, title, niche)
        child_to_parent = {} # dict of child_asin -> parent_asin

        # --- EXCEL ---
        print(f"📖 Processing Excel: {SOURCES['excel']}")
        df_excel = pl.read_excel(SOURCES['excel'])
        for row in df_excel.to_dicts():
            c_asin = row['ASIN']
            p_asin = row['Parent Asin']
            child_to_parent[c_asin] = p_asin
            
        # Extract unique parents from Excel
        excel_parents = df_excel.select([
            pl.col("Parent Asin").alias("parent_asin"),
            pl.col("Brand").alias("brand"),
            pl.col("Company Category").alias("category"),
            pl.col("Main Niche").alias("niche")
        ]).unique(subset=["parent_asin"])
        
        for row in excel_parents.to_dicts():
            valid_parents.append((row['parent_asin'], 'comforter', row['brand'], 'Imported from Excel', row['niche']))

        # --- JSONLs ---
        def process_jsonl(path, category):
            print(f"📖 Processing JSONL: {path} ({category})")
            if not os.path.exists(path):
                print(f"⚠️ Warning: File not found {path}")
                return
            with open(path, 'r') as f:
                for line in f:
                    data = json.loads(line)
                    asin = data.get('asin')
                    p_asin = data.get('parentAsin') or asin # Fallback to asin if parent missing
                    if asin:
                        child_to_parent[asin] = p_asin
                    
                    # We only add the "parent" record if we haven't seen it in valid_parents list
                    if p_asin and p_asin not in [p[0] for p in valid_parents]:
                        valid_parents.append((
                            p_asin, 
                            category, 
                            data.get('brand', 'Unknown'), 
                            data.get('title', 'Imported from JSONL'), 
                            data.get('niche', 'unknown')
                        ))

        process_jsonl(SOURCES['tumbler'], 'tumbler')
        process_jsonl(SOURCES['books_1'], 'book')
        process_jsonl(SOURCES['books_2'], 'book')

        print(f"✅ Collected {len(valid_parents)} total valid parents.")
        print(f"✅ Collected {len(child_to_parent)} child -> parent mappings.")

        # 2. Reset product_parents
        print("🧹 Clearing product_parents table...")
        conn.execute("DELETE FROM product_parents")
        
        # 3. Insert Valid Parents
        print("📥 Inserting validated parents...")
        for p in valid_parents:
            conn.execute("""
                INSERT INTO product_parents (parent_asin, category, brand, title, niche)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (parent_asin) DO UPDATE SET 
                    category = EXCLUDED.category,
                    brand = EXCLUDED.brand,
                    title = EXCLUDED.title,
                    niche = EXCLUDED.niche
            """, p)

        # 4. Update products Table
        print("🛠️ Relinking 'products' table...")
        # We'll use a temp table for the mapping update
        mapping_data = pl.DataFrame([
            {"asin": k, "correct_parent_asin": v} for k, v in child_to_parent.items()
        ])
        conn.execute("CREATE OR REPLACE TEMPORARY TABLE relink_map AS SELECT * FROM mapping_data")
        
        conn.execute("""
            UPDATE products 
            SET parent_asin = m.correct_parent_asin
            FROM relink_map m
            WHERE products.asin = m.asin
        """)
        
        # 5. Handle leftovers in products
        # Any product not in our mapping should probably have parent_asin = asin (default orphan)
        # OR we leave them as is if they already match.
        
        # 6. Final Validation
        final_count = conn.execute("SELECT count(*) FROM product_parents").fetchone()[0]
        orphan_count = conn.execute("SELECT count(*) FROM products WHERE parent_asin NOT IN (SELECT parent_asin FROM product_parents)").fetchone()[0]
        
        print("\n--- FINAL SOURCE-OF-TRUTH SUMMARY ---")
        print(f"Total Families (product_parents): {final_count}")
        print(f"Orphaned products: {orphan_count}")
        print("Categories:")
        print(conn.execute("SELECT category, count(*) FROM product_parents GROUP BY category").fetchall())
        print("--------------------------------------")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    reset_and_sync()
