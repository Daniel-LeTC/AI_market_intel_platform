import duckdb
import sys
from pathlib import Path

# Add root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scout_app.core.config import Settings
from scout_app.core.stats_engine import StatsEngine

def fix_variations():
    db_path = Settings.get_active_db_path()
    print(f"🔧 Fixing Variation Counts in {db_path}...")
    
    with duckdb.connect(str(db_path)) as conn:
        # 1. Find rows with NULL or 0 variation_count
        targets = conn.execute("SELECT asin FROM products WHERE variation_count IS NULL OR variation_count = 0").fetchall()
        print(f"👉 Found {len(targets)} ASINs to fix.")
        
        updated_count = 0
        engine = StatsEngine(db_path=str(db_path))

        for row in targets:
            asin = row[0]
            
            # 2. Count distinct child_asin from reviews
            # Note: reviews table links via parent_asin column
            v_count = conn.execute("SELECT COUNT(DISTINCT child_asin) FROM reviews WHERE parent_asin = ?", [asin]).fetchone()[0]
            
            # Fallback: If reviews has 0 (maybe it's a child row?), check if it IS a child in reviews
            if v_count == 0:
                 # Check if this ASIN appears as a child_asin in reviews
                 is_child = conn.execute("SELECT COUNT(*) FROM reviews WHERE child_asin = ?", [asin]).fetchone()[0]
                 if is_child > 0:
                     v_count = 1 # It's a single child variant

            if v_count > 0:
                print(f"   ✅ Fixing {asin}: {v_count} variations")
                conn.execute("UPDATE products SET variation_count = ? WHERE asin = ?", [v_count, asin])
                updated_count += 1
                
                # 3. Trigger Stats Recalc
                engine.calculate_and_save(asin)
            else:
                print(f"   ⚠️  Skipping {asin} (No reviews data found)")

        print(f"\n🎉 Fixed {updated_count} ASINs.")

if __name__ == "__main__":
    fix_variations()
