import duckdb
import sys
import time
from pathlib import Path
from tqdm import tqdm

# Add root to sys.path
sys.path.append("/app")
from scout_app.core.config import Settings
from scout_app.core.stats_engine import StatsEngine

def recalc_targets(delay=0.05):
    db_path = Settings.get_active_db_path()
    print(f"🔄 Starting TARGETED Stats Recalculation (Tumbler & Book) on {db_path}...")
    
    with duckdb.connect(str(db_path)) as conn:
        # Filter logic: Only Tumbler, Book
        sql = """
            SELECT asin FROM products 
            WHERE category IN ('tumbler', 'book')
        """
        rows = conn.execute(sql).fetchall()
        asins = [r[0] for r in rows]
    
    print(f"🚀 Found {len(asins)} ASINs to process.")
    
    engine = StatsEngine(db_path=str(db_path))
    
    success_count = 0
    error_count = 0
    
    for asin in tqdm(asins, desc="Processing"):
        try:
            engine.calculate_and_save(asin)
            success_count += 1
            time.sleep(delay) 
        except Exception as e:
            print(f"\n❌ Error on {asin}: {e}")
            error_count += 1

    print(f"\n✨ Done! Success: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    recalc_targets()