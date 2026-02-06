# Code Deep Dive: UI Architecture (`Market_Intelligence.py` & `Tabs`)

**Role:** The Presentation Layer.
**Responsibility:** Providing an interactive interface for data exploration, request management, and AI-driven analysis. Built with **Streamlit**.

---

## 1. Global Entry Point: `Market_Intelligence.py`

### Key Logic & Atomic Flows

#### **State Management (`st.session_state`)**
Streamlit re-runs the entire script on every interaction. To maintain state, the app uses `session_state` for:
- `authenticated`: Login status.
- `main_asin_selector`: The currently active Parent ASIN across all tabs.
- `last_db_update`: Timestamp to force-refresh cached data when the DB changes.

#### **Sidebar Logic: "The Smart Explorer"**
1.  **Unified Metadata Fetch:** Calls `get_all_product_metadata()`. This is heavily cached to prevent DB thrashing.
2.  **Hierarchical Filtering:** 
    - Filters by **Category** (e.g., Tumbler).
    - Then by **Niche** (e.g., Travel).
    - Then by **Search Term** (Partial matches on Brand, Title, or Variation ASINs).
3.  **Redirection Logic:** When a user requests an ASIN that *already exists*, the app automatically identifies the Parent ASIN and updates `main_asin_selector` to redirect the user.

---

## 2. UI Utility Layer: `scout_app/ui/common.py`
**Role:** The Data Proxy.

### Atomic Logic terminal points
- **`query_df` / `query_one`**: Low-level DuckDB access wrappers with `read_only=True` for safety.
- **`get_weighted_sentiment_data`**: Implements the **Weighted Extrapolation Logic** directly in SQL using CTEs for high-speed UI rendering (as an alternative to the Python-based `StatsEngine`).
- **`request_new_asin`**: 
    - **Deduplication:** Checks if the ASIN is already in `scrape_queue` or `products`.
    - **Persistence:** Inserts into `scrape_queue` with a `PENDING_APPROVAL` status.

---

## 3. Modular Tabs (`scout_app/ui/tabs/`)

### `overview.py` (Executive Summary)
- **Logic:** Fetches `product_stats.metrics_json`. Renders "Pulse Metrics" (Avg Rating, Review Velocity, Negative %).
- **Visualization:** Uses `st.columns` for KPIs and Plotly for the Rating Distribution chart.

### `xray.py` (Customer Sentiment)
- **Logic:** Fetches raw and weighted sentiment lists.
- **Atomic Interaction:** Allows users to click on an aspect to see raw evidence quotes (Drill-down logic).

### `showdown.py` (Competitor Comparison)
- **Logic:** Compares two ASINs side-by-side. 
- **Feature:** "Smart Match" - Suggests the top competitor based on shared niches within the same category.

### `strategy.py` (AI Analyst)
- **Logic:** Wraps `DetectiveAgent`. 
- **UX:** Implements a chat history flow with "Quick Actions" (buttons that trigger specific agent tools).

---

## 4. Dependency Graph

### Calls
- **`ui/common.py`**: All data fetching.
- **`core/auth.py`**: User validation.
- **`core/detective.py`**: AI backend (only in Strategy tab).

### Side Effects
- **Session State**: Mutates `st.session_state` for navigation.
- **Database**: Writes to `scrape_queue` via `request_new_asin`.
