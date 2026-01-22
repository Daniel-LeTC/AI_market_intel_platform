import duckdb
import shutil
import time
from scout_app.core.stats_engine import StatsEngine
from scout_app.core.config import Settings

def backfill():
    # 1. Identify Target (Standby) DB
    active_db = Settings.get_active_db_path()
    target_db = Settings.get_standby_db_path()
    
    print(f"[Blue-Green] Active: {active_db.name}, Target: {target_db.name}")
    print(f"🚀 Starting Backfill Process...")

    # 2. Sync: Copy Active -> Target
    try:
        if active_db.exists():
            print(f"📋 Syncing {active_db.name} -> {target_db.name}...")
            shutil.copy(active_db, target_db)
    except Exception as e:
        print(f"❌ Sync Failed: {e}")
        return

    # 3. Process on Target DB (No Lock on Active)
    print(f"⚙️ Processing on {target_db.name}...")
    engine = StatsEngine(db_path=str(target_db))
    
    # Get all ASINs from Target
    with duckdb.connect(str(target_db)) as conn:
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
    
    print(f"\n\n✅ Calculation Completed on Standby DB!")
    print(f"⏱️ Duration: {duration:.2f}s (Avg: {duration/total:.2f}s/asin)")
    print(f"📈 Success: {success}")
    print(f"📉 Errors: {errors}")

    # 4. Swap DBs
    print("🔄 Swapping Database to apply changes...")
    Settings.swap_db()
    print(f"✅ DONE! Active DB is now {target_db.name}")

if __name__ == "__main__":
    backfill()