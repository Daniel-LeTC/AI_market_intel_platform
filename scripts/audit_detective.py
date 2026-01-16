import duckdb
import pandas as pd
from scout_app.core.config import Settings

def audit():
    db_path = str(Settings.get_active_db_path())
    conn = duckdb.connect(db_path, read_only=True)
    asin = 'B09FV1J5XC'

    print(f"=== AUDIT REPORT FOR ASIN: {asin} ===")
    
    # 1. Sentiment Check
    q_sentiment = """
        SELECT 
            COALESCE(am.standard_aspect, rt.aspect) as aspect,
            COUNT(*) as mentions,
            ROUND(SUM(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pos_pct
        FROM review_tags rt
        LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
        WHERE rt.parent_asin = ?
        GROUP BY 1
        HAVING mentions >= 3
        ORDER BY mentions DESC
    """
    df = conn.execute(q_sentiment, [asin]).df()
    print("\n--- Top Aspects Sentiment ---")
    print(df)

    # 2. Quote Verification
    print("\n--- Quote Verification ---")
    quotes_to_check = [
        "bottom sheet is too small",
        "bedding was very very small",
        "Fitted sheet is way too big for a twin",
        "curtains are shorter than the window",
        "Inside stuffing too-small"
    ]
    
    for q_text in quotes_to_check:
        res = conn.execute("SELECT count(*) FROM reviews WHERE parent_asin = ? AND text ILIKE ?", [asin, f"%{q_text}%"]).fetchone()[0]
        status = "✅ FOUND" if res > 0 else "❌ NOT FOUND"
        print(f"Quote: '{q_text}' -> {status}")

    # 3. Specific Keyword Search (Material/Thickness)
    print("\n--- Keyword Context Check ---")
    keywords = ["slippery", "silky", "thin", "cheap", "tears", "ripped"]
    for kw in keywords:
        res = conn.execute("SELECT count(*) FROM reviews WHERE parent_asin = ? AND text ILIKE ?", [asin, f"%{kw}%"]).fetchone()[0]
        print(f"Keyword '{kw}': {res} mentions")

    conn.close()

if __name__ == "__main__":
    audit()
