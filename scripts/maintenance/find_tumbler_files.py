import pandas as pd
import glob
import os

targets = [6279, 2129, 7214]
files = glob.glob("staging_data/*.xlsx")

print("--- SCANNING FOR MATCHING FILES ---")
for f in files:
    try:
        df = pd.read_excel(f)
        count = len(df)
        if count in targets:
            print(f"✅ MATCH FOUND: {os.path.basename(f)} (Rows: {count})")
            # Check for breakdown columns
            has_bd = any("reviewSummary" in c for c in df.columns)
            print(f"   Has Breakdown Cols: {has_bd}")
            # Check ASIN col
            asin_col = next((c for c in df.columns if c.lower() in ['asin', 'parentasin']), "N/A")
            print(f"   ASIN Col: {asin_col}")
            if asin_col != "N/A":
                print(f"   Sample ASINs: {df[asin_col].head(3).tolist()}")
    except Exception as e:
        pass
