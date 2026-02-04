import duckdb
import pandas as pd
import glob
import os
import json
import sys

# Add root path
sys.path.append("/app")
from scout_app.core.config import Settings

STAGING_DIR = "/app/staging_data"  # Docker path

def get_db_path():
    try:
        return str(Settings.get_active_db_path())
    except:
        return "/app/scout_app/database/scout_a.duckdb"

def sync_breakdowns():
    db_path = get_db_path()
    print(f"🚀 Syncing Breakdowns to {db_path}...")
    
    conn = duckdb.connect(db_path)
    
    # 1. Scan Excel Files (Priority Source)
    excel_files = glob.glob(f"{STAGING_DIR}/*.xlsx")
    updates = {}
    
    for f in excel_files:
        if "raw_scrape" not in f and "Scraper_Data" not in f and "dataset_amazon" not in f:
            continue
            
        print(f"📂 Reading {os.path.basename(f)}...")
        try:
            df = pd.read_excel(f)
            # Find breakdown columns
            pct_cols = [c for c in df.columns if "reviewSummary" in c and "percentage" in c]
            if not pct_cols:
                continue
                
            for _, row in df.iterrows():
                asin = row.get("asin")
                if not asin:
                    asin = row.get("parentAsin")
                if not asin: continue
                
                # Check valid breakdown
                try:
                    bd = {
                        "5": float(row.get("reviewSummary/fiveStar/percentage", 0) or 0),
                        "4": float(row.get("reviewSummary/fourStar/percentage", 0) or 0),
                        "3": float(row.get("reviewSummary/threeStar/percentage", 0) or 0),
                        "2": float(row.get("reviewSummary/twoStar/percentage", 0) or 0),
                        "1": float(row.get("reviewSummary/oneStar/percentage", 0) or 0)
                    }
                    
                    total_pct = sum(bd.values())
                    if total_pct > 0:
                        updates[asin] = json.dumps(bd)
                except:
                    pass
        except Exception as e:
            print(f"❌ Error reading {f}: {e}")

    print(f"✅ Found {len(updates)} ASINs with breakdowns.")
    
    # 2. Batch Update DB
    count = 0
    for asin, bd_json in updates.items():
        conn.execute("""
            UPDATE products 
            SET rating_breakdown = ? 
            WHERE asin = ?
        """, [bd_json, asin])
        count += 1
        
    print(f"💾 Updated {count} rows in DB.")
    conn.close()

if __name__ == "__main__":
    sync_breakdowns()
