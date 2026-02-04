import pandas as pd
import duckdb
import os

def check_files():
    # 1. Get Target ASINs
    try:
        con = duckdb.connect('/app/scout_app/database/scout_a.duckdb')
        missing_asins_df = con.execute("""
            SELECT asin, parent_asin 
            FROM products 
            WHERE category = 'tumbler' AND rating_breakdown IS NULL
        """).df()
        
        missing_list = set(missing_asins_df['asin'].tolist())
        parent_list = set(missing_asins_df['parent_asin'].tolist())
        all_targets = missing_list.union(parent_list)
        con.close()
        print(f"Total Targets: {len(all_targets)}")
    except Exception as e:
        print(f"DB Error: {e}")
        return

    files = [
        "dataset_amazon-reviews-scraper_2026-01-28_08-59-33-996.xlsx",
        "dataset_amazon-reviews-scraper_2026-01-28_09-12-01-723.xlsx"
    ]

    for f in files:
        print(f"\n--- Checking {f} ---")
        if not os.path.exists(f):
            print("File not found at root, checking staging...")
            f = os.path.join("staging_data", f)
            if not os.path.exists(f):
                print("Still not found")
                continue
            
        try:
            df = pd.read_excel(f)
            print(f"Rows: {len(df)}")
            
            # Check columns for breakdown
            bd_cols = [c for c in df.columns if "reviewSummary" in c]
            print(f"Has Breakdown Cols: {len(bd_cols) > 0}")
            
            # Match ASINs
            found = set()
            for col in ['asin', 'variationId', 'parentAsin']:
                if col in df.columns:
                    matches = df[df[col].isin(all_targets)][col].unique().tolist()
                    found.update(matches)
            
            if found:
                print(f"Found {len(found)} matching ASINs!")
                print(f"Sample: {sorted(list(found))[:5]}")
            else:
                print("No matching ASINs found.")
        except Exception as e:
            print(f"Error reading file: {e}")

if __name__ == "__main__":
    check_files()