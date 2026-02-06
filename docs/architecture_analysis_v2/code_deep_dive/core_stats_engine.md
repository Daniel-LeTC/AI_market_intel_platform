# Code Deep Dive: `scout_app/core/stats_engine.py`

**Role:** The Statistical Calculation Engine.
**Responsibility:** Transforms raw data (`products`, `reviews`, `review_tags`) into analytical metrics (`kpis`, `sentiment`, `trends`). It serves as the "Commercial Logic" layer.

---

## 1. Class: `StatsEngine`

### Initialization `__init__(self, db_path=None)`
- **Dependency:** `scout_app.core.config.Settings`.
- **Logic:** Defaults to `Settings.get_active_db_path()` (supporting Blue-Green DBs) if no path is provided.
- **State:** Stores `self.db_path`.

---

## 2. Core Logic Functions

### `calculate_kpis(conn, asin)`
**Role:** Generates basic product health metrics.
- **Logic (Atomic):** "Dual-Source Fallback"
    1.  **Primary:** Reads metadata from `products` table (`real_total_ratings`, `rating_breakdown`).
    2.  **Fallback:** If `products` is empty or missing data, counts rows in `reviews` table (Local Count).
    3.  **Variations:** Checks `variation_count`. If 0, counts distinct `child_asin` in `reviews`.
    4.  **Neg%:** Calculates negative sentiment % from `rating_breakdown` (1+2 stars / total).
- **Dependencies:** `products` table, `reviews` table.
- **Returns:** `Dict` (total_reviews, avg_rating, total_variations, neg_pct).

### `calculate_sentiment_weighted(conn, asin)`
**Role:** Commercial Impact Analysis (The "Secret Sauce").
- **Logic (Atomic):** "Statistical Extrapolation"
    1.  **Population Source:** Reads `rating_breakdown` (e.g., {"5": 1000, "1": 100}) from `products`.
    2.  **Sample Source:** Calculates aspect mention rate per star in `reviews` + `review_tags`.
        *   *Formula:* `Rate(Aspect, Star) = Count(Aspect, Star) / Total_Reviews(Star)`
    3.  **Extrapolation:** Projects the sample rate onto the real population.
        *   *Formula:* `Est_Volume = Rate(Aspect, Star) * Real_Count(Star)`
- **Why?** Eliminates **Selection Bias** (e.g., scraping only top 100 reviews would otherwise hide problems prevalent in the total 5000 reviews).
- **Dependencies:** `review_tags`, `aspect_mapping` (for standardization).
- **Returns:** List of dicts (aspect, est_positive, est_negative, net_impact).

### `calculate_sentiment_raw(conn, asin)`
**Role:** Simple frequency count (Legacy/Debug).
- **Logic:** Direct SQL aggregation of `review_tags`.
- **Returns:** List of dicts.

### `calculate_rating_trend(conn, asin)`
**Role:** Time-series analysis.
- **Logic:** Aggregates `avg(rating_score)` by Month.
- **Returns:** List of dicts (month, avg_score).

---

## 3. Orchestration Functions

### `calculate_all(asin, conn=None)`
**Role:** Aggregator.
- **Logic:** Wraps all calculation functions (`kpis`, `sentiment`, `trend`) into a single Dict.
- **Call Graph:**
    - Calls: `_calculate_logic`.

### `save_to_db(asin, metrics_dict, conn=None)`
**Role:** Caching / Persistence.
- **Logic:** Serializes metrics to JSON and performs an `UPSERT` (Insert or Update) into `product_stats`.
- **Dependencies:** `product_stats` table.

### `calculate_and_save(asin, conn=None)`
**Role:** Batch Worker Entry Point.
- **Logic:** Orchestrates Calculation -> Save.
- **Call Graph:**
    - Called By: `worker_api.py` (via `run_recalc_task`).

---

## 4. Helper Functions
- `_query_df`: Wrapper for `conn.execute().df()`.
- `_query_one`: Wrapper for fetching single value.
- `_safe_float` / `_safe_int`: Robust casting to prevent crashes on dirty data.

---

## 5. Dependency Graph

### Calls
- **DuckDB**: Direct SQL execution.
- **Pandas**: DataFrame manipulation.
- **Settings**: DB Path configuration.

### Called By
- **UI**: `scout_app/ui/common.py` (via `get_precalc_stats` implicitly, though UI often re-implements parts of this logic for speed).
- **Worker**: `worker_api.py` (triggers `calculate_and_save`).
- **Detective**: `scout_app/core/detective.py` (fetches stats for AI context).
