import duckdb
import pandas as pd
import json
import os
import glob
import sys

# Setup paths
STAGING_DATA = "staging_data"
METADATA_DIR = "staging_data_local/20260129_data/new_product_metadata"

def get_db_connection():
    try:
        # Hardcode fallback for audit
        return duckdb.connect("scout_app/database/scout_a.duckdb")
    except:
        return duckdb.connect("scout_app/database/scout.duckdb")

def load_excel_breakdown(file_path):
    try:
        df = pd.read_excel(file_path, nrows=500) 
        cols = [c for c in df.columns if "reviewSummary" in c and "percentage" in c]
        if not cols:
            return {}
        
        breakdowns = {}
        for _, row in df.iterrows():
            asin = row.get("asin")
            if not asin:
                 asin = row.get("parentAsin")
            if not asin: continue
            
            bd = {
                "5": row.get("reviewSummary/fiveStar/percentage", 0),
                "4": row.get("reviewSummary/fourStar/percentage", 0),
                "3": row.get("reviewSummary/threeStar/percentage", 0),
                "2": row.get("reviewSummary/twoStar/percentage", 0),
                "1": row.get("reviewSummary/oneStar/percentage", 0)
            }
            breakdowns[asin] = bd
        return breakdowns
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}

def audit():
    conn = get_db_connection()
    
    print("--- DB SAMPLES ---")
    # Hardcode known ASIN for verification
    target_asin = 'B0C1N8DJX7' 
    samples = conn.execute(f"SELECT category, asin, real_total_ratings, rating_breakdown FROM products WHERE asin = '{target_asin}'").fetchall()
    
    if not samples:
        print(f"ASIN {target_asin} not found in DB!")
        return
    
    db_map = {}
    for row in samples:
        db_map[row[1]] = {"total": row[2], "bd": row[3]}
    
    print(json.dumps(db_map, indent=2))
    
    print("--- METADATA FILES (JSONL) ---")
    meta_files = glob.glob(f"{METADATA_DIR}/*.jsonl")
    found_meta = {}
    for mf in meta_files:
        try:
            with open(mf, 'r') as f:
                for i, line in enumerate(f):
                    if i > 5000: break 
                    try:
                        d = json.loads(line)
                        asin = d.get("asin")
                        if asin in db_map:
                            has_bd = "reviewSummary" in str(d) or "fiveStar" in str(d)
                            found_meta[asin] = {
                                "file": os.path.basename(mf),
                                "countReview": d.get("countReview"),
                                "has_breakdown": has_bd
                            }
                    except: pass
        except: pass
    print(json.dumps(found_meta, indent=2))

    print("--- REVIEW FILES (EXCEL) ---")
    review_files = glob.glob(f"{STAGING_DATA}/*.xlsx")
    found_reviews = {}
    for rf in review_files:
        if "raw_scrape" not in rf: continue
        bds = load_excel_breakdown(rf)
        for asin in db_map:
            if asin in bds:
                found_reviews[asin] = {
                    "file": os.path.basename(rf),
                    "breakdown_sample": bds[asin]
                }
    print(json.dumps(found_reviews, indent=2))

if __name__ == "__main__":
    audit()