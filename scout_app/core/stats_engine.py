import json
import duckdb
import pandas as pd
from datetime import datetime
from .config import Settings

class StatsEngine:
    def __init__(self, db_path=None):
        self.db_path = db_path or str(Settings.get_active_db_path())

    def _query_df(self, conn, sql, params=None):
        return conn.execute(sql, params).df()

    def _query_one(self, conn, sql, params=None):
        res = conn.execute(sql, params).fetchone()
        return res[0] if res else None

    def calculate_kpis(self, conn, asin):
        """Extract basic KPIs from products table."""
        sql = """
            SELECT 
                real_total_ratings as total_reviews,
                real_average_rating as avg_rating,
                variation_count as total_variations,
                rating_breakdown
            FROM products
            WHERE asin = ?
        """
        df = self._query_df(conn, sql, [asin])
        if df.empty:
            return {}
        
        row = df.iloc[0]
        # Calculate neg_pct from breakdown if possible
        neg_pct = 0
        try:
            rb = row['rating_breakdown']
            if isinstance(rb, str): rb = json.loads(rb)
            total = sum(rb.values())
            if total > 0:
                neg_pct = (rb.get('1', 0) + rb.get('2', 0)) / total * 100
        except:
            pass

        return {
            "total_reviews": int(row['total_reviews']) if pd.notnull(row['total_reviews']) else 0,
            "avg_rating": float(row['avg_rating']) if pd.notnull(row['avg_rating']) else 0.0,
            "total_variations": int(row['total_variations']) if pd.notnull(row['total_variations']) else 0,
            "neg_pct": float(neg_pct)
        }

    def calculate_sentiment_raw(self, conn, asin):
        """Ported from Market_Intelligence.py"""
        sql = """
            SELECT 
                COALESCE(am.standard_aspect, rt.aspect) as aspect,
                SUM(CASE WHEN rt.sentiment = 'Positive' THEN 1 ELSE 0 END) as positive,
                SUM(CASE WHEN rt.sentiment = 'Negative' THEN 1 ELSE 0 END) as negative
            FROM review_tags rt
            LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
            WHERE rt.parent_asin = ?
            GROUP BY 1
            HAVING (positive + negative) > 1 
            ORDER BY (positive + negative) DESC
            LIMIT 15
        """
        df = self._query_df(conn, sql, [asin])
        return df.to_dict(orient='records')

    def calculate_sentiment_weighted(self, conn, asin):
        """Ported from Market_Intelligence.py (The heavy one)"""
        # 1. Get Weights
        w_json = self._query_one(conn, "SELECT rating_breakdown FROM products WHERE asin = ?", [asin])
        weights = {5:0, 4:0, 3:0, 2:0, 1:0}
        if w_json:
            try:
                raw_w = json.loads(w_json) if isinstance(w_json, str) else w_json
                total_w = sum(raw_w.values())
                if total_w > 0:
                    weights = {int(k): v / total_w for k, v in raw_w.items()}
            except: return []

        # 2. Weighted SQL
        weighted_sql = f"""
            WITH base AS (
                SELECT 
                    COALESCE(am.standard_aspect, rt.aspect) as aspect,
                    CAST(ROUND(r.rating_score) AS INTEGER) as star,
                    rt.sentiment
                FROM review_tags rt
                JOIN reviews r ON rt.review_id = r.review_id
                LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
                WHERE rt.parent_asin = ?
            ),
            aspect_stats AS (
                SELECT aspect, star,
                    SUM(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as pos_rate
                FROM base GROUP BY 1, 2
            ),
            weighted_calc AS (
                SELECT aspect,
                    SUM(pos_rate * CASE 
                        WHEN star = 5 THEN {weights.get(5, 0)}
                        WHEN star = 4 THEN {weights.get(4, 0)}
                        WHEN star = 3 THEN {weights.get(3, 0)}
                        WHEN star = 2 THEN {weights.get(2, 0)}
                        WHEN star = 1 THEN {weights.get(1, 0)}
                        ELSE 0 END) as score
                FROM aspect_stats GROUP BY 1
            )
            SELECT aspect, score * 100 as score_pct FROM weighted_calc ORDER BY score ASC LIMIT 15
        """
        df = self._query_df(conn, weighted_sql, [asin])
        return df.to_dict(orient='records')

    def calculate_rating_trend(self, conn, asin):
        sql = """
            SELECT 
                CAST(DATE_TRUNC('month', review_date) AS VARCHAR) as month, 
                AVG(rating_score) as avg_score 
            FROM reviews 
            WHERE parent_asin = ? 
            GROUP BY 1 ORDER BY 1
        """
        df = self._query_df(conn, sql, [asin])
        return df.to_dict(orient='records')

    def calculate_all(self, asin):
        """Main entry point to aggregate everything."""
        with duckdb.connect(self.db_path) as conn:
            data = {
                "asin": asin,
                "last_calc": datetime.now().isoformat(),
                "kpis": self.calculate_kpis(conn, asin),
                "sentiment_raw": self.calculate_sentiment_raw(conn, asin),
                "sentiment_weighted": self.calculate_sentiment_weighted(conn, asin),
                "rating_trend": self.calculate_rating_trend(conn, asin)
            }
            return data

    def save_to_db(self, asin, metrics_dict):
        """Upsert metrics into product_stats table."""
        # Use a fresh connection for writing to avoid issues
        with duckdb.connect(self.db_path) as conn:
            json_str = json.dumps(metrics_dict)
            now = datetime.now()
            sql = """
                INSERT INTO product_stats (asin, last_updated, metrics_json)
                VALUES (?, ?, ?)
                ON CONFLICT (asin) DO UPDATE SET 
                    metrics_json = EXCLUDED.metrics_json,
                    last_updated = EXCLUDED.last_updated
            """
            conn.execute(sql, [asin, now, json_str])

    def calculate_and_save(self, asin):
        data = self.calculate_all(asin)
        self.save_to_db(asin, data)
        return data
