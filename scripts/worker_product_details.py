import os
import sys
import json
from apify_client import ApifyClient
from pathlib import Path

# Add root to sys.path to find core
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scout_app.core.config import Settings
from scout_app.core.logger import log_event
import duckdb

def run_apify_product_details(asins: list):
    """
    Fetch full product details from Apify Axesso Scraper.
    """
    token = Settings.APIFY_TOKEN or os.getenv("APIFY_TOKEN")
    client = ApifyClient(token)
    
    urls = [f"https://www.amazon.com/dp/{asin}" for asin in asins]
    print(f"🎭 Launching Apify Detail Scraper for {len(urls)} URLs...")
    
    run_input = { "urls": urls }
    
    try:
        # Run the Actor (axesso_data~amazon-product-details-scraper)
        # Note: 7KgyOHHEiPEcilZXM is the internal ID for this actor
        run = client.actor("axesso_data/amazon-product-details-scraper").call(run_input=run_input)
        results = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
            
        print(f"✅ Fetched details for {len(results)} items.")
        
        # --- PERSIST TO DB ---
        db_path = str(Settings.get_active_db_path())
        conn = duckdb.connect(db_path)
        try:
            for item in results:
                # 1. Robust ASIN Extraction
                requested_asin = None
                if item.get("url"):
                    import re
                    match = re.search(r'/dp/([A-Z0-9]{10})', item["url"])
                    if match:
                        requested_asin = match.group(1)
                
                scraped_asin = item.get("asin")
                scraped_parent = item.get("parentAsin")
                
                # The target is either the one we asked for, or the one we got, or the known parent
                asins_to_update = {a for a in [requested_asin, scraped_asin, scraped_parent] if a}
                
                if not asins_to_update:
                    continue

                # 2. Robust Title Extraction
                title = item.get("title") or item.get("productTitle")

                # 3. Robust Brand Extraction
                brand = item.get("brand") 
                if not brand:
                    # Try manufacturer (often "Visit the X Store")
                    mfr = item.get("manufacturer")
                    if mfr:
                        brand = mfr.replace("Visit the ", "").replace(" Store", "").strip()
                
                if not brand and item.get("productDetails"):
                    # Scan productDetails list
                    for detail in item["productDetails"]:
                        if isinstance(detail, dict):
                            name = str(detail.get("name", "")).lower()
                            if "brand" in name:
                                brand = detail.get("value")
                                break
                
                # Clean brand (some values have weird chars like \u200e)
                if brand:
                    brand = brand.replace("\u200e", "").strip()

                # 4. Image Extraction
                image = item.get("mainImage")
                if isinstance(image, dict):
                    image = image.get("imageUrl")
                elif not image and item.get("imageUrlList"):
                    image = item["imageUrlList"][0]

                # 5. Niche / Category
                niche = "Unknown"
                if item.get("breadCrumbs"):
                    niche = item["breadCrumbs"].split(">")[-1].strip()
                elif item.get("categoriesExtended") and len(item["categoriesExtended"]) > 0:
                    niche = item["categoriesExtended"][-1].get("name")

                # --- DB UPDATE FOR ALL RELATED ASINS ---
                for target_asin in asins_to_update:
                    conn.execute("""
                        INSERT INTO product_parents (parent_asin, category, niche, title, brand, image_url, last_updated)
                        VALUES (?, 'comforter', ?, ?, ?, ?, now())
                        ON CONFLICT (parent_asin) DO UPDATE SET
                            niche = COALESCE(excluded.niche, product_parents.niche),
                            title = CASE 
                                WHEN excluded.title IS NOT NULL AND excluded.title != '' AND excluded.title NOT LIKE 'Imported%' 
                                THEN excluded.title 
                                ELSE product_parents.title 
                            END,
                            brand = COALESCE(excluded.brand, product_parents.brand),
                            image_url = COALESCE(excluded.image_url, product_parents.image_url),
                            last_updated = now()
                    """, [target_asin, niche, title, brand, image])
                
                primary_display = scraped_parent or scraped_asin or requested_asin
                print(f"✅ Processed family for {primary_display}: Brand={brand}")
                log_event("ApifyDetail", {"parent_asin": scraped_parent, "requested_asin": requested_asin, "status": "enriched", "brand": brand})
        finally:
            conn.close()
            
        return len(results)
        
    except Exception as e:
        print(f"❌ Apify Error: {e}")
        return None

if __name__ == "__main__":
    asins = sys.argv[1:] if len(sys.argv) > 1 else ["B00P8XQPY4"]
    run_apify_product_details(asins)
