import json
from scout_app.core.stats_engine import StatsEngine
from scout_app.core.config import Settings

def test_engine():
    asin = "B0BNZP6H6K"
    print(f"🚀 Testing StatsEngine for ASIN: {asin}")
    
    engine = StatsEngine()
    
    # 1. Test Calculation
    print("\n--- 1. Calculating All Metrics ---")
    data = engine.calculate_all(asin)
    print(json.dumps(data, indent=2)[:1000] + "...") # Print partial
    
    # 2. Test Saving
    print("\n--- 2. Saving to DB ---")
    engine.save_to_db(asin, data)
    print("✅ Saved to product_stats")
    
    # 3. Verify in DB
    print("\n--- 3. Verifying in DB ---")
    import duckdb
    with duckdb.connect(str(Settings.get_active_db_path())) as conn:
        res = conn.execute("SELECT metrics_json FROM product_stats WHERE asin = ?", [asin]).fetchone()
        if res:
            stored_data = json.loads(res[0])
            print(f"✅ Stored ASIN: {stored_data['asin']}")
            print(f"✅ Stored KPIs: {stored_data['kpis']}")
        else:
            print("❌ Failed to find record in DB.")

if __name__ == "__main__":
    test_engine()
