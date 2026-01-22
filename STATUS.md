# 🛠️ Technical Status & Context Map

**Last Updated:** Jan 22, 2026
**Current Branch:** `fix_rating_distribution`
**Status:** **PERFORMANCE SOLVED (st.fragment)**

---

## 🗺️ Critical File Map

### 1. UI Components (Optimized)
- `scout_app/Market_Intelligence.py`: Main Orchestrator.
- `scout_app/ui/tabs/*.py`: ALL Tabs are now wrapped with `@st.fragment`.
    - **Outcome:** Interactions inside a tab (Toggle, Chat, Select) ONLY re-run that specific tab. Global app reload is eliminated for local actions.
- `scout_app/ui/common.py`:
    - `query_df`: Wrapped with `time_it` (debug).
    - `get_precalc_stats`: Aggressively cached + Fallback logic (Child -> Parent ASIN).

### 2. Core Logic
- `scout_app/core/stats_engine.py`: JSON-based pre-calculation.

---

## 📝 Session Log (The Performance Battle)

1.  **Issue:** UI Latency 3-4s per interaction.
    - *Root Cause 1:* Streamlit Full Rerun for every interaction (Chart toggle re-runs heavy SQL queries).
    - *Root Cause 2:* Child ASINs causing Cache Miss (Live Query Fallback).
2.  **Fixes Implemented:**
    - **`@st.fragment`:** Applied to all Tabs. Isolates execution scope.
    - **Lazy Loading:** Evidence quotes put into Expander (safe now with Fragment).
    - **Parent Lookup:** Fixed Cache Miss logic in `common.py`.
    - **UX:** Disabled Chat Input while AI is thinking.

---

## ⏭️ Next Priority
- **Social Scout AI:** Trend Bridge Implementation.