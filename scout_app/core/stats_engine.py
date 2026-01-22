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
        
        # Variations Fallback
        variations = int(row['total_variations']) if pd.notnull(row['total_variations']) else 0
        if variations == 0:
            # Try counting from reviews
            try:
                v_count = conn.execute("SELECT COUNT(DISTINCT child_asin) FROM reviews WHERE parent_asin = ?", [asin]).fetchone()[0]
                variations = v_count
            except:
                pass

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
            "total_variations": variations,
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
        """
        Calculates 'Estimated Customer Impact' (Commercial Logic).
        Extrapolates sample data to real population volume to fix sampling bias.
        """
        # 1. Get Real Population Stats
        p_row = self._query_df(conn, "SELECT real_total_ratings, rating_breakdown FROM products WHERE asin = ?", [asin])
        if p_row.empty: return []
        
        real_total = p_row.iloc[0]['real_total_ratings']
        if pd.isnull(real_total) or real_total == 0: return []
        
        breakdown_json = p_row.iloc[0]['rating_breakdown']
        real_counts = {5:0, 4:0, 3:0, 2:0, 1:0}
        
        try:
            if breakdown_json:
                bd = json.loads(breakdown_json) if isinstance(breakdown_json, str) else breakdown_json
                # bd is usually percentages like {"5": 70, "4": 10...} or counts.
                # Assuming percentages summing to ~100 or 1.0. Let's normalize.
                total_bd = sum(bd.values())
                if total_bd > 0:
                    for k, v in bd.items():
                        real_counts[int(k)] = (v / total_bd) * real_total
        except:
            return []

        # 2. Get Sample Stats (Mention Rates per Star)
        # We need: For each aspect, for each star, how many mentions vs total sample size at that star?
        
        # Total samples per star (Denominator)
        sample_counts_df = self._query_df(conn, """
            SELECT CAST(ROUND(rating_score) AS INTEGER) as star, COUNT(*) as cnt 
            FROM reviews 
            WHERE parent_asin = ? 
            GROUP BY 1
        """, [asin])
        sample_counts = {r['star']: r['cnt'] for r in sample_counts_df.to_dict('records')}

        # Aspect mentions per star (Numerator)
        aspect_df = self._query_df(conn, """
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
        """, [asin])

        if aspect_df.empty: return []

        # 3. Calculate Estimated Impact
        # aspect_impact = {aspect: {'pos': 0, 'neg': 0}}
        impact_map = {}

        for _, row in aspect_df.iterrows():
            aspect = row['aspect']
            star = int(row['star'])
            sentiment = row['sentiment']
            count = row['cnt']
            
            if star not in sample_counts or sample_counts[star] == 0: continue
            if star not in real_counts: continue

            # Rate in Sample = Count / Sample_Size_At_Star
            rate = count / sample_counts[star]
            
            # Est. Real Volume = Rate * Real_Population_At_Star
            est_volume = rate * real_counts[star]
            
            if aspect not in impact_map: impact_map[aspect] = {'pos': 0, 'neg': 0}
            
            if sentiment == 'Positive':
                impact_map[aspect]['pos'] += est_volume
            else:
                impact_map[aspect]['neg'] += est_volume

        # 4. Format Result
        results = []
        for aspect, vals in impact_map.items():
            net = vals['pos'] - vals['neg']
            total_vol = vals['pos'] + vals['neg']
            results.append({
                "aspect": aspect,
                "est_positive": int(vals['pos']),
                "est_negative": int(vals['neg']),
                "net_impact": int(net),
                "total_impact_vol": int(total_vol)
            })
            
        # Sort by magnitude of impact (Absolute Net or Total Volume?)
        # User wants to see what drives 1 star vs 5 star. 
        # Sort by Net Impact (Most Positive to Most Negative)
        results.sort(key=lambda x: x['net_impact'], reverse=True)
        
        # Take Top 15 (Positive & Negative mix)
        # To ensure we see both extremes, let's take Top 8 Positive and Top 7 Negative?
        # Or just sort by Total Volume?
        # Let's return Top 20 by Total Volume, then UI can sort by Net Impact.
        results.sort(key=lambda x: x['total_impact_vol'], reverse=True)
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
