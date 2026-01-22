# 🛠️ Technical Status & Context Map

**Last Updated:** Jan 22, 2026 (Refactor Planning)
**Current Branch:** `fix_rating_distribution`
**Active Focus:** UI Refactoring & Blue-Green Fix.

---

## 🗺️ Critical File Map

### 1. Core Logic (Backend)
- **Ingest Engine:** `scout_app/core/ingest.py` (Stable).
- **Stats Engine:** `scout_app/core/stats_engine.py` (Stable).

### 2. User Interface (Streamlit)
- **Main App:** `scout_app/Market_Intelligence.py`
    - *Status:* **Functional but Bloated.** >800 lines. Using Pre-calc data.
    - *Issue:* Hard to maintain. Needs modularization.

### 3. Operational Issues
- **DB Locking:** Running `backfill_stats_v1.py` on the Active DB caused Streamlit to freeze.
    - *Fix Required:* Move backfill logic to use Blue-Green deployment (Write Standby -> Swap).

---

## 💾 Database Schema Snapshot

### Active Database: `scout_app/database/scout_a.duckdb`
- **`product_stats`:** Fully populated (10k+ records).

---

## ⏭️ Next Steps

1.  **Git Push:** Save current state (Logic works, Architecture needs cleanup).
2.  **Refactor UI:** Split `Market_Intelligence.py` into `scout_app/ui/tabs/*`.
3.  **Fix Backfill Script:** Implement Blue-Green logic.