import json
import duckdb
import pandas as pd
import streamlit as st
import sys
import uuid
from pathlib import Path
import time
import functools

# Add root to sys.path to find core
# Assuming this file is in scout_app/ui/common.py, root is ../../
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from scout_app.core.config import Settings

def time_it(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        print(f"👉 [START] {func.__name__}")
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            print(f"❌ [ERROR] {func.__name__}: {e}")
            raise e
        end = time.time()
        print(f"✅ [END] {func.__name__} took {end - start:.4f}s")
        return result
    return wrapper

# --- Database Helpers ---

@time_it
def query_df(sql, params=None):
    with duckdb.connect(Settings.get_active_db_path(), read_only=True) as conn:
        return conn.execute(sql, params).df()

@time_it
def query_one(sql, params=None):
    with duckdb.connect(Settings.get_active_db_path(), read_only=True) as conn:
        res = conn.execute(sql, params).fetchone()
        return res[0] if res else None


# --- Cached Data Functions ---
@st.cache_data
def get_raw_sentiment_data(asin: str):
    """Fetch raw mention counts for sentiment analysis (unweighted)."""
    aspect_query = """
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
        LIMIT 10
    """
    return query_df(aspect_query, [asin])

@st.cache_data
def get_weighted_sentiment_data(asin: str):
    """Fetch and calculate the weighted sentiment score using DuckDB."""
    # 1. Get Weights from Histogram
    w_query = "SELECT rating_breakdown FROM products WHERE asin = ?"
    w_json = query_one(w_query, [asin])
    
    weights = {5:0, 4:0, 3:0, 2:0, 1:0}
    has_weights = False
    if w_json:
        import json
        try:
            raw_w = json.loads(w_json) if isinstance(w_json, str) else w_json
            total_w = sum(raw_w.values())
            if total_w > 0:
                weights = {int(k): v / total_w for k, v in raw_w.items()}
                has_weights = True
        except:
            pass 

    if not has_weights:
        return pd.DataFrame()

    # 2. Optimized SQL Aggregation
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
            SELECT 
                aspect,
                star,
                SUM(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as pos_rate
            FROM base
            GROUP BY 1, 2
        ),
        weighted_calc AS (
            SELECT 
                aspect,
                SUM(
                    pos_rate * CASE 
                        WHEN star = 5 THEN {weights.get(5, 0)}
                        WHEN star = 4 THEN {weights.get(4, 0)}
                        WHEN star = 3 THEN {weights.get(3, 0)}
                        WHEN star = 2 THEN {weights.get(2, 0)}
                        WHEN star = 1 THEN {weights.get(1, 0)}
                        ELSE 0
                    END
                ) as score
            FROM aspect_stats
            GROUP BY 1
        )
        SELECT aspect, score
        FROM weighted_calc
        ORDER BY score ASC
        LIMIT 15
    """
    df_weighted = query_df(weighted_sql, [asin])
    if not df_weighted.empty:
        df_weighted['score_pct'] = df_weighted['score'] * 100
    return df_weighted

@st.cache_data(ttl=300)
def get_precalc_stats(asin):
    print(f"[DEBUG] Fetching Pre-calc for: {asin}")
    sql = "SELECT metrics_json FROM product_stats WHERE asin = ?"
    try:
        res = query_one(sql, [asin])
        print(f"[DEBUG] Result for {asin}: {'FOUND' if res else 'NONE'}")
        if res:
            try:
                res_obj = json.loads(res) if isinstance(res, str) else res
                print(f"[DEBUG] JSON Size: {len(res)/1024:.2f} KB")
                return res_obj
            except Exception as e:
                print(f"[DEBUG] JSON Parse Error: {e}")
                return None
    except Exception as e:
        print(f"[DEBUG] DB Error: {e}")
        return None
    return None

@st.cache_data
def get_evidence_data(asin: str):
    """Fetch evidence quotes with caching to prevent UI lag on reruns."""
    ev_query = """
        SELECT 
            COALESCE(am.category, rt.category) as "Category",
            CASE 
                WHEN am.standard_aspect IS NOT NULL THEN '✅ ' || am.standard_aspect
                ELSE '⏳ ' || rt.aspect 
            END as "Aspect (Status)",
            rt.sentiment as "Sentiment", 
            rt.quote as "Evidence Quote"
        FROM review_tags rt
        LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
        WHERE rt.parent_asin = ?
        ORDER BY rt.sentiment, "Category"
        LIMIT 200
    """
    return query_df(ev_query, [asin])

@st.cache_data(ttl=3600)
def get_niche_benchmark(niche: str):
    """Calculate average satisfaction % per aspect for an entire niche."""
    if not niche or niche in ["None", "Non-defined"]:
        return None

    sql = """
        SELECT metrics_json 
        FROM product_stats ps
        JOIN products p ON ps.asin = p.asin
        WHERE p.main_niche = ?
    """
    results = query_df(sql, [niche])
    if results.empty:
        return None

    import json
    aspect_totals = {}  # {aspect: {'pos': 0, 'neg': 0}}

    for _, row in results.iterrows():
        try:
            m = json.loads(row["metrics_json"]) if isinstance(row["metrics_json"], str) else row["metrics_json"]
            for item in m.get("sentiment_weighted", []):
                asp = item["aspect"]
                if asp not in aspect_totals:
                    aspect_totals[asp] = {"pos": 0, "neg": 0}
                aspect_totals[asp]["pos"] += item["est_positive"]
                aspect_totals[asp]["neg"] += item["est_negative"]
        except:
            continue

    # Calculate %
    benchmark = {}
    for asp, vals in aspect_totals.items():
        total = vals["pos"] + vals["neg"]
        if total > 50:  # Only include aspects with significant volume across niche
            benchmark[asp] = (vals["pos"] / total) * 100

    return benchmark


def request_new_asin(asin_input, note="", force_update=False, user_id=None):
    """
    Smart Request Handler V2
    """
    db_path = str(Settings.get_active_db_path())
    final_asin = asin_input
    system_note = ""
    is_unknown = False

    try:
        with duckdb.connect(db_path, read_only=True) as conn:
            # 1. Lookup Product Logic
            row = conn.execute(
                "SELECT parent_asin FROM products WHERE asin = ? OR parent_asin = ? LIMIT 1", [asin_input, asin_input]
            ).fetchone()

            if row:
                mapped_parent = row[0]
                if mapped_parent and mapped_parent != asin_input:
                    final_asin = mapped_parent
                    system_note = f"[Auto-Map] Child {asin_input} -> Parent {final_asin}"
            else:
                is_unknown = True
                system_note = "[Unknown ASIN] Not in Product DB. Admin verify Parent."

            # 2. Check Existing Data (Reviews)
            rev_stats = conn.execute(
                "SELECT COUNT(*), MAX(review_date) FROM reviews WHERE parent_asin = ?", [final_asin]
            ).fetchone()
            has_data = rev_stats[0] > 0
            last_date = rev_stats[1]

            if has_data and not force_update:
                return (
                    False,
                    f"🛑 Đã có dữ liệu! Tìm thấy {rev_stats[0]} reviews (Mới nhất: {last_date}). Nếu cần cập nhật, hãy tick 'Force Update'.",
                )

            if has_data and force_update:
                system_note += f" | [Force Update] Last Data: {last_date}"

            # 3. Check Duplicate Queue
            check_sql = "SELECT status FROM scrape_queue WHERE asin = ? AND status IN ('PENDING_APPROVAL', 'READY_TO_SCRAPE', 'PROCESSING')"
            existing = conn.execute(check_sql, [final_asin]).fetchone()
            if existing:
                return False, f"⚠️ Yêu cầu cho {final_asin} đang chờ xử lý (Trạng thái: {existing[0]})."

    except Exception as e:
        return False, f"Lỗi hệ thống: {e}"

    # Append User Note
    full_note = f"{system_note} | {note}" if note else system_note

    # Insert
    req_id = str(uuid.uuid4())
    sql = """
        INSERT INTO scrape_queue (request_id, asin, status, requested_by, note)
        VALUES (?, ?, 'PENDING_APPROVAL', ?, ?)
    """
    try:
        with duckdb.connect(db_path, read_only=False) as conn:
            conn.execute(sql, [req_id, final_asin, user_id, full_note])

        # Success Messages
        if is_unknown:
            return False, f"⚠️ Đã gửi yêu cầu cho {final_asin}. (Lưu ý: Không tìm thấy trong Product DB)."
        elif final_asin != asin_input:
            return True, f"✅ Đã tự động chuyển về ASIN Cha: {final_asin}. Yêu cầu đã được gửi!"
        else:
            return True, f"✅ Đã gửi yêu cầu thành công cho {final_asin}!"

    except Exception as e:
        return False, str(e)
