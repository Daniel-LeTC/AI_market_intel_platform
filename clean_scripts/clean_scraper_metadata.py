import polars as pl
import os
import re
import json

# --- CONFIG ---
# Update this path to your target file
INPUT_FILE = "staging_data_local/20260129_data/new_product_metadata/39_asin.jsonl"
OUTPUT_FILE = "staging_data_local/Cleaned_39_Asin_Metadata.jsonl"

DNA_MAP = {
    "Material": "material", "Fabric Type": "material", "Material Composition": "material",
    "Style": "design_type", "Pattern": "design_type", "Theme": "design_type",
    "Target Audience": "target_audience", "Department": "target_audience",
    "Size": "size_capacity", "Capacity": "size_capacity",
    "Number of Pieces": "num_pieces", "Included Components": "pack",
    "Brand": "brand", "Publisher": "brand", "Manufacturer": "brand"
}

def clean():
    print(f"🔍 Reading {INPUT_FILE}...")
    if not os.path.exists(INPUT_FILE):
        print("❌ File not found.")
        return

    # 1. Load & Filter Garbage
    data = []
    with open(INPUT_FILE, 'r') as f:
        for line in f:
            if not line.strip(): continue
            try:
                item = json.loads(line)
                # STRICT FILTER: Must be FOUND and have a TITLE to be useful
                if item.get("statusCode") == 200 and item.get("title"):
                    data.append(item)
            except: continue
    
    if not data:
        print("⚠️ No valid FOUND records with titles.")
        return

    print(f"📊 Loaded {len(data)} valid rows (excluding 404s/empty).")
    
    # 2. Extract DNA and Standardize ASINs
    schema_cols = list(set(DNA_MAP.values()))
    clean_rows = []

    for row in data:
        # --- A. ASIN LOGIC (The Brain) ---
        url = row.get("url", "")
        # Extract ASIN from URL (usually the Parent/Search Target)
        url_asin_match = re.search(r"/dp/([A-Z0-9]{10})", url)
        url_asin = url_asin_match.group(1) if url_asin_match else None
        
        raw_asin = row.get("asin", "")
        
        final_child = None
        final_parent = None

        if raw_asin and url_asin:
            if raw_asin == url_asin:
                # Standalone item (Book) or landed on main variant
                final_child = raw_asin
                final_parent = raw_asin
            else:
                # Variation item (Tumbler) -> URL is Parent, Body is Child
                final_child = raw_asin
                final_parent = url_asin
        elif raw_asin and not url_asin:
            # Fallback: only have body ASIN
            final_child = raw_asin
            final_parent = raw_asin
        elif url_asin and not raw_asin:
            # Fallback: Body empty but URL valid (Rare but possible)
            final_child = url_asin
            final_parent = url_asin
        else:
            # Both missing -> Skip
            continue

        # --- B. DNA Extraction ---
        row_dna = {col: None for col in schema_cols}
        details = row.get("productDetails")
        
        if isinstance(details, list):
            for item in details:
                if not isinstance(item, dict): continue
                k = item.get("name", "")
                v = item.get("value", "")
                
                if k and v:
                    k = str(k).replace(" ‏ : ‎", "").replace("‏", "").replace("‎", "").strip()
                    v = str(v).strip()
                    
                    # Map
                    for map_k, map_v in DNA_MAP.items():
                        if map_k.lower() in k.lower():
                            if row_dna[map_v] is None: row_dna[map_v] = v
                            else: row_dna[map_v] += f" | {v}"

        # --- C. Assemble Clean Row ---
        clean_row = {
            "asin": final_child,
            "parent_asin": final_parent,
            "title": row.get("title"),
            "image_url": row.get("imageUrlList", [None])[0] if row.get("imageUrlList") else None,
            "brand": row.get("manufacturer"), # Default brand source
            "real_average_rating": row.get("productRating"),
            "real_total_ratings": row.get("countReview")
        }
        # Merge DNA
        clean_row.update(row_dna)
        clean_rows.append(clean_row)

    # 3. Create Final DataFrame
    df_final = pl.DataFrame(clean_rows, infer_schema_length=None, strict=False)

    # 4. Type Cleaning
    if "real_average_rating" in df_final.columns:
        df_final = df_final.with_columns(
            pl.col("real_average_rating").cast(pl.Utf8)
            .str.extract(r"(\d+\.?\d*)", 1)
            .cast(pl.Float64, strict=False)
        )
    
    print(f"DEBUG: Final Shape: {df_final.shape}")
    print(f"Sample: {df_final.head(1)}")
    
    print(f"💾 Saving to {OUTPUT_FILE}...")
    df_final.write_ndjson(OUTPUT_FILE)
    print("🏁 Done!")

if __name__ == "__main__":
    clean()
