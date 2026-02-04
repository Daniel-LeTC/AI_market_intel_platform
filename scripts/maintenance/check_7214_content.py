import pandas as pd
import duckdb
import os

# 1. Get ASINs from DB
con = duckdb.connect('/app/scout_app/database/scout_a.duckdb')
missing_asins_df = con.execute("""
    SELECT asin, parent_asin 
    FROM products 
    WHERE category = 'tumbler' AND rating_breakdown IS NULL
""").df()

missing_list = set(missing_asins_df['asin'].tolist())
parent_list = set(missing_asins_df['parent_asin'].tolist())
all_targets = missing_list.union(parent_list)

print(f"Target count: {len(all_targets)}")

# 2. Read Excel
excel_path = "staging_data/raw_scrape_20260129_040351_C8FL4HcUW6K9O7b7D.xlsx"
df_excel = pd.read_excel(excel_path)

# 3. Match
found_asins = set()
for col in ['asin', 'variationId', 'parentAsin']:
    if col in df_excel.columns:
        matches = df_excel[df_excel[col].isin(all_targets)][col].unique().tolist()
        found_asins.update(matches)

print("\n--- MATCHED ASINS ---")
if not found_asins:
    print("None found")
else:
    print(f"Found: {len(found_asins)}")
    for a in sorted(list(found_asins)):
        role = "PARENT" if a in parent_list else "CHILD"
        print(f"- {a} ({role})")

con.close()