import polars as pl
import duckdb
import os
import sys
from pathlib import Path
from datetime import datetime

# Ensure root is in path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scout_app.core.config import Settings

RAW_FILES = [
    "staging_data/raw_scrape_20260115_032941_Y5XaeGhHnCtFGNP68.xlsx",
    "staging_data/raw_scrape_20260116_064312_MQVMHkPm818gTYMPY.xlsx",
    "staging_data/raw_scrape_20260129_040351_C8FL4HcUW6K9O7b7D.xlsx"
]

def enrich():
    db_path = Settings.get_active_db_path()
    print(f"🔗 Connecting to database: {db_path}")
    conn = duckdb.connect(str(db_path))

    try:
        # 1. Get validated parent ASINs
        valid_parents = [r[0] for r in conn.execute("SELECT parent_asin FROM product_parents").fetchall()]
        print(f"✅ Found {len(valid_parents)} validated parents in DB.")

        # 2. Extract child metadata from raw files
        all_child_data = []
        seen_child_asins = set()

        for f_path in RAW_FILES:
            if not os.path.exists(f_path):
                print(f"⚠️ Warning: File not found {f_path}")
                continue
            
            print(f"📖 Processing {f_path}...")
            df = pl.read_excel(f_path)
            
            # Map raw columns to products schema
            # asin (target) -> parent_asin
            # variationId -> asin (child)
            subset = df.select([
                pl.col("variationId").alias("asin"),
                pl.col("asin").alias("parent_asin"),
                pl.col("productTitle").alias("title"),
                pl.col("imageUrlList/0").alias("image_url"),
                pl.col("variationList/0").alias("specs")
            ]).filter(
                (pl.col("parent_asin").is_in(valid_parents)) & 
                (pl.col("asin").is_not_null())
            )

            # Deduplicate within and across files
            for row in subset.unique(subset=["asin"]).to_dicts():
                if row["asin"] not in seen_child_asins:
                    all_child_data.append(row)
                    seen_child_asins.add(row["asin"])

        print(f"✅ Extracted {len(all_child_data)} unique child products.")

        # 3. Ingest into products table
        print("📥 Ingesting into 'products' table...")
        ingested_count = 0
        updated_count = 0
        
        for item in all_child_data:
            # Check if exists
            exists = conn.execute("SELECT 1 FROM products WHERE asin = ?", [item["asin"]]).fetchone()
            
            if not exists:
                conn.execute("""
                    INSERT INTO products (asin, parent_asin, title, image_url, specs_json, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [
                    item["asin"], 
                    item["parent_asin"], 
                    item["title"], 
                    item["image_url"], 
                    None if item["specs"] is None else '{"variation_0": "' + str(item["specs"]) + '"}',
                    datetime.now()
                ])
                ingested_count += 1
            else:
                # Update parent link just in case it was an orphan before
                conn.execute("""
                    UPDATE products 
                    SET parent_asin = ?, 
                        last_updated = ?
                    WHERE asin = ?
                """, [item["parent_asin"], datetime.now(), item["asin"]])
                updated_count += 1

        print(f"🚀 Ingestion Summary:")
        print(f"- New products created: {ingested_count}")
        print(f"- Existing products updated: {updated_count}")

        # 4. Final Health Check
        total_products = conn.execute("SELECT count(*) FROM products").fetchone()[0]
        orphan_count = conn.execute("SELECT count(*) FROM products WHERE parent_asin NOT IN (SELECT parent_asin FROM product_parents)").fetchone()[0]
        
        print("\n--- DATABASE HEALTH ---")
        print(f"Total Products: {total_products}")
        print(f"Orphaned Products: {orphan_count}")
        print("------------------------")

    except Exception as e:
        print(f"❌ Error during enrichment: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    enrich()
