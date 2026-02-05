import duckdb
import polars as pl
from pathlib import Path
from typing import Dict, Any
import shutil
import os
import json
from .config import Settings


class DataIngester:
    def __init__(self):
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
                        category VARCHAR,
                        verification_status VARCHAR DEFAULT 'UNCERTAIN',
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
                    CREATE TABLE IF NOT EXISTS product_parents (
                        parent_asin VARCHAR PRIMARY KEY,
                        category VARCHAR,
                        title VARCHAR,
                        brand VARCHAR,
                        image_url VARCHAR,
                        niche VARCHAR,
                        verification_status VARCHAR DEFAULT 'UNCERTAIN',
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS scrape_queue (
                        asin VARCHAR PRIMARY KEY,
                        status VARCHAR DEFAULT 'PENDING',
                        note VARCHAR,
                        priority INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS scrape_transactions (
                        id UUID PRIMARY KEY DEFAULT uuid(),
                        asin VARCHAR,
                        action VARCHAR,
                        amount FLOAT,
                        user_id VARCHAR,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS social_case_studies (
                        id UUID PRIMARY KEY DEFAULT uuid(),
                        title VARCHAR,
                        content TEXT,
                        category VARCHAR,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS users_budget (
                        user_id VARCHAR PRIMARY KEY,
                        balance FLOAT DEFAULT 0.0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
        except Exception as e:
            print(f"Schema Init Error: {e}")

    def _clean_dataframe(self, df: pl.DataFrame, filename: str) -> pl.DataFrame:
        df = df.rename({c: c.lower() for c in df.columns})
        cols_map = {
            "reviewid": "review_id",
            "asin": "parent_asin",
            "variationid": "child_asin",
            "username": "author_name",
            "rating": "rating_raw",
            "title": "title",
            "text": "text",
            "date": "date_raw",
            "verified": "verified_raw",
            "vine": "vine_raw",
            "numberofhelpful": "helpful_count",
        }
        exprs = []
        for raw_col, db_col in cols_map.items():
            if raw_col in df.columns:
                exprs.append(pl.col(raw_col).alias(db_col))
            else:
                exprs.append(
                    pl.lit(0 if db_col == "helpful_count" else None)
                    .cast(pl.Int32 if db_col == "helpful_count" else pl.Utf8)
                    .alias(db_col)
                )

        if "variationlist/0" in df.columns:
            exprs.append(pl.col("variationlist/0").alias("variation_text"))
        else:
            exprs.append(pl.lit(None).cast(pl.Utf8).alias("variation_text"))

        df = (
            df.select(exprs)
            .with_columns(
                [
                    pl.col("rating_raw")
                    .cast(pl.Utf8)
                    .str.extract(r"(\d+\.?\d*)", 1)
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
                    pl.lit("PENDING").alias("mining_status"),
                ]
            )
            .filter(pl.col("review_id").is_not_null() & pl.col("review_date").is_not_null())
        )

        return df

    def _flatten_structs(self, df: pl.DataFrame) -> pl.DataFrame:
        has_struct = any(isinstance(dtype, pl.Struct) for dtype in df.dtypes)
        if not has_struct:
            return df
        new_cols = []
        for col_name, dtype in zip(df.columns, df.dtypes):
            if isinstance(dtype, pl.Struct):
                for field in dtype.fields:
                    new_cols.append(pl.col(col_name).struct.field(field.name).alias(f"{col_name}/{field.name}"))
            else:
                new_cols.append(pl.col(col_name))
        return self._flatten_structs(df.select(new_cols))

    def _ingest_products(self, df: pl.DataFrame, conn, category_hint: str = None):
        """Standardized Ingest with Force Metadata Overwrite and Auto-Aggregation."""
        df = self._flatten_structs(df)
        df = df.rename({c: c.lower() for c in df.columns})

        if not category_hint:
            first_titles = (
                " ".join([str(t) for t in df["title"].head(5).to_list() if t]).lower() if "title" in df.columns else ""
            )
            if "book" in first_titles or "drawing" in first_titles:
                category_hint = "book"
            elif "tumbler" in first_titles or "bottle" in first_titles:
                category_hint = "tumbler"
            else:
                category_hint = "comforter"

        mapping = {"asin": "asin", "parentasin": "parent_asin", "parent_asin": "parent_asin"}
        mapping.update({
            "producttitle": "title",
            "manufacturer": "brand",
            "countratings": "real_total_ratings",
            "productrating": "real_average_rating",
            "imageurllist/0": "image_url"
        })

        if category_hint == "comforter":
            mapping.update(
                {
                    "title": "title",
                    "brand": "brand",
                    "niche": "main_niche",
                    "main niche": "main_niche",
                    "countratings": "real_total_ratings",
                    "productrating": "real_average_rating",
                }
            )
        elif "productdetails" in df.columns:
            mapping.update(
                {
                    "title": "title",
                    "manufacturer": "brand",
                    "countreview": "real_total_ratings",
                    "productrating": "real_average_rating",
                    "mainimage/imageurl": "image_url",
                }
            )

        exprs = []
        added = set()
        if "url" in df.columns:
            df = df.with_columns(pl.col("url").str.extract(r"/dp/([A-Z0-9]{10})", 1).alias("url_asin"))
            df = df.with_columns(pl.coalesce(["url_asin", "asin"]).alias("asin"))

        for r, d in mapping.items():
            if r in df.columns and d not in added:
                if d == "real_average_rating":
                    exprs.append(
                        pl.col(r).cast(pl.Utf8).str.extract(r"(\d+\.?\d*)", 1).cast(pl.Float64, strict=False).alias(d)
                    )
                else:
                    exprs.append(pl.col(r).alias(d))
                added.add(d)

        # --- RATING BREAKDOWN LOGIC ---
        rb_map = {
            "5": "reviewsummary/fivestar/percentage",
            "4": "reviewsummary/fourstar/percentage",
            "3": "reviewsummary/threestar/percentage",
            "2": "reviewsummary/twostar/percentage",
            "1": "reviewsummary/onestar/percentage"
        }
        rb_cols_present = [v for v in rb_map.values() if v in df.columns]
        
        if rb_cols_present:
            # Construct JSON string like {"5": "80%", "4": "10%", ...}
            df = df.with_columns([
                pl.struct([pl.col(v).alias(k) for k, v in rb_map.items() if v in df.columns])
                .map_elements(lambda x: json.dumps(x) if x else None, return_dtype=pl.Utf8)
                .alias("rating_breakdown")
            ])
            if "rating_breakdown" not in added:
                exprs.append(pl.col("rating_breakdown"))
                added.add("rating_breakdown")

        if not exprs:
            return
        p_df = df.select(exprs).unique(subset=["asin"])

        type_map = {
            "asin": pl.Utf8,
            "parent_asin": pl.Utf8,
            "title": pl.Utf8,
            "brand": pl.Utf8,
            "image_url": pl.Utf8,
            "real_average_rating": pl.Float64,
            "real_total_ratings": pl.Int32,
            "rating_breakdown": pl.Utf8,
            "variation_count": pl.Int32,
            "material": pl.Utf8,
            "main_niche": pl.Utf8,
            "category": pl.Utf8,
        }
        for col, dtype in type_map.items():
            if col not in p_df.columns:
                p_df = p_df.with_columns(pl.lit(None).cast(dtype).alias(col))
            if col == "category" and p_df["category"].null_count() == len(p_df):
                p_df = p_df.with_columns(pl.lit(category_hint).alias("category"))

        # --- CLEAN & FALLBACK BRAND NAME ---
        p_df = p_df.with_columns(
            pl.col("brand")
            .str.replace("Visit the ", "")
            .str.replace(" Store", "")
            .str.replace("Brand: ", "")
            .str.replace(r"(?i)^by\s+", "")
            .str.replace(r"\s*\((Author|Producer|Creator|Contributor|Illustrator)\)", "")
            .str.strip_chars()
        )
        # Fallback: If brand is null, try to find ALL CAPS brand at start, else first word
        if "title" in p_df.columns:
            p_df = p_df.with_columns(
                pl.when(pl.col("brand").is_null() | (pl.col("brand") == ""))
                .then(
                    pl.col("title")
                    .str.extract(r"^([A-Z0-9]{2,}(?:\s[A-Z0-9]{2,})*)", 1) # Try CAPS sequence
                    .fill_null(pl.col("title").str.split(" ").list.get(0)) # FIXED: Use list.get(0)
                    .str.replace_all(r"[,:\-]", "") # Clean punctuation
                    .str.strip_chars()
                )
                .otherwise(pl.col("brand"))
                .alias("brand")
            )
        
        # DEBUG: Let's see what we got
        print("--- DEBUG P_DF (Metadata) ---")
        print(p_df.select(["asin", "brand", "title"]).head(5))

        # --- DB UPSERT ---
        conn.register("temp_p", p_df.to_arrow())
        conn.execute("""
            INSERT INTO product_parents (parent_asin, category, title, brand, image_url, last_updated)
            SELECT DISTINCT COALESCE(parent_asin, asin), COALESCE(category, 'generic'), title, brand, image_url, now()
            FROM temp_p ON CONFLICT (parent_asin) DO UPDATE SET
                category = COALESCE(excluded.category, product_parents.category),
                title = COALESCE(excluded.title, product_parents.title), 
                brand = COALESCE(excluded.brand, product_parents.brand),
                image_url = COALESCE(excluded.image_url, product_parents.image_url), 
                last_updated = now()
        """)
        conn.execute("""
            INSERT INTO products (asin, parent_asin, title, brand, image_url, real_average_rating, real_total_ratings, 
                                rating_breakdown, main_niche, category, last_updated)
            SELECT asin, COALESCE(parent_asin, asin), title, brand, image_url, real_average_rating, real_total_ratings, 
                   rating_breakdown, main_niche, category, now()
            FROM temp_p ON CONFLICT (asin) DO UPDATE SET
                title = COALESCE(excluded.title, products.title),
                brand = COALESCE(excluded.brand, products.brand),
                image_url = COALESCE(excluded.image_url, products.image_url),
                real_average_rating = COALESCE(excluded.real_average_rating, products.real_average_rating),
                real_total_ratings = COALESCE(excluded.real_total_ratings, products.real_total_ratings),
                rating_breakdown = COALESCE(excluded.rating_breakdown, products.rating_breakdown),
                main_niche = COALESCE(excluded.main_niche, products.main_niche),
                last_updated = now()
        """)
        conn.execute("""
            UPDATE product_parents SET niche = (
                SELECT STRING_AGG(DISTINCT main_niche, ', ') FROM products 
                WHERE products.parent_asin = product_parents.parent_asin AND main_niche IS NOT NULL AND main_niche != 'unknown'
            ) WHERE parent_asin IN (SELECT DISTINCT COALESCE(parent_asin, asin) FROM temp_p)
        """)

    def ingest_file(self, file_path: Path) -> Dict[str, Any]:
        if not file_path.exists():
            return {"error": "File not found"}
        target_db = Settings.get_standby_db_path()
        active_db = Settings.get_active_db_path()
        try:
            if active_db.exists():
                shutil.copy(active_db, target_db)
            self._init_schema(target_db)
            if file_path.suffix == ".xlsx":
                df = pl.read_excel(file_path)
            elif file_path.suffix == ".jsonl":
                df = pl.read_ndjson(file_path)
            else:
                return {"error": "Format not supported"}

            with duckdb.connect(str(target_db)) as conn:
                self._ingest_products(df, conn)
                df_clean = self._clean_dataframe(df, file_path.name)
                if not df_clean.is_empty():
                    conn.register("temp_reviews_raw", df_clean.to_arrow())

                    # 1. FALLBACK MECHANISM: Create missing parents first to satisfy Foreign Key
                    # This handles cases where a completely new product is scraped
                    conn.execute("""
                        INSERT INTO product_parents (parent_asin, category, title, brand, verification_status)
                        SELECT DISTINCT 
                            COALESCE(p.parent_asin, tr.parent_asin), 
                            'unknown', 
                            'Recovered Product: ' || COALESCE(p.parent_asin, tr.parent_asin),
                            'Unknown',
                            'UNCERTAIN'
                        FROM temp_reviews_raw tr
                        LEFT JOIN products p ON tr.child_asin = p.asin
                        WHERE COALESCE(p.parent_asin, tr.parent_asin) NOT IN (SELECT parent_asin FROM product_parents)
                    """)

                    # 2. ROBUST REVIEW LINKING (Lookup real parent from products table)
                    conn.execute("""
                        INSERT INTO reviews (
                            review_id, parent_asin, child_asin, variation_text, author_name, 
                            rating_score, title, text, review_date, is_verified, 
                            vine_program, helpful_count, source_file, mining_status, ingested_at
                        )
                        SELECT tr.review_id, COALESCE(p.parent_asin, tr.parent_asin), tr.child_asin, tr.variation_text, 
                               tr.author_name, tr.rating_score, tr.title, tr.text, tr.review_date, tr.is_verified,
                               tr.vine_program, tr.helpful_count, tr.source_file, tr.mining_status, current_timestamp
                        FROM temp_reviews_raw tr
                        LEFT JOIN products p ON tr.child_asin = p.asin
                        WHERE tr.review_id NOT IN (SELECT review_id FROM reviews)
                    """)
            Settings.swap_db()
            return {"total_rows": len(df), "db_switched_to": target_db.name}
        except Exception as e:
            return {"error": str(e)}
