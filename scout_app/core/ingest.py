import duckdb
import polars as pl
from pathlib import Path
from typing import Dict, Any
import shutil
import os
import json
from .config import Settings
from .metadata_parser import MetadataParser


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
        
        # 1. Refine Metadata using specialized Parser
        p_df = MetadataParser.refine_metadata(df, category_hint)
        
        if p_df.is_empty():
            return
        
        # DEBUG: Write to file so agent can read
        try:
            debug_info = {
                "columns": p_df.columns,
                "sample_j3": p_df.filter(pl.col('asin') == 'B0C7CC5BJ3').to_dicts()
            }
            with open("scout_app/logs/debug_ingest.json", "w") as f:
                json.dump(debug_info, f, indent=2)
        except:
            pass

        # --- DB UPSERT (Robust Join-Update Strategy) ---
        conn.register("temp_p", p_df.to_arrow())
        
        # 1. Update product_parents (The Families)
        conn.execute("""
            INSERT OR IGNORE INTO product_parents (parent_asin, category, title, brand, image_url, last_updated)
            SELECT DISTINCT COALESCE(parent_asin, asin), COALESCE(category, 'generic'), title, brand, image_url, now()
            FROM temp_p
        """)
        conn.execute("""
            UPDATE product_parents
            SET 
                category = COALESCE(temp_p.category, product_parents.category),
                title = COALESCE(temp_p.title, product_parents.title),
                brand = COALESCE(temp_p.brand, product_parents.brand),
                image_url = COALESCE(temp_p.image_url, product_parents.image_url),
                last_updated = now()
            FROM temp_p
            WHERE product_parents.parent_asin = COALESCE(temp_p.parent_asin, temp_p.asin)
        """)

        # 2. Update products (The Children)
        # 2.1. Insert new ones first
        conn.execute("""
            INSERT OR IGNORE INTO products (asin, parent_asin, title, brand, image_url, real_average_rating, 
                                          real_total_ratings, rating_breakdown, main_niche, category, 
                                          material, target_audience, specs_json, last_updated)
            SELECT asin, COALESCE(parent_asin, asin), title, brand, image_url, real_average_rating, 
                   real_total_ratings, rating_breakdown, main_niche, category, 
                   material, target_audience, specs_json, now()
            FROM temp_p
        """)
        # 2.2. Update existing ones (Metadata Enrichment)
        conn.execute("""
            UPDATE products
            SET 
                parent_asin = COALESCE(temp_p.parent_asin, products.parent_asin),
                title = COALESCE(temp_p.title, products.title),
                brand = COALESCE(temp_p.brand, products.brand),
                image_url = COALESCE(temp_p.image_url, products.image_url),
                real_average_rating = COALESCE(temp_p.real_average_rating, products.real_average_rating),
                real_total_ratings = COALESCE(temp_p.real_total_ratings, products.real_total_ratings),
                rating_breakdown = COALESCE(temp_p.rating_breakdown, products.rating_breakdown),
                main_niche = COALESCE(temp_p.main_niche, products.main_niche),
                material = COALESCE(temp_p.material, products.material),
                target_audience = COALESCE(temp_p.target_audience, products.target_audience),
                specs_json = COALESCE(temp_p.specs_json, products.specs_json),
                last_updated = now()
            FROM temp_p
            WHERE products.asin = temp_p.asin
        """)
        # 3. Infer Parent in 'products' table (The "Con báo hiếu Cha" Logic)
        # If parent doesn't exist in products table, create it using child's metadata as a placeholder
        conn.execute("""
            INSERT INTO products (asin, parent_asin, title, brand, image_url, main_niche, category, verification_status, last_updated)
            SELECT DISTINCT 
                parent_asin, 
                parent_asin, 
                title, 
                brand, 
                image_url, 
                main_niche, 
                category, 
                'INFERRED_FROM_CHILD', 
                now()
            FROM temp_p
            WHERE parent_asin IS NOT NULL AND parent_asin != asin
            ON CONFLICT (asin) DO NOTHING
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
