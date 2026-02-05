import polars as pl
import json
import re

class MetadataParser:
    """
    Expert Module for refining raw scraper data into 'products' table ready metadata.
    Handles both Review Scraper (XLSX) and Product Details Scraper (JSONL).
    """

    @staticmethod
    def refine_metadata(df: pl.DataFrame, category_hint: str = None) -> pl.DataFrame:
        """
        Main entry point. Transforms raw DataFrame into a clean Product Metadata DataFrame.
        """
        
        # 1. Standardize Column Names
        df = df.rename({c: c.lower() for c in df.columns})
        
        # 2. Smart Mapping (Unified Logic)
        # Priorities:
        # - countratings > countreview (Review Scraper metadata is usually better for total)
        # - producttitle > title
        mapping = {"asin": "asin", "parentasin": "parent_asin", "parent_asin": "parent_asin"}
        mapping.update({
            "producttitle": "title",
            "manufacturer": "brand",
            "countratings": "real_total_ratings",
            "countreview": "real_total_ratings", 
            "productrating": "real_average_rating",
            "imageurllist/0": "image_url",
            "mainimage/imageurl": "image_url"
        })

        if category_hint == "comforter":
            mapping.update({"niche": "main_niche", "main niche": "main_niche"})
        
        # Build selection expressions
        exprs = []
        added = set()
        
        # URL parsing fallback for ASIN
        if "url" in df.columns:
            df = df.with_columns(pl.col("url").str.extract(r"/dp/([A-Z0-9]{10})", 1).alias("url_asin"))
            df = df.with_columns(pl.coalesce(["url_asin", "asin"]).alias("asin"))

        for r, d in mapping.items():
            if r in df.columns and d not in added:
                if d == "real_average_rating":
                    exprs.append(
                        pl.col(r).cast(pl.Utf8)
                        .str.extract(r"(\d+\.?\d*)", 1)
                        .cast(pl.Float64, strict=False)
                        .alias(d)
                    )
                else:
                    exprs.append(pl.col(r).alias(d))
                added.add(d)

        # 3. Rating Breakdown (Review Scraper Exclusive)
        rb_map = {
            "5": "reviewsummary/fivestar/percentage",
            "4": "reviewsummary/fourstar/percentage",
            "3": "reviewsummary/threestar/percentage",
            "2": "reviewsummary/twostar/percentage",
            "1": "reviewsummary/onestar/percentage"
        }
        rb_cols_present = [v for v in rb_map.values() if v in df.columns]
        
        if rb_cols_present:
            df = df.with_columns([
                pl.struct([pl.col(v).alias(k) for k, v in rb_map.items() if v in df.columns])
                .map_elements(lambda x: json.dumps(x) if x else None, return_dtype=pl.Utf8)
                .alias("rating_breakdown")
            ])
            if "rating_breakdown" not in added:
                exprs.append(pl.col("rating_breakdown"))
                added.add("rating_breakdown")

        # 4. DNA Extraction (Product Details Scraper)
        if "productdetails" in df.columns:
            # Helper to extract value by name key
            def extract_dna(val_list, key_name):
                if val_list is None: return None
                # Polars sometimes passes a Series or list of dicts
                items = val_list.to_list() if hasattr(val_list, 'to_list') else val_list
                for item in items:
                    if isinstance(item, dict) and item.get("name", "").strip().lower() == key_name.lower():
                        return item.get("value")
                return None

            df = df.with_columns([
                pl.col("productdetails").map_elements(lambda x: json.dumps(x.to_list() if hasattr(x, 'to_list') else x) if x is not None else None, return_dtype=pl.Utf8).alias("specs_json"),
                pl.col("productdetails").map_elements(lambda x: extract_dna(x, "material"), return_dtype=pl.Utf8).alias("material"),
                pl.col("productdetails").map_elements(lambda x: extract_dna(x, "reading age") or extract_dna(x, "target audience"), return_dtype=pl.Utf8).alias("target_audience")
            ])
            
            for col in ["specs_json", "material", "target_audience"]:
                if col not in added:
                    exprs.append(pl.col(col))
                    added.add(col)

        if not exprs:
            return pl.DataFrame() # Empty if no valid cols found

        # 5. Extract Unique Products
        p_df = df.select(exprs).unique(subset=["asin"])

        # 6. Type Enforcement (Prepare for DB)
        type_map = {
            "asin": pl.Utf8, "parent_asin": pl.Utf8, "title": pl.Utf8, "brand": pl.Utf8,
            "image_url": pl.Utf8, "real_average_rating": pl.Float64, "real_total_ratings": pl.Int32,
            "rating_breakdown": pl.Utf8, "variation_count": pl.Int32, "material": pl.Utf8,
            "main_niche": pl.Utf8, "category": pl.Utf8, "specs_json": pl.Utf8
        }
        
        for col, dtype in type_map.items():
            if col not in p_df.columns:
                p_df = p_df.with_columns(pl.lit(None).cast(dtype).alias(col))
            if col == "category" and p_df["category"].null_count() == len(p_df):
                p_df = p_df.with_columns(pl.lit(category_hint).alias("category"))

        # 7. Brand Cleaning & Smart Fallback
        p_df = MetadataParser._clean_and_fallback_brand(p_df)

        return p_df

    @staticmethod
    def _clean_and_fallback_brand(df: pl.DataFrame) -> pl.DataFrame:
        if "brand" not in df.columns:
            return df
            
        # Basic Cleaning
        df = df.with_columns(
            pl.col("brand")
            .str.replace("Visit the ", "")
            .str.replace(" Store", "")
            .str.replace("Brand: ", "")
            .str.replace(r"(?i)^by\s+", "")
            .str.replace(r"\s*\((Author|Producer|Creator|Contributor|Illustrator)\)", "")
            .str.strip_chars()
        )
        
        # Smart Fallback from Title (CAPS LOCK Strategy)
        if "title" in df.columns:
            df = df.with_columns(
                pl.when(pl.col("brand").is_null() | (pl.col("brand") == ""))
                .then(
                    pl.col("title")
                    .str.extract(r"^([A-Z0-9]{2,}(?:\s[A-Z0-9]{2,})*)", 1) # Try CAPS sequence
                    .fill_null(pl.col("title").str.split(" ").list.get(0)) # Fallback to 1st word
                    .str.replace_all(r"[,:\-]", "") 
                    .str.strip_chars()
                )
                .otherwise(pl.col("brand"))
                .alias("brand")
            )
        return df
