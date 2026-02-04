import json
import duckdb
import os
from pathlib import Path
import sys

# Add root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scout_app.core.config import Settings

FILES_TO_IMPORT = [
    "staging_data_local/20260129_data/new_product_metadata/39_asin.jsonl",
    "staging_data_local/20260129_data/new_product_metadata/dataset_amazon-product-details-scraper_2026-01-29_03-21-49-183.jsonl",
    "staging_data_local/20260129_data/new_product_metadata/dataset_amazon-product-details-scraper_2026-01-29_03-23-57-967.jsonl"
]

def backfill():
    db_path = str(Settings.get_active_db_path())
    print(f"🚀 Connecting to {db_path}...")
    conn = duckdb.connect(db_path)
    
    total_processed = 0
    total_inserted = 0
    
    for file_path in FILES_TO_IMPORT:
        if not os.path.exists(file_path):
            print(f"⚠️ File not found: {file_path}")
            continue
            
        print(f"📦 Processing {file_path}...")
        with open(file_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("statusCode") != 200:
                        continue
                        
                    asin = data.get("asin")
                    if not asin:
                        continue
                        
                    title = data.get("title", "")
                    # Extract brand from manufacturer (usually "by Brand (Author)")
                    raw_brand = data.get("manufacturer", "N/A")
                    brand = raw_brand.replace("by ", "").split("(")[0].strip() if "N/A" not in raw_brand else "N/A"
                    
                    image = data.get("imageUrlList", [None])[0]
                    
                    # Logic for Category: If it's the book dataset, category = 'book'
                    category = "book" if "draw" in title.lower() or "book" in title.lower() else "comforter"
                    niche = "How to Draw" if "how to draw" in title.lower() else None

                    # Parse Rating
                    raw_rating = data.get("productRating", "0")
                    try:
                        if isinstance(raw_rating, str):
                            avg_rating = float(raw_rating.split(" ")[0])
                        else:
                            avg_rating = float(raw_rating)
                    except:
                        avg_rating = 0.0

                    # Parse Total Ratings
                    total_ratings = data.get("countReview", 0)

                    # 1. Update Parent Hierarchy
                    conn.execute("""
                        INSERT INTO product_parents (parent_asin, category, niche, title, brand, image_url, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, now())
                        ON CONFLICT (parent_asin) DO UPDATE SET
                            category = COALESCE(excluded.category, product_parents.category),
                            niche = COALESCE(excluded.niche, product_parents.niche),
                            title = COALESCE(excluded.title, product_parents.title),
                            brand = COALESCE(excluded.brand, product_parents.brand),
                            image_url = COALESCE(excluded.image_url, product_parents.image_url),
                            last_updated = now()
                    """, [asin, category, niche, title, brand, image])

                    # 2. Update Product Metadata (The Missing Link)
                    # We treat these as Parents, so parent_asin = asin
                    conn.execute("""
                        INSERT INTO products (
                            asin, parent_asin, title, brand, image_url, 
                            real_average_rating, real_total_ratings, category, last_updated
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, now())
                        ON CONFLICT (asin) DO UPDATE SET
                            real_average_rating = excluded.real_average_rating,
                            real_total_ratings = excluded.real_total_ratings,
                            title = COALESCE(excluded.title, products.title),
                            brand = COALESCE(excluded.brand, products.brand),
                            image_url = COALESCE(excluded.image_url, products.image_url),
                            last_updated = now()
                    """, [asin, asin, title, brand, image, avg_rating, total_ratings, category])
                    
                    total_inserted += 1
                except Exception as e:
                    print(f"❌ Error line: {e}")
                total_processed += 1
                
    conn.close()
    print(f"✅ Finished. Processed: {total_processed}, Ingested/Updated: {total_inserted}")

if __name__ == "__main__":
    backfill()
