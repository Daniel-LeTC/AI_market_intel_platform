import duckdb
import sys
import time
from pathlib import Path
from tqdm import tqdm

# Add root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scout_app.core.config import Settings
from scout_app.core.stats_engine import StatsEngine

def recalc_all(delay=0.1):
    db_path = Settings.get_active_db_path()
    print(f"🔄 Starting Full Stats Recalculation on {db_path}...")
    print(f"🐌 Low CPU Mode: {delay}s delay per ASIN.")
    
    with duckdb.connect(str(db_path)) as conn:
        # Get all ASINs (Parents preferred)
        print("📥 Fetching ASIN list...")
        rows = conn.execute("SELECT asin FROM products").fetchall()
        asins = [r[0] for r in rows]
    
    print(f"🚀 Found {len(asins)} ASINs to process.")
    
    engine = StatsEngine(db_path=str(db_path))
    
    for asin in tqdm(asins, desc="Processing"):
        try:
            engine.calculate_and_save(asin)
            time.sleep(delay) # Throttle CPU usage
        except Exception as e:
            print(f"\n❌ Error on {asin}: {e}")

    print("\n✨ All Done!")

if __name__ == "__main__":
    # Default delay 0.1s. Can increase if still hot.
    recalc_all(delay=0.1)
