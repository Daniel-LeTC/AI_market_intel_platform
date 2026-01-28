import duckdb
import polars as pl
from pathlib import Path
from typing import Dict, Any
import shutil
import os
from .config import Settings
from .stats_engine import StatsEngine

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
                        real_average_rating DOUBLE,
                        real_total_ratings INTEGER,
                        rating_breakdown JSON,
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
                    CREATE TABLE IF NOT EXISTS product_stats (
                        asin VARCHAR PRIMARY KEY,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metrics_json JSON
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

    def _flatten_structs(self, df: pl.DataFrame) -> pl.DataFrame:
        """Recursively flatten Struct columns into flat columns with '/' separator."""
        has_struct = any(isinstance(dtype, pl.Struct) for dtype in df.dtypes)
        if not has_struct:
            return df

        new_cols = []
        for col_name, dtype in zip(df.columns, df.dtypes):
            if isinstance(dtype, pl.Struct):
                # Expand struct fields
                for field in dtype.fields:
                    new_cols.append(
                        pl.col(col_name).struct.field(field.name).alias(f"{col_name}/{field.name}")
                    )
            else:
                new_cols.append(pl.col(col_name))
        
        # Recurse until no more structs (for deeply nested like reviewSummary/fiveStar/percentage)
        df_flat = df.select(new_cols)
        return self._flatten_structs(df_flat)

    def _ingest_products(self, df: pl.DataFrame, conn):
        """
        Robustly ingest product metadata for both Parent and Child ASINs.
        Uses COALESCE to prevent overwriting existing data with NULLs.
        """
        # --- NEW: AUTO-FLATTEN FOR JSONL SUPPORT ---
        df = self._flatten_structs(df)
        df = df.rename({c: c.lower() for c in df.columns})
        
        schema_cols = [
            "asin", "parent_asin", "title", "brand", "image_url", 
            "real_average_rating", "real_total_ratings", "rating_breakdown", "variation_count"
        ]

        # 1. PREPARE PARENT METADATA
        # Mapping for core product info + DNA fields
        mapping = {
            "asin": "asin",
            "parentasin": "parent_asin",
            "producttitle": "title", 
            "productoriginalimage": "image_url", 
            "brand": "brand",
            "countratings": "real_total_ratings",
            # DNA FIELDS
            "material": "material", "fabric": "material",
            "niche": "main_niche", "category": "main_niche",
            "audience": "target_audience", "target": "target_audience",
            "design": "design_type", "style": "design_type",
            "capacity": "size_capacity", "size": "size_capacity",
            "line": "product_line", "series": "product_line",
            "pieces": "num_pieces", "count": "num_pieces",
            "pack": "pack"
        }
        
        # If 'parent_asin' column is missing, assume 'asin' is the parent
        if "parent_asin" not in df.columns and "asin" in df.columns:
            df = df.with_columns(pl.col("asin").alias("parent_asin"))

        exprs = [pl.col(r).alias(d) for r, d in mapping.items() if r in df.columns]
        
        if "productrating" in df.columns:
            exprs.append(
                pl.col("productrating").cast(pl.Utf8).str.extract(r"(\d+\.?\d*)", 1)
                .cast(pl.Float64).alias("real_average_rating")
            )

        # Histogram Extraction
        hist_cols = {
            "reviewsummary/fivestar/percentage": "5", "reviewsummary/fourstar/percentage": "4",
            "reviewsummary/threestar/percentage": "3", "reviewsummary/twostar/percentage": "2",
            "reviewsummary/onestar/percentage": "1"
        }
        hist_exprs = [pl.format('"{}" : {}', pl.lit(star), pl.col(col).fill_null(0)) 
                     for col, star in hist_cols.items() if col in df.columns]
        
        if hist_exprs:
            exprs.append(
                pl.concat_str([pl.lit("{"), pl.concat_str(hist_exprs, separator=", "), pl.lit("}")])
                .alias("rating_breakdown")
            )

        # Variation Count
        var_col = next((c for c in df.columns if c.lower() in ["count variation asins", "total variations", "variation_count"]), None)
        if var_col: exprs.append(pl.col(var_col).cast(pl.Int32).alias("variation_count"))

        if not exprs: return

        # Create cleaned products dataframe (Unique by ASIN, not just Parent)
        p_df = df.select(exprs).unique(subset=["asin"])
        
        # Add missing columns with CORRECT TYPES to match schema for Parent
        type_map = {
            "asin": pl.Utf8, "parent_asin": pl.Utf8, "title": pl.Utf8, "brand": pl.Utf8, "image_url": pl.Utf8,
            "real_average_rating": pl.Float64, "real_total_ratings": pl.Int32, 
            "rating_breakdown": pl.Utf8, "variation_count": pl.Int32,
            "material": pl.Utf8, "main_niche": pl.Utf8, "target_audience": pl.Utf8,
            "design_type": pl.Utf8, "size_capacity": pl.Utf8, "product_line": pl.Utf8,
            "num_pieces": pl.Utf8, "pack": pl.Utf8
        }
        for col, dtype in type_map.items():
            if col not in p_df.columns:
                p_df = p_df.with_columns(pl.lit(None).cast(dtype).alias(col))
            else:
                p_df = p_df.with_columns(pl.col(col).cast(dtype, strict=False))
        
        schema_cols = list(type_map.keys())
        p_df = p_df.select(schema_cols)

        # 2. PREPARE CHILD METADATA (From variations)
        var_id_col = next((c for c in df.columns if c.lower() == "variationid"), None)
        if var_id_col and "asin" in df.columns:
            c_df = df.select([
                pl.col(var_id_col).alias("asin"),
                pl.col("asin").alias("parent_asin"),
                pl.col("producttitle").alias("title") if "producttitle" in df.columns else pl.lit(None).cast(pl.Utf8),
                pl.col("brand").alias("brand") if "brand" in df.columns else pl.lit(None).cast(pl.Utf8),
            ]).unique(subset=["asin"]).filter(pl.col("asin").is_not_null())
            
            for col, dtype in type_map.items():
                if col not in c_df.columns:
                    c_df = c_df.with_columns(pl.lit(None).cast(dtype).alias(col))
                else:
                    c_df = c_df.with_columns(pl.col(col).cast(dtype))
            
            p_df = pl.concat([p_df, c_df.select(schema_cols)]).unique(subset=["asin"])

        if p_df.is_empty(): return

        # 3. SMART UPSERT INTO DUCKDB
        # We use COALESCE(excluded.col, products.col) to keep old data if new data is NULL
        conn.register("temp_p", p_df.to_arrow())
        conn.execute("""
            INSERT INTO products (
                asin, parent_asin, title, brand, image_url, 
                real_average_rating, real_total_ratings, rating_breakdown, 
                variation_count, material, main_niche, target_audience,
                design_type, size_capacity, product_line, num_pieces, pack,
                last_updated
            )
            SELECT 
                asin, 
                COALESCE(parent_asin, asin), 
                title, brand, image_url, 
                real_average_rating, real_total_ratings, 
                CAST(rating_breakdown AS JSON), 
                variation_count, material, main_niche, target_audience,
                design_type, size_capacity, product_line, num_pieces, pack,
                now() as last_updated
            FROM temp_p
            ON CONFLICT (asin) DO UPDATE SET
                parent_asin = COALESCE(CAST(excluded.parent_asin AS VARCHAR), products.parent_asin),
                title = COALESCE(CAST(excluded.title AS VARCHAR), products.title),
                brand = COALESCE(CAST(excluded.brand AS VARCHAR), products.brand),
                image_url = COALESCE(CAST(excluded.image_url AS VARCHAR), products.image_url),
                real_average_rating = COALESCE(CAST(excluded.real_average_rating AS DOUBLE), products.real_average_rating),
                real_total_ratings = COALESCE(CAST(excluded.real_total_ratings AS INTEGER), products.real_total_ratings),
                rating_breakdown = COALESCE(CAST(excluded.rating_breakdown AS JSON), products.rating_breakdown),
                variation_count = COALESCE(CAST(excluded.variation_count AS INTEGER), products.variation_count),
                material = COALESCE(CAST(excluded.material AS VARCHAR), products.material),
                main_niche = COALESCE(CAST(excluded.main_niche AS VARCHAR), products.main_niche),
                target_audience = COALESCE(CAST(excluded.target_audience AS VARCHAR), products.target_audience),
                design_type = COALESCE(CAST(excluded.design_type AS VARCHAR), products.design_type),
                size_capacity = COALESCE(CAST(excluded.size_capacity AS VARCHAR), products.size_capacity),
                product_line = COALESCE(CAST(excluded.product_line AS VARCHAR), products.product_line),
                num_pieces = COALESCE(CAST(excluded.num_pieces AS VARCHAR), products.num_pieces),
                pack = COALESCE(CAST(excluded.pack AS VARCHAR), products.pack),
                last_updated = now()
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

            # 3.5. Trigger Pre-calculation (NEW)
            try:
                unique_asins = df["asin"].unique().to_list() if "asin" in df.columns else []
                if not unique_asins and "parent_asin" in df.columns:
                    unique_asins = df["parent_asin"].unique().to_list()
                
                if unique_asins:
                    print(f"📊 [Ingester] Recalculating stats for {len(unique_asins)} ASINs on {target_db.name}...")
                    engine = StatsEngine(db_path=str(target_db))
                    for asin in unique_asins:
                        if asin: engine.calculate_and_save(asin)
            except Exception as stats_err:
                print(f"⚠️ [Ingester] Stats Calculation Warning: {stats_err}")
            
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
