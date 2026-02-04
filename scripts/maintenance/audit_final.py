import duckdb
import json
import pandas as pd
import sys
import os

# Add root path to find config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scout_app.core.config import Settings

def audit_local():
    db_path = "/app/scout_app/database/scout_a.duckdb" # Docker path
    print(f"🔍 Auditing {db_path}...")
    conn = duckdb.connect(db_path)
    
    # 1. Parents Check
    print("\n--- 1. PARENTS BY CATEGORY ---")
    try:
        df_p = conn.execute("SELECT category, COUNT(*) as cnt FROM product_parents GROUP BY 1 ORDER BY 2 DESC").df()
        print(df_p.to_string(index=False))
    except:
        print("Table product_parents not found or empty.")
    
    # 2. Products Check
    print("\n--- 2. PRODUCTS STATS & SUSPICIOUS DATA ---")
    df_prod = conn.execute("""
        SELECT 
            category,
            COUNT(*) as total_asins,
            COUNT(rating_breakdown) as have_breakdown,
            CAST(AVG(real_total_ratings) AS INTEGER) as avg_ratings
        FROM products 
        GROUP BY 1
    """).df()
    print(df_prod.to_string(index=False))
    
    # 3. Suspicious Rounding Check
    print("\n--- 3. SUSPICIOUS ROUNDING (Total % 100 == 0) ---")
    df_sus = conn.execute("""
        SELECT asin, category, real_total_ratings, rating_breakdown
        FROM products
        WHERE real_total_ratings > 99 
        AND real_total_ratings % 100 = 0
        LIMIT 10
    """).df()
    if df_sus.empty:
        print("✅ No suspicious rounding detected in sample.")
    else:
        print(df_sus.to_string(index=False))

    # 4. Low Rating Integrity Check
    print("\n--- 4. LOW RATING INTEGRITY (< 500 ratings) ---")
    df_low = conn.execute("""
        SELECT asin, category, real_total_ratings, rating_breakdown
        FROM products
        WHERE real_total_ratings > 0 AND real_total_ratings < 500
        AND rating_breakdown IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 5
    """).df()
    print(df_low.to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    audit_local()