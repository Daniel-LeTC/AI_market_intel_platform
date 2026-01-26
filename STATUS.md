# 🛠️ Technical Status & Context Map

**Last Updated:** Jan 26, 2026 (Dev Session)

## [2026-01-26] Feature: Showdown Tab Refinement
- **Logic Overhaul:**
    - Replaced "Satisfaction %" comparison with "Weighted Win" (Estimated Positive Population).
    - **Reason:** Small sample sizes (e.g., 100% of 1 review) were beating proven quality (90% of 100 reviews).
    - **New Metric:** `est_positive = (Positive Mentions / Sample Size) * Real Population`.
- **Tie-Breaker:** Added 10% margin threshold. If `abs(A - B) < 10% of Max`, result is **Tie**.
- **Battle Matrix Filter:** Only compares aspects where **BOTH** sides have `est_positive > 0`. Removes noise from one-sided features.
- **UI:** Updated column names to "Khách khen (Est)" and added visual progress bars.

## [2026-01-23] Milestone: Production Deployment & Stabilization
- **Deployment Status:** LIVE on GCP (`34.87.30.120`).
- **Infrastructure:**
    - **Docker:** `docker-compose.prod.yml` (Artifact Registry images).
    - **CI/CD:** Manual scripts in `scripts/`.
- **Critical Fixes:**
    - **UI Magic Error:** Fixed `DeltaGenerator` rendering issue.
    - **UUID Error:** Fixed `NameError: uuid` in common.py.

## Current Branch: `ui-refactor`
**Status:** **ACTIVE DEV**

---

## 📂 System Architecture (GCP Production)

### 1. Components
- **Scout UI (`scout_ui_prod`):** Streamlit App (Port 8501).
- **Worker (`scout_worker_prod`):** FastAPI Background Tasks (Port 8000).
- **Database:** DuckDB (Volume Mounted from Host: `~/bright-scraper/scout_app/database`).

### 2. Operational Workflows
- **Deploy New Version:**
  ```bash
  ./scripts/deploy_build.sh && ./scripts/deploy_remote.sh
  ```
- **Hot Fix (Code Only):**
  ```bash
  ./scripts/hot_patch_all.sh
  ```

---

## 💾 Database State
- **Active:** `scout_b.duckdb` (Primary for Dev).
- **Standby:** `scout_a.duckdb`.

---

## ⏭️ Next Mission (Roadmap)
- **Module 4:** Social Scout AI Implementation (Trend Bridge).
- **UI Polish:** Heatmap Revival in Strategy Tab.