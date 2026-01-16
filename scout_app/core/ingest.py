import duckdb
import polars as pl
from pathlib import Path
from typing import Dict, Any, List
from .config import Settings

class DataIngester:
    def __init__(self):
        self.db_path = str(Settings.DB_PATH)
        # Init schema immediately upon instantiation
        self._init_schema()

    def _init_schema(self):
        """Ensure DB tables exist."""
        conn = duckdb.connect(self.db_path)
        try:
            # Reviews Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id VARCHAR PRIMARY KEY,
                    parent_asin VARCHAR,
                    child_asin VARCHAR,
                    variation_text VARCHAR,
                    author_name VARCHAR,
                    rating_score FLOAT,
                    title VARCHAR,
                    text VARCHAR,
                    review_date DATE,
                    is_verified BOOLEAN,
                    vine_program BOOLEAN,
                    helpful_count INTEGER,
                    source_file VARCHAR,
                    mining_status VARCHAR DEFAULT 'PENDING', -- PENDING, QUEUED, COMPLETED
                    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Products Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    asin VARCHAR PRIMARY KEY, -- Child ASIN or Parent if unknown
                    parent_asin VARCHAR,
                    title VARCHAR,
                    brand VARCHAR,
                    image_url VARCHAR,
                    material VARCHAR,
                    main_niche VARCHAR,
                    gender VARCHAR,
                    design_type VARCHAR,
                    target_audience VARCHAR,
                    size_capacity VARCHAR,
                    product_line VARCHAR,
                    num_pieces VARCHAR,
                    pack VARCHAR,
                    variation_count INTEGER,
                    specs_json JSON,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Review Tags Table (AI Output)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS review_tags (
                    tag_id UUID PRIMARY KEY DEFAULT uuid(), 
                    review_id VARCHAR,
                    parent_asin VARCHAR,
                    category VARCHAR,
                    aspect VARCHAR,
                    sentiment VARCHAR,
                    quote VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Aspect Mapping (For Normalizer)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS aspect_mapping (
                    raw_aspect TEXT PRIMARY KEY,
                    standard_aspect TEXT,
                    category TEXT
                )
            """)
        finally:
            conn.close()

    def _clean_dataframe(self, df: pl.DataFrame, filename: str) -> pl.DataFrame:
        """Normalize raw scraped data to DB schema (Reviews)."""
        df = df.rename({c: c.lower() for c in df.columns})
        
        cols_map = {
            "reviewid": "review_id",
            "asin": "parent_asin",  # Apify often puts Parent ASIN here for reviews
            "variationid": "child_asin",
            "username": "author_name",
            "rating": "rating_raw",
            "title": "title",
            "text": "text",
            "date": "date_raw",
            "verified": "verified_raw",
            "vine": "vine_raw",
            "numberofhelpful": "helpful_count"
        }
        
        exprs = []
        for raw_col, db_col in cols_map.items():
            if raw_col in df.columns:
                exprs.append(pl.col(raw_col).alias(db_col))
            else:
                if db_col == "helpful_count":
                    exprs.append(pl.lit(0).alias(db_col))
                elif db_col == "child_asin":
                    if "parent_asin" in cols_map.values(): 
                         exprs.append(pl.col("parent_asin").alias(db_col))
                    else:
                         exprs.append(pl.lit(None).cast(pl.Utf8).alias(db_col))
                else:
                    exprs.append(pl.lit(None).cast(pl.Utf8).alias(db_col))

        if "variationlist/0" in df.columns:
             exprs.append(pl.col("variationlist/0").alias("variation_text"))
        else:
             exprs.append(pl.lit(None).cast(pl.Utf8).alias("variation_text"))

        df_selected = df.select(exprs)
        
        df_clean = df_selected.with_columns([
            pl.col("rating_raw")
                .cast(pl.Utf8).str.extract(r"(\d+\.?\d*)", 1)
                .cast(pl.Float64, strict=False)
                .fill_null(0.0)
                .alias("rating_score"),

            pl.col("date_raw")
                .str.replace(r".*on ", "")
                .str.strip_chars()
                .str.to_date("%B %d, %Y", strict=False)
                .alias("review_date"),
            
            (pl.col("verified_raw").cast(pl.Utf8).str.to_lowercase() == "true")
                .fill_null(False)
                .alias("is_verified"),
            
            (pl.col("vine_raw").cast(pl.Utf8).str.to_lowercase() == "true")
                .fill_null(False)
                .alias("vine_program"),
            
            pl.col("helpful_count").fill_null(0).cast(pl.Int32, strict=False),
            pl.lit(filename).alias("source_file"),
            pl.lit("PENDING").alias("mining_status")
        ])

        df_final = df_clean.filter(
            pl.col("review_id").is_not_null() & 
            pl.col("review_date").is_not_null()
        )
        
        target_cols = [
            "review_id", "parent_asin", "child_asin", "variation_text",
            "author_name", "rating_score", "title", "text",
            "review_date", "is_verified", "vine_program",
            "helpful_count", "source_file", "mining_status"
        ]
        
        for col in target_cols:
             if col not in df_final.columns:
                 df_final = df_final.with_columns(pl.lit(None).alias(col))

        return df_final.select(target_cols)

    def _ingest_products_from_df(self, df: pl.DataFrame, conn):
        """Extract and Upsert Product Metadata."""
        # Normalize columns first
        df = df.rename({c: c.lower() for c in df.columns})
        
        # Check available product columns
        mapping = {
            "asin": "parent_asin", 
            "producttitle": "title",
            "productoriginalimage": "image_url",
            "brand": "brand"
        }
        
        available_exprs = []
        for raw, db in mapping.items():
            if raw in df.columns:
                available_exprs.append(pl.col(raw).alias(db))
        
        if not available_exprs:
            return

        # Select & Unique
        product_df = df.select(available_exprs).unique(subset=["parent_asin"])
        
        # Add missing columns with Null
        required_cols = ["parent_asin", "title", "brand", "image_url"]
        for col in required_cols:
            if col not in product_df.columns:
                 product_df = product_df.with_columns(pl.lit(None).cast(pl.Utf8).alias(col))
        
        # We assume Parent ASIN is the key for now in this context
        product_df = product_df.with_columns(pl.col("parent_asin").alias("asin"))
        
        if product_df.is_empty():
            return

        print(f"📦 [Ingester] Found metadata for {len(product_df)} products. Upserting...")
        
        # Register and Insert OR REPLACE
        conn.register("temp_products_batch", product_df.to_arrow())
        conn.execute("""
            INSERT OR REPLACE INTO products (asin, parent_asin, title, brand, image_url, last_updated)
            SELECT asin, parent_asin, title, brand, image_url, current_timestamp
            FROM temp_products_batch
        """)

    def ingest_file(self, file_path: Path) -> Dict[str, Any]:
        """Ingests a single file into DuckDB."""
        if not file_path.exists():
            return {"error": "File not found"}

        print(f"⚙️ [Ingester] Processing {file_path.name}...")
        
        try:
            if file_path.suffix.lower() == '.xlsx':
                df_raw = pl.read_excel(file_path, infer_schema_length=0)
            elif file_path.suffix.lower() == '.jsonl':
                df_raw = pl.read_ndjson(file_path, infer_schema_length=0)
            else:
                 return {"error": "Unsupported file format"}

            if df_raw.is_empty():
                return {"total_rows": 0, "inserted_rows": 0, "asins_found": []}

            conn = duckdb.connect(self.db_path)
            
            # 1. Ingest Products First
            self._ingest_products_from_df(df_raw, conn)

            # 2. Ingest Reviews
            df_clean = self._clean_dataframe(df_raw, file_path.name)
            
            if df_clean.is_empty():
                 conn.close()
                 return {"total_rows": 0, "inserted_rows": 0, "asins_found": []}

            asins_found = df_clean["parent_asin"].unique().to_list()
            asins_found = [str(x) for x in asins_found if x]

            conn.register("temp_arrow_view", df_clean.to_arrow())
            conn.execute("""
                INSERT INTO reviews (review_id, parent_asin, child_asin, variation_text, author_name, rating_score, title, text, review_date, is_verified, vine_program, helpful_count, source_file, mining_status, ingested_at)
                SELECT *, current_timestamp
                FROM temp_arrow_view
                WHERE review_id NOT IN (SELECT review_id FROM reviews)
            """)
            
            conn.close()
            
            print(f"✅ [Ingester] Ingested {len(df_clean)} rows from {file_path.name}")
            return {
                "total_rows": len(df_raw), 
                "inserted_rows": len(df_clean),
                "asins_found": asins_found
            }

        except Exception as e:
            print(f"💥 [Ingester] Error: {e}")
            return {"error": str(e)}