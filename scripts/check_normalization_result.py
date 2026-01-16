import duckdb
import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

def check_results():
    conn = duckdb.connect('scout_app/database/scout.duckdb')
    
    print("\n=== MAPPING PREVIEW (Top Grouped) ===")
    query = """
        SELECT 
            m.category,
            m.standard_aspect, 
            COUNT(r.review_id) as freq,
            STRING_AGG(DISTINCT r.aspect, ', ') as raw_variations
        FROM review_tags r
        JOIN aspect_mapping m ON lower(trim(r.aspect)) = lower(trim(m.raw_aspect))
        GROUP BY 1, 2
        ORDER BY freq DESC
        LIMIT 20
    """
    df = conn.execute(query).df()
    print(df)
    conn.close()

if __name__ == "__main__":
    check_results()
