import duckdb
from scout_app.core.stats_engine import StatsEngine
from scout_app.core.config import Settings
import time

def backfill():
    db_path = Settings.get_active_db_path()
    print(f"🚀 Starting Backfill on {db_path.name}...")
    
    engine = StatsEngine(db_path=str(db_path))
    
    # 1. Get all ASINs
    with duckdb.connect(str(db_path)) as conn:
        asins = [row[0] for row in conn.execute("SELECT asin FROM products").fetchall()]
    
    total = len(asins)
    print(f"📦 Found {total} products to process.")
    
    start_time = time.time()
    success = 0
    errors = 0
    
    for i, asin in enumerate(asins):
        try:
            print(f"[{i+1}/{total}] Processing {asin}...", end="\r")
            engine.calculate_and_save(asin)
            success += 1
        except Exception as e:
            print(f"\n❌ Error processing {asin}: {e}")
            errors += 1
            
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n\n✅ Backfill Completed!")
    print(f"⏱️ Duration: {duration:.2f}s (Avg: {duration/total:.2f}s/asin)")
    print(f"📈 Success: {success}")
    print(f"📉 Errors: {errors}")

if __name__ == "__main__":
    backfill()
