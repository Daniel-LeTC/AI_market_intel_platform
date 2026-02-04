import os
import sys
import json
import argparse
from apify_client import ApifyClient
from pathlib import Path

# Add root to sys.path to find core
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scout_app.core.config import Settings
from scout_app.core.logger import log_event
import duckdb

def run_apify_product_details(asins: list, category: str = "comforter"):
    """
    Fetch full product details from Apify Axesso Scraper.
    """
    token = Settings.APIFY_TOKEN or os.getenv("APIFY_TOKEN")
    client = ApifyClient(token)
    
    urls = [f"https://www.amazon.com/dp/{asin}" for asin in asins]
    print(f"🎭 Launching Apify Detail Scraper for {len(urls)} URLs...")
    
    run_input = { "urls": urls }
    
    try:
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
                
                # CRITICAL: Prioritize requested_asin (Source of Truth) over scraper's canonical parent
                # to prevent unwanted "Grandparent" consolidation.
                final_parent_asin = requested_asin or scraped_parent or scraped_asin
                if not final_parent_asin:
                    continue

                # 2. Metadata Extraction
                title = item.get("title") or item.get("productTitle")
                brand = item.get("brand") 
                if not brand:
                    mfr = item.get("manufacturer")
                    if mfr:
                        brand = mfr.replace("Visit the ", "").replace(" Store", "").strip()
                
                if brand:
                    brand = brand.replace("Brand: ", "").replace("Visit the ", "").replace(" Store", "").replace("\u200e", "").strip()
                
                # DNA Fields (Technical metadata)
                material = None
                design_type = None
                target_audience = None
                gender = None
                
                if item.get("productDetails"):
                    for detail in item["productDetails"]:
                        name = str(detail.get("name", "")).lower()
                        val = detail.get("value")
                        if not brand and "brand" in name: brand = val
                        if "material" in name: material = val
                        if "design" in name or "style" in name: design_type = val
                        if "audience" in name or "target" in name: target_audience = val
                        if "gender" in name: gender = val

                # --- NEW: Pipeline Enrichment (Common Sense Logic) ---
                # 1. Tumbler DNA
                if category == "tumbler":
                    if not material and any(k in title.lower() for k in ["stainless", "steel", "insulated"]):
                        material = "Stainless Steel"
                
                # 2. Book DNA
                elif category == "book":
                    if not material: material = "Paper"
                    if not target_audience and any(k in title.lower() for k in ["kids", "children", "toddler"]):
                        target_audience = "Kids"

                if brand: brand = brand.replace("\u200e", "").strip()

                image = item.get("mainImage")
                if isinstance(image, dict):
                    image = image.get("imageUrl")
                elif not image and item.get("imageUrlList"):
                    image = item["imageUrlList"][0]

                # Niche detection
                niche = "Unknown"
                if item.get("breadCrumbs"):
                    niche = item["breadCrumbs"].split(">")[-1].strip()
                elif item.get("categoriesExtended") and len(item["categoriesExtended"]) > 0:
                    niche = item["categoriesExtended"][-1].get("name")

                # --- DB UPDATE 1: product_parents (High-level Anchor) ---
                # We update this FIRST to satisfy Foreign Key constraints in the products table
                conn.execute("""
                    INSERT INTO product_parents (parent_asin, category, niche, title, brand, image_url, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, now())
                    ON CONFLICT (parent_asin) DO UPDATE SET
                        category = CASE 
                            WHEN product_parents.category IS NULL OR product_parents.category IN ('Unknown', 'comforter') 
                            THEN excluded.category 
                            ELSE product_parents.category 
                        END,
                        niche = COALESCE(excluded.niche, product_parents.niche),
                        title = COALESCE(excluded.title, product_parents.title),
                        brand = COALESCE(excluded.brand, product_parents.brand),
                        image_url = COALESCE(excluded.image_url, product_parents.image_url),
                        last_updated = now()
                """, [final_parent_asin, category, niche, title, brand, image])

                # --- DB UPDATE 2: products (Technical Metadata) ---
                if scraped_asin:
                    conn.execute("""
                        INSERT INTO products (asin, parent_asin, title, brand, image_url, material, main_niche, design_type, target_audience, gender, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now())
                        ON CONFLICT (asin) DO UPDATE SET
                            title = COALESCE(excluded.title, products.title),
                            brand = COALESCE(excluded.brand, products.brand),
                            image_url = COALESCE(excluded.image_url, products.image_url),
                            material = COALESCE(excluded.material, products.material),
                            main_niche = COALESCE(excluded.main_niche, products.main_niche),
                            design_type = COALESCE(excluded.design_type, products.design_type),
                            target_audience = COALESCE(excluded.target_audience, products.target_audience),
                            gender = COALESCE(excluded.gender, products.gender),
                            last_updated = now()
                    """, [scraped_asin, final_parent_asin, title, brand, image, material, niche, design_type, target_audience, gender])
                
                print(f"✅ Enriched family for {final_parent_asin} (ASIN: {scraped_asin})")
                log_event("ApifyDetail", {"parent_asin": final_parent_asin, "scraped_asin": scraped_asin, "status": "enriched"})

            # --- SMART NICHE: Check for Multi-Niche Parents ---
            # (Run after all updates in this batch)
            affected_parents = list({(scraped_parent or scraped_asin or requested_asin) for item in results})
            for p_asin in affected_parents:
                if not p_asin: continue
                niche_count = conn.execute("SELECT COUNT(DISTINCT main_niche) FROM products WHERE parent_asin = ?", [p_asin]).fetchone()[0]
                if niche_count > 1:
                    conn.execute("UPDATE product_parents SET niche = 'Multi-Niche' WHERE parent_asin = ?", [p_asin])
                    print(f"🔀 Marked {p_asin} as 'Multi-Niche'")

        finally:
            conn.close()
            
        return len(results)
        
    except Exception as e:
        print(f"❌ Apify Error: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("asins", nargs="+")
    parser.add_argument("--category", default="comforter")
    args = parser.parse_args()
    
    run_apify_product_details(args.asins, args.category)
