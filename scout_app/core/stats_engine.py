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
        """Extract basic KPIs from products table (with fallback to reviews)."""
        sql = """
            SELECT 
                parent_asin,
                real_total_ratings,
                real_average_rating,
                variation_count,
                rating_breakdown
            FROM products
            WHERE asin = ?
        """
        df = self._query_df(conn, sql, [asin])

        # Fallback to local counts if metadata is missing
        local_stats = conn.execute(
            """
            SELECT COUNT(*), AVG(rating_score) 
            FROM reviews WHERE parent_asin = ?
        """,
            [asin],
        ).fetchone()

        local_total = local_stats[0] if local_stats else 0
        local_avg = local_stats[1] if local_stats else 0.0

        if df.empty:
            return {
                "total_reviews": local_total,
                "avg_rating": float(local_avg),
                "total_variations": 0,
                "neg_pct": 0.0,
                "is_fallback": True,
            }

        row = df.iloc[0]

        # Use Real Ratings if available, else local
        total_reviews = int(row["real_total_ratings"]) if pd.notnull(row["real_total_ratings"]) else local_total
        avg_rating = float(row["real_average_rating"]) if pd.notnull(row["real_average_rating"]) else float(local_avg)

        # Variations Fallback
        variations = int(row["variation_count"]) if pd.notnull(row["variation_count"]) else 0
        if variations == 0:
            try:
                v_count = conn.execute(
                    "SELECT COUNT(DISTINCT child_asin) FROM reviews WHERE parent_asin = ?", [asin]
                ).fetchone()[0]
                variations = v_count
            except:
                pass

        # Calculate neg_pct from breakdown if possible
        neg_pct = 0
        try:
            rb = row["rating_breakdown"]
            if isinstance(rb, str):
                rb = json.loads(rb)
            total_rb = sum(rb.values())
            if total_rb > 0:
                # Assuming rb values are counts or percentages
                neg_pct = (float(rb.get("1", 0)) + float(rb.get("2", 0))) / total_rb * 100
        except:
            pass

        return {
            "total_reviews": total_reviews,
            "avg_rating": avg_rating,
            "total_variations": variations,
            "neg_pct": float(neg_pct),
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
        return df.to_dict(orient="records")

    def calculate_sentiment_weighted(self, conn, asin):
        """
        Calculates 'Estimated Customer Impact' (Commercial Logic).
        Extrapolates sample data to real population volume to fix sampling bias.
        """
        # 1. Get Real Population Stats
        p_row = self._query_df(conn, "SELECT real_total_ratings, rating_breakdown FROM products WHERE asin = ?", [asin])

        # Fallback counts if real metadata is missing
        local_total = conn.execute("SELECT COUNT(*) FROM reviews WHERE parent_asin = ?", [asin]).fetchone()[0]

        real_total = p_row.iloc[0]["real_total_ratings"] if not p_row.empty else local_total
        if pd.isnull(real_total) or real_total == 0:
            real_total = local_total  # Hard fallback

        if real_total == 0:
            return []

        breakdown_json = p_row.iloc[0]["rating_breakdown"] if not p_row.empty else None
        real_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}

        try:
            if breakdown_json:
                bd = json.loads(breakdown_json) if isinstance(breakdown_json, str) else breakdown_json
                total_bd = sum(bd.values())
                if total_bd > 0:
                    for k, v in bd.items():
                        real_counts[int(k)] = (float(v) / total_bd) * real_total
            else:
                # If no breakdown, use local star distribution as proxy
                local_bd = conn.execute(
                    """
                    SELECT CAST(ROUND(rating_score) AS INTEGER) as star, COUNT(*) 
                    FROM reviews WHERE parent_asin = ? GROUP BY 1
                """,
                    [asin],
                ).fetchall()
                total_local = sum(r[1] for r in local_bd)
                if total_local > 0:
                    for star, count in local_bd:
                        if star in real_counts:
                            real_counts[star] = (count / total_local) * real_total
        except:
            # Last resort: flat distribution (not ideal but avoids crash)
            for s in real_counts:
                real_counts[s] = real_total / 5.0

        # 2. Get Sample Stats (Mention Rates per Star)
        # We need: For each aspect, for each star, how many mentions vs total sample size at that star?

        # Total samples per star (Denominator)
        sample_counts_df = self._query_df(
            conn,
            """
            SELECT CAST(ROUND(rating_score) AS INTEGER) as star, COUNT(*) as cnt 
            FROM reviews 
            WHERE parent_asin = ? 
            GROUP BY 1
        """,
            [asin],
        )
        sample_counts = {r["star"]: r["cnt"] for r in sample_counts_df.to_dict("records")}

        # Aspect mentions per star (Numerator)
        aspect_df = self._query_df(
            conn,
            """
            SELECT 
                COALESCE(am.standard_aspect, rt.aspect) as aspect,
                CAST(ROUND(r.rating_score) AS INTEGER) as star,
                rt.sentiment,
                COUNT(*) as cnt
            FROM review_tags rt
            JOIN reviews r ON rt.review_id = r.review_id
            LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
            WHERE rt.parent_asin = ?
            GROUP BY 1, 2, 3
        """,
            [asin],
        )

        if aspect_df.empty:
            return []

        # 3. Calculate Estimated Impact
        # aspect_impact = {aspect: {'pos': 0, 'neg': 0}}
        impact_map = {}

        for _, row in aspect_df.iterrows():
            if pd.isnull(row["star"]):
                continue
            aspect = row["aspect"]
            star = int(row["star"])
            sentiment = row["sentiment"]
            count = row["cnt"]

            if star not in sample_counts or sample_counts[star] == 0:
                continue
            if star not in real_counts:
                continue

            # Rate in Sample = Count / Sample_Size_At_Star
            rate = count / sample_counts[star]

            # Est. Real Volume = Rate * Real_Population_At_Star
            est_volume = rate * real_counts[star]

            if aspect not in impact_map:
                impact_map[aspect] = {"pos": 0, "neg": 0}

            if sentiment == "Positive":
                impact_map[aspect]["pos"] += est_volume
            else:
                impact_map[aspect]["neg"] += est_volume

        # 4. Format Result
        results = []
        for aspect, vals in impact_map.items():
            net = vals["pos"] - vals["neg"]
            total_vol = vals["pos"] + vals["neg"]
            results.append(
                {
                    "aspect": aspect,
                    "est_positive": int(vals["pos"]),
                    "est_negative": int(vals["neg"]),
                    "net_impact": int(net),
                    "total_impact_vol": int(total_vol),
                }
            )

        # Sort by magnitude of impact (Absolute Net or Total Volume?)
        # User wants to see what drives 1 star vs 5 star.
        # Sort by Net Impact (Most Positive to Most Negative)
        results.sort(key=lambda x: x["net_impact"], reverse=True)

        # Take Top 15 (Positive & Negative mix)
        # To ensure we see both extremes, let's take Top 8 Positive and Top 7 Negative?
        # Or just sort by Total Volume?
        # Let's return Top 20 by Total Volume, then UI can sort by Net Impact.
        results.sort(key=lambda x: x["total_impact_vol"], reverse=True)
        return results[:20]

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
        return df.to_dict(orient="records")

    def calculate_all(self, asin, conn=None):
        """Main entry point to aggregate everything."""
        if conn:
            return self._calculate_logic(conn, asin)

        with duckdb.connect(self.db_path) as conn:
            return self._calculate_logic(conn, asin)

    def _calculate_logic(self, conn, asin):
        """Internal logic using an existing connection."""
        return {
            "asin": asin,
            "last_calc": datetime.now().isoformat(),
            "kpis": self.calculate_kpis(conn, asin),
            "sentiment_raw": self.calculate_sentiment_raw(conn, asin),
            "sentiment_weighted": self.calculate_sentiment_weighted(conn, asin),
            "rating_trend": self.calculate_rating_trend(conn, asin),
        }

    def save_to_db(self, asin, metrics_dict, conn=None):
        """Upsert metrics into product_stats table."""
        json_str = json.dumps(metrics_dict)
        now = datetime.now()

        # 1. Update product_stats (SWOT Source)
        sql_stats = """
            INSERT INTO product_stats (asin, last_updated, metrics_json)
            VALUES (?, ?, ?)
            ON CONFLICT (asin) DO UPDATE SET 
                metrics_json = EXCLUDED.metrics_json,
                last_updated = EXCLUDED.last_updated
        """

        if conn:
            conn.execute(sql_stats, [asin, now, json_str])
        else:
            with duckdb.connect(self.db_path) as conn:
                conn.execute(sql_stats, [asin, now, json_str])

    def calculate_and_save(self, asin, conn=None):
        """Single ASIN calculation and save."""
        if conn:
            data = self._calculate_logic(conn, asin)
            self.save_to_db(asin, data, conn=conn)
        else:
            with duckdb.connect(self.db_path) as conn:
                data = self._calculate_logic(conn, asin)
                self.save_to_db(asin, data, conn=conn)
        return data
