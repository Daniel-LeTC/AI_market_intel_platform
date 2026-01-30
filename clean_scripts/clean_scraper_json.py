import polars as pl
import os
import json

# --- CONFIG ---
INPUT_FILE = "dataset_amazon-product-details-scraper_2026-01-28_09-03-46-099.json"
OUTPUT_FILE = "staging_data/Scraper_Data_Cleaned.jsonl"

DNA_MAP = {
    "Material": "Material", "Fabric Type": "Material", "Material Composition": "Material",
    "Style": "Design Type", "Pattern": "Design Type", "Theme": "Design Type",
    "Target Audience": "Target Audience", "Department": "Target Audience",
    "Size": "Size/Capacity", "Capacity": "Size/Capacity",
    "Number of Pieces": "Number of Pieces", "Included Components": "Details of Pieces",
    "Brand": "Brand"
}

def clean():
    print(f"🔍 Reading {INPUT_FILE}...")
    if not os.path.exists(INPUT_FILE):
        print("❌ File not found.")
        return

    # Read standard JSON
    df = pl.read_json(INPUT_FILE)
    
    # 1. Identify ProductDetail Columns
    # In JSON, productDetails might be a Struct or List of Structs.
    # Polars read_json usually infers Structs.
    # Let's inspect column names first.
    print(f"Columns loaded: {len(df.columns)}")
    
    # Check if productDetails exists
    if "productDetails" not in df.columns:
        print("⚠️ productDetails column not found. Skipping deep clean.")
    else:
        # We need to process productDetails. 
        # If it's a List of Structs (name, value), we can explode.
        # But for simplicity, we use row iteration like the Excel script.
        # However, Polars Struct handling is strict. Let's convert to dicts.
        rows = df.to_dicts()
        schema_cols = list(set(DNA_MAP.values()))
        extracted_rows = {col: [] for col in schema_cols}
        
        for row in rows:
            row_dna = {col: None for col in schema_cols}
            details = row.get("productDetails")
            
            # details should be a list of dicts: [{'name': '...', 'value': '...'}, ...]
            if isinstance(details, list):
                for item in details:
                    if not isinstance(item, dict): continue
                    key = item.get("name")
                    val = item.get("value")
                    
                    if key and val:
                        key = str(key).strip()
                        for map_k, map_v in DNA_MAP.items():
                            if map_k.lower() in key.lower():
                                if row_dna[map_v] is None:
                                    row_dna[map_v] = str(val)
                                else:
                                    row_dna[map_v] += f" | {val}"
            
            for col in schema_cols:
                extracted_rows[col].append(row_dna[col])
        
        # Add new columns
        for col, values in extracted_rows.items():
            df = df.with_columns(pl.Series(name=col, values=values))

    # 4. Map Standard Columns
    # Rename map
    rename_map = {}
    if "productRating" in df.columns: rename_map["productRating"] = "Reviews: Rating"
    if "countReview" in df.columns: rename_map["countReview"] = "Reviews: Review Count"
    if "asin" in df.columns: rename_map["asin"] = "ASIN"
    
    df = df.rename(rename_map)
    
    # Filter Invalid
    if "ASIN" in df.columns:
        df = df.filter(pl.col("ASIN").is_not_null() & (pl.col("ASIN").str.len_bytes() > 0))

    print(f"DEBUG: Final Shape: {df.shape}")

    # 5. Save as JSONL (NDJSON)
    print(f"💾 Saving to {OUTPUT_FILE}...")
    df.write_ndjson(OUTPUT_FILE)
    print("🏁 Done!")

if __name__ == "__main__":
    clean()
