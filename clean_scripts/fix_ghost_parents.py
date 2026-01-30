import polars as pl
import os
from pathlib import Path

# --- CONFIG ---
INPUT_FILE = "staging_data/RnD_Test_Ingest.xlsx"
OUTPUT_FILE = "staging_data/RnD_Test_Ingest_Fixed.xlsx"

def fix():
    print(f"🔍 Reading {INPUT_FILE}...")
    if not os.path.exists(INPUT_FILE):
        print("❌ File not found.")
        return

    # Read everything as string to prevent schema issues during processing
    df = pl.read_excel(INPUT_FILE, infer_schema_length=0)
    
    # 1. Identify Ghosts
    all_asins = set(df["ASIN"].drop_nulls().unique().to_list())
    all_parents = set(df["Parent Asin"].drop_nulls().unique().to_list())
    ghost_ids = all_parents - all_asins
    
    print(f"📊 Found {len(all_asins)} ASIN rows.")
    print(f"👻 Found {len(ghost_ids)} Ghost Parents (ASINs used as Parent but missing their own row).")

    if not ghost_ids:
        print("✨ No ghosts found. Nothing to do.")
        return

    # 2. Generate Parent Rows from Children
    ghost_rows = []
    
    for gid in ghost_ids:
        # Get all children for this ghost parent
        children = df.filter(pl.col("Parent Asin") == gid)
        
        if children.is_empty():
            continue
            
        # Strategy: Choose a representative child to act as Parent
        # We try to sort by Sales Rank (if available) to pick the best one
        # Sales Rank is often like '1,234 in Kitchen', need to extract number
        try:
            # Simple heuristic: just take the first one for now, or sort if Sales Rank looks clean
            # For robustness in ad-hoc script, we take the first child.
            representative = children.head(1).clone()
            
            # Update ID to be the Parent itself
            representative = representative.with_columns([
                pl.lit(gid).alias("ASIN"),
                pl.lit(gid).alias("Parent Asin"),
                # Optional: Mark this as an auto-generated parent row
                pl.lit("AUTO_GENERATED_PARENT").alias("Status Asin")
            ])
            
            ghost_rows.append(representative)
        except Exception as e:
            print(f"⚠️ Error processing ghost {gid}: {e}")

    if ghost_rows:
        df_ghosts = pl.concat(ghost_rows)
        # 3. Merge and Save
        df_final = pl.concat([df, df_ghosts])
        
        print(f"✅ Created {len(df_ghosts)} new parent rows.")
        print(f"💾 Saving to {OUTPUT_FILE}...")
        
        # Use xlsxwriter for better excel support if needed, but polars default is fine
        df_final.write_excel(OUTPUT_FILE)
        print("🏁 Done!")
    else:
        print("∅ No rows generated.")

if __name__ == "__main__":
    fix()
