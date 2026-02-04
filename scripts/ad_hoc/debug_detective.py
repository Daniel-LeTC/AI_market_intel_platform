
import duckdb
from scout_app.core.config import Settings
import pandas as pd

def test_detective_query(asin, aspect_input):
    db_path = str(Settings.get_active_db_path())
    print(f"Using DB: {db_path}")
    
    conn = duckdb.connect(db_path, read_only=True)
    
    # 1. Check if 'Product' exists in review_tags
    print(f"\n--- 1. Check 'Product' tags for {asin} ---")
    tags = conn.execute(f"SELECT aspect, sentiment, quote FROM review_tags WHERE parent_asin = '{asin}' AND aspect ILIKE '{aspect_input}' LIMIT 5").df()
    print(tags)

    # 2. Check mapping for 'Product'
    print(f"\n--- 2. Check Mapping for '{aspect_input}' ---")
    mapping = conn.execute(f"SELECT * FROM aspect_mapping WHERE raw_aspect ILIKE '{aspect_input}'").df()
    print(mapping)
    
    # 3. Run the Exact Query from Detective Agent
    print(f"\n--- 3. Run Detective Query for '{aspect_input}' ---")
    parent_asin = asin
    aspect = aspect_input
    
    # Simulate the logic in search_review_evidence
    clauses = ["rt.parent_asin = ?"]
    params = [parent_asin]
    
    # The problematic part?
    clauses.append("lower(trim(am.standard_aspect)) = lower(trim(?))")
    params.append(aspect)
    
    where_stmt = " AND ".join(clauses)
    
    query = f"""
        SELECT 
            COALESCE(am.standard_aspect, rt.aspect) as aspect,
            rt.sentiment, 
            rt.quote
        FROM review_tags rt
        JOIN reviews r ON rt.review_id = r.review_id
        LEFT JOIN aspect_mapping am ON lower(trim(rt.aspect)) = lower(trim(am.raw_aspect))
        WHERE {where_stmt}
        LIMIT 5
    """
    
    try:
        res = conn.execute(query, params).df()
        print(res)
    except Exception as e:
        print(f"Query Failed: {e}")

if __name__ == "__main__":
    test_detective_query('B0835K217P', 'Product')
