import duckdb
import polars as pl
from pathlib import Path
from typing import Dict, Any
import shutil
import os
from .config import Settings

class DataIngester:
    def __init__(self):
        # We determine target DB at runtime of ingest, not init
        pass

    def _init_schema(self, db_path):
        """Ensure DB tables exist on specific DB."""
        try:
            with duckdb.connect(str(db_path)) as conn:
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
                        mining_status VARCHAR DEFAULT 'PENDING',
                        ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS products (
                        asin VARCHAR PRIMARY KEY,
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
                    CREATE TABLE IF NOT EXISTS aspect_mapping (
                        raw_aspect TEXT PRIMARY KEY,
                        standard_aspect TEXT,
                        category TEXT
                    );
                    -- Social Wallet Tables (V2)
                    CREATE TABLE IF NOT EXISTS users_budget (
                        user_id VARCHAR PRIMARY KEY,
                        monthly_cap FLOAT DEFAULT 20.0,
                        current_spend FLOAT DEFAULT 0.0,
                        is_locked BOOLEAN DEFAULT FALSE,
                        last_reset DATE DEFAULT CURRENT_DATE
                    );
                    CREATE TABLE IF NOT EXISTS scrape_transactions (
                        trans_id UUID PRIMARY KEY DEFAULT uuid(),
                        user_id VARCHAR,
                        platform VARCHAR,
                        target TEXT,
                        item_count INTEGER,
                        estimated_cost FLOAT,
                        actual_cost FLOAT,
                        status VARCHAR,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
        except Exception as e:
            print(f"Schema Init Error: {e}")

    def _clean_dataframe(self, df: pl.DataFrame, filename: str) -> pl.DataFrame:
        df = df.rename({c: c.lower() for c in df.columns})
        cols_map = {
            "reviewid": "review_id", "asin": "parent_asin", "variationid": "child_asin",
            "username": "author_name", "rating": "rating_raw", "title": "title",
            "text": "text", "date": "date_raw", "verified": "verified_raw",
            "vine": "vine_raw", "numberofhelpful": "helpful_count"
        }
        exprs = []
        for raw_col, db_col in cols_map.items():
            if raw_col in df.columns: exprs.append(pl.col(raw_col).alias(db_col))
            else: exprs.append(pl.lit(0 if db_col=="helpful_count" else None).cast(pl.Int32 if db_col=="helpful_count" else pl.Utf8).alias(db_col))
        
        if "variationlist/0" in df.columns: exprs.append(pl.col("variationlist/0").alias("variation_text"))
        else: exprs.append(pl.lit(None).cast(pl.Utf8).alias("variation_text"))
        
        df = df.select(exprs).with_columns([
            pl.col("rating_raw").cast(pl.Utf8).str.extract(r"(\d+\.?\d*)", 1).cast(pl.Float64, strict=False).fill_null(0.0).alias("rating_score"),
            pl.col("date_raw").str.replace(r".*on ", "").str.strip_chars().str.to_date("%B %d, %Y", strict=False).alias("review_date"),
            (pl.col("verified_raw").cast(pl.Utf8).str.to_lowercase() == "true").fill_null(False).alias("is_verified"),
            (pl.col("vine_raw").cast(pl.Utf8).str.to_lowercase() == "true").fill_null(False).alias("vine_program"),
            pl.col("helpful_count").fill_null(0).cast(pl.Int32, strict=False),
            pl.lit(filename).alias("source_file"), pl.lit("PENDING").alias("mining_status")
        ]).filter(pl.col("review_id").is_not_null() & pl.col("review_date").is_not_null())
        
        target_cols = [
            "review_id", "parent_asin", "child_asin", "variation_text",
            "author_name", "rating_score", "title", "text",
            "review_date", "is_verified", "vine_program",
            "helpful_count", "source_file", "mining_status"
        ]
        
        # Ensure all columns exist
        for col in target_cols:
            if col not in df.columns:
                df = df.with_columns(pl.lit(None).alias(col))

        return df.select(target_cols)

    def _ingest_products(self, df: pl.DataFrame, conn):
        df = df.rename({c: c.lower() for c in df.columns})
        mapping = {"asin": "parent_asin", "producttitle": "title", "productoriginalimage": "image_url", "brand": "brand"}
        exprs = [pl.col(r).alias(d) for r, d in mapping.items() if r in df.columns]
        if not exprs: return
        
        p_df = df.select(exprs).unique(subset=["parent_asin"]).with_columns([
            pl.col("parent_asin").alias("asin"),
            pl.lit(None).cast(pl.Utf8).alias("material"),
            pl.lit(None).cast(pl.Utf8).alias("main_niche"),
            pl.lit(None).cast(pl.Utf8).alias("target_audience"),
            pl.lit(None).cast(pl.Utf8).alias("design_type"),
            pl.lit(None).cast(pl.Utf8).alias("gender"),
            pl.lit(None).cast(pl.Utf8).alias("size_capacity"),
            pl.lit(None).cast(pl.Utf8).alias("product_line"),
            pl.lit(None).cast(pl.Utf8).alias("num_pieces"),
            pl.lit(None).cast(pl.Utf8).alias("pack"),
            pl.lit(0).cast(pl.Int32).alias("variation_count"),
            pl.lit(None).alias("specs_json")
        ])

        # Ensure all required columns for INSERT exist
        for col in ["title", "brand", "image_url"]:
            if col not in p_df.columns:
                p_df = p_df.with_columns(pl.lit(None).cast(pl.Utf8).alias(col))
        
        if not p_df.is_empty():
            conn.register("temp_products", p_df.to_arrow())
            conn.execute("""
                INSERT OR REPLACE INTO products (asin, parent_asin, title, brand, image_url, last_updated)
                SELECT asin, parent_asin, title, brand, image_url, current_timestamp FROM temp_products
            """)

    def ingest_file(self, file_path: Path) -> Dict[str, Any]:
        """Blue-Green Ingestion Strategy."""
        if not file_path.exists(): return {"error": "File not found"}

        # 1. Identify Target (Standby) DB
        target_db = Settings.get_standby_db_path()
        active_db = Settings.get_active_db_path()
        
        print(f"🔄 [Blue-Green] Active: {active_db.name}, Target: {target_db.name}")

        # 2. Sync: Copy Active -> Target (Overwrite)
        # This ensures Target has latest data + schema before we write new stuff
        # If Active doesn't exist (fresh start), we init schema on Target
        try:
            if active_db.exists():
                print(f"📋 [Blue-Green] Syncing {active_db.name} -> {target_db.name}...")
                shutil.copy(active_db, target_db)
            
            # Ensure schema (in case it's fresh or migration needed)
            self._init_schema(target_db)
            
        except Exception as e:
            return {"error": f"Blue-Green Sync Failed: {e}"}

        # 3. Write to Target (Exclusive access guaranteed)
        print(f"⚙️ [Ingester] Writing to {target_db.name}...")
        try:
            if file_path.suffix == '.xlsx': df = pl.read_excel(file_path, infer_schema_length=0)
            elif file_path.suffix == '.jsonl': df = pl.read_ndjson(file_path, infer_schema_length=0)
            else: return {"error": "Format not supported"}

            if df.is_empty(): return {"rows": 0, "status": "Empty File"}

            with duckdb.connect(str(target_db)) as conn:
                self._ingest_products(df, conn)
                df_clean = self._clean_dataframe(df, file_path.name)
                if not df_clean.is_empty():
                    conn.register("temp_reviews", df_clean.to_arrow())
                    conn.execute("""
                        INSERT INTO reviews (review_id, parent_asin, child_asin, variation_text, author_name, rating_score, title, text, review_date, is_verified, vine_program, helpful_count, source_file, mining_status, ingested_at)
                        SELECT *, current_timestamp FROM temp_reviews
                        WHERE review_id NOT IN (SELECT review_id FROM reviews)
                    """)
            
            # 4. Swap
            Settings.swap_db()
            print(f"✅ [Ingester] Done & Swapped. Active is now {target_db.name}")
            
            return {
                "total_rows": len(df),
                "inserted_rows": len(df_clean) if 'df_clean' in locals() else 0,
                "db_switched_to": target_db.name
            }

        except Exception as e:
            print(f"💥 [Ingester] Write Error: {e}")
            return {"error": str(e)}
