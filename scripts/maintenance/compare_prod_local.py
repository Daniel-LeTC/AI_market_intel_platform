import duckdb
import pandas as pd
import json

def compare_dbs():
    local_db = "scout_app/database/scout_a.duckdb"
    gcp_db = "scout_gcp.duckdb"
    
    print(f"🔄 Comparing Local ({local_db}) vs GCP ({gcp_db})...")
    
    con_local = duckdb.connect(local_db)
    con_gcp = duckdb.connect(gcp_db)
    
    # 1. Summary Comparison
    query_summary = """
        SELECT 
            category, 
            COUNT(*) as total, 
            COUNT(rating_breakdown) as has_bd
        FROM products 
        WHERE category IN ('tumbler', 'book', 'comforter')
        GROUP BY 1
    """
    
    df_local = con_local.execute(query_summary).df()
    df_gcp = con_gcp.execute(query_summary).df()
    
    print("\n--- SUMMARY COMPARISON ---")
    merged = pd.merge(df_local, df_gcp, on='category', suffixes='_LOCAL _GCP'.split(' '))
    print(merged.to_string(index=False))
    
    # 2. Detail Check for fixed ASINs
    query_diff = """
        SELECT asin, category, rating_breakdown
        FROM products
        WHERE rating_breakdown IS NOT NULL
        AND category IN ('tumbler', 'book')
    """
    
    fixed_asins = con_local.execute(query_diff).df()
    gcp_check = con_gcp.execute("SELECT asin, rating_breakdown FROM products WHERE rating_breakdown IS NOT NULL").df()
    
    # Identify ASINs in Local that are NULL or different in GCP
    newly_fixed = fixed_asins[~fixed_asins['asin'].isin(gcp_check['asin'])]
    
    print(f"\n--- NEWLY FIXED ASINS (In Local but not in GCP) ---")
    print(f"Total newly fixed: {len(newly_fixed)}")
    if not newly_fixed.empty:
        print("\nSample of fixed ASINs:")
        print(newly_fixed.head(10).to_string(index=False))
    
    con_local.close()
    con_gcp.close()

if __name__ == "__main__":
    compare_dbs()