import polars as pl
import duckdb
from pathlib import Path
from scout_app.core.config import Settings


def fix_ssot():
    excel_path = Path("Kid Comforter Set_Thoai RnD_19-12-2025.xlsx")
    print(f"📖 Loading SSOT from Excel: {excel_path}")
    df_excel = pl.read_excel(excel_path)

    # 1. Map Child -> Real Parent from Excel
    # For every ASIN in Excel, it tells us who its Parent is.
    mapping_df = df_excel.select([pl.col("ASIN").alias("asin"), pl.col("Parent Asin").alias("real_parent")]).filter(
        pl.col("real_parent").is_not_null()
    )

    # 2. Get list of 902 Unique Parents
    parents_df = (
        df_excel.select(
            [
                pl.col("Parent Asin").alias("parent_asin"),
                pl.col("Title").alias("title"),
                pl.col("Brand").alias("brand"),
                pl.col("Main Niche").alias("niche"),
            ]
        )
        .unique(subset=["parent_asin"])
        .filter(pl.col("parent_asin").is_not_null())
    )

    for db_p in [Settings.get_active_db_path(), Settings.get_standby_db_path()]:
        print(f"⚡ Applying SSOT to {db_p.name}...")
        with duckdb.connect(str(db_p)) as conn:
            conn.register("ssot_map", mapping_df.to_arrow())
            conn.register("ssot_parents", parents_df.to_arrow())

            # 1. ENSURE ALL PARENTS EXIST FIRST (To satisfy Foreign Key)
            conn.execute("""
                INSERT OR IGNORE INTO product_parents (parent_asin, category, title, brand, niche, verification_status)
                SELECT parent_asin, 'comforter', title, brand, niche, 'GOLDEN'
                FROM ssot_parents
            """)

            # 2. RESET PRODUCTS: Force all known parents to be their own parent
            conn.execute("""
                UPDATE products 
                SET parent_asin = asin 
                WHERE asin IN (SELECT parent_asin FROM ssot_parents)
            """)

            # 3. FIX VARIATIONS: Link children to real parents based on Excel
            conn.execute("""
                UPDATE products 
                SET parent_asin = m.real_parent 
                FROM ssot_map m 
                WHERE products.asin = m.asin
            """)

            # D. CLEANUP: Delete any comforter parent NOT in the 902 list
            conn.execute("""
                DELETE FROM product_parents 
                WHERE category = 'comforter' 
                AND parent_asin NOT IN (SELECT parent_asin FROM ssot_parents)
            """)

            # E. RE-LINK REVIEWS: Force reviews to point to Excel parents
            conn.execute("""
                UPDATE reviews 
                SET parent_asin = m.real_parent
                FROM ssot_map m 
                WHERE reviews.child_asin = m.asin
            """)

            count = conn.execute("SELECT count(*) FROM product_parents WHERE category = 'comforter'").fetchone()[0]
            print(f"✅ {db_p.name} synchronized. Comforter Parent count: {count}")


if __name__ == "__main__":
    fix_ssot()
