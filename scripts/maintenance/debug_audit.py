import sys
import os
import duckdb
import pandas as pd
import json

sys.path.append(os.getcwd())
from scout_app.core.config import Settings

try:
    db_path = Settings.get_active_db_path()
    print(f"DEBUG: Active DB Path: {db_path}")
except:
    db_path = "scout_app/database/scout.duckdb"

if not os.path.exists(db_path):
    import glob
    dbs = glob.glob("scout_app/database/*.duckdb")
    if dbs:
        db_path = dbs[0]
        print(f"DEBUG: Found alternative DB: {db_path}")
    else:
        print("No DB found")
        sys.exit(1)

con = duckdb.connect(db_path)

print("--- SUMMARY ---")
try:
    df = con.execute("""
        SELECT 
            p.category, 
            COUNT(p.asin) as cnt, 
            COUNT(p.real_total_ratings) as has_meta, 
            CAST(AVG(COALESCE(r.cnt, 0)) AS INTEGER) as avg_rev, 
            CAST(AVG(p.real_total_ratings) AS INTEGER) as avg_meta 
        FROM products p
        LEFT JOIN (SELECT parent_asin, COUNT(*) as cnt FROM reviews GROUP BY parent_asin) r
        ON p.asin = r.parent_asin
        GROUP BY p.category
    """).df()
    print(df.to_string())
except Exception as e:
    print(f"Summary Error: {e}")

print("\n--- DETAILS ---")
try:
    df2 = con.execute("""
        SELECT 
            p.category, 
            p.asin, 
            COALESCE(r.cnt, 0) as reviews_count, 
            p.real_total_ratings, 
            p.rating_breakdown 
        FROM products p
        LEFT JOIN (SELECT parent_asin, COUNT(*) as cnt FROM reviews GROUP BY parent_asin) r
        ON p.asin = r.parent_asin
        WHERE p.category IN ('tumbler', 'book', 'comforter')
    """).df()

    for cat in df2['category'].unique():
        print(f"\nCAT: {cat}")
        print(df2[df2['category'] == cat].head(3).to_string())
except Exception as e:
    print(f"Details Error: {e}")

con.close()