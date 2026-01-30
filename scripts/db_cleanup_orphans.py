import polars as pl
import duckdb
import os
import sys
from pathlib import Path

# Ensure root is in path to import scout_app
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scout_app.core.config import Settings

EXCEL_FILE = "Kid Comforter Set_Thoai RnD_19-12-2025.xlsx"

def cleanup():
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ Excel file not found: {EXCEL_FILE}")
        return

    print(f"📖 Loading Excel mapping from {EXCEL_FILE}...")
    # Read Excel using polars
    df = pl.read_excel(EXCEL_FILE)
    
    # Select relevant columns and rename to match DB schema where possible
    # ASIN, Parent Asin, Brand, Product Line, Company Category, Main Niche
    mapping_df = df.select([
        pl.col("ASIN").alias("asin"),
        pl.col("Parent Asin").alias("correct_parent_asin"),
        pl.col("Brand").alias("brand"),
        pl.col("Product Line").alias("product_line"),
        pl.col("Company Category").alias("category"),
        pl.col("Main Niche").alias("niche")
    ]).unique(subset=["asin"])

    print(f"✅ Loaded {len(mapping_df)} unique ASIN mappings.")

    db_path = Settings.get_active_db_path()
    print(f"🔗 Connecting to database: {db_path}")
    conn = duckdb.connect(str(db_path))

    try:
        # 1. Create temporary mapping table
        conn.execute("CREATE OR REPLACE TEMPORARY TABLE excel_mapping AS SELECT * FROM mapping_df")
        
        # 2. Update products table with correct parent_asin
        print("🛠️ Updating 'products' table with correct parent ASINs...")
        update_query = """
        UPDATE products 
        SET parent_asin = m.correct_parent_asin
        FROM excel_mapping m
        WHERE products.asin = m.asin
        """
        conn.execute(update_query)
        updated_count = conn.execute("SELECT count(*) FROM excel_mapping m JOIN products p ON m.asin = p.asin").fetchone()[0]
        print(f"✅ Updated {updated_count} records in 'products'.")

        # 3. Ensure all Parents from Excel exist in 'product_parents'
        print("🛠️ Synchronizing 'product_parents' from Excel...")
        
        # We need to get unique parent info from the mapping (since many children share one parent)
        parent_info = mapping_df.select([
            pl.col("correct_parent_asin").alias("parent_asin"),
            pl.col("category"),
            pl.col("brand"),
            pl.col("niche")
        ]).unique(subset=["parent_asin"])
        
        conn.execute("CREATE OR REPLACE TEMPORARY TABLE excel_parents AS SELECT * FROM parent_info")
        
        # Insert missing parents
        insert_parents_query = """
        INSERT INTO product_parents (parent_asin, category, brand, niche, title)
        SELECT m.parent_asin, m.category, m.brand, m.niche, 'Imported from Excel'
        FROM excel_parents m
        LEFT JOIN product_parents p ON m.parent_asin = p.parent_asin
        WHERE p.parent_asin IS NULL
        """
        conn.execute(insert_parents_query)
        inserted_parents = conn.execute("SELECT count(*) FROM excel_parents m JOIN product_parents p ON m.parent_asin = p.parent_asin WHERE p.title = 'Imported from Excel'").fetchone()[0]
        print(f"✅ Inserted {inserted_parents} new parents into 'product_parents'.")

        # Update existing parents if they are 'unclassified' or 'Unknown'
        update_parents_query = """
        UPDATE product_parents
        SET category = m.category,
            brand = m.brand,
            niche = m.niche
        FROM excel_parents m
        WHERE product_parents.parent_asin = m.parent_asin
        AND (product_parents.category IS NULL OR product_parents.category IN ('unclassified', 'Unknown'))
        """
        conn.execute(update_parents_query)
        print("✅ Refined categories/niches for existing parents.")

        # 4. Final Cleanup: Remove invalid orphans
        # Orphans are products where parent_asin = asin AND they are NOT supposed to be parents (based on Excel)
        # However, it's safer to just look for products whose parent_asin is NOT in product_parents
        print("📊 Analyzing remaining orphans...")
        orphans = conn.execute("""
            SELECT count(*) FROM products 
            WHERE parent_asin NOT IN (SELECT parent_asin FROM product_parents)
        """).fetchone()[0]
        print(f"⚠️ Found {orphans} remaining products with invalid parent mappings.")

        # 5. Summary Statistics
        total_products = conn.execute("SELECT count(*) FROM products").fetchone()[0]
        distinct_parents_in_products = conn.execute("SELECT count(DISTINCT parent_asin) FROM products").fetchone()[0]
        total_parents = conn.execute("SELECT count(*) FROM product_parents").fetchone()[0]

        print("\n--- FINAL SUMMARY ---")
        print(f"Total Products: {total_products}")
        print(f"Distinct Parent ASINs in Products: {distinct_parents_in_products}")
        print(f"Total Records in product_parents: {total_parents}")
        print("----------------------")

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup()
