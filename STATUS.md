# 🛠️ Technical Status & Context Map

**Last Updated:** Jan 23, 2026 (Production Live on GCP)

## [2026-01-23] Milestone: Production Deployment & Stabilization
- **Deployment Status:** LIVE on GCP (`34.87.30.120`).
- **Infrastructure:**
    - **Docker:** `docker-compose.prod.yml` (Artifact Registry images).
    - **CI/CD:** Manual scripts in `scripts/`.
        - `deploy_build.sh`: Build & Push to GCP Artifact Registry.
        - `deploy_remote.sh`: SCP config & Restart containers on VM.
        - `hot_patch_all.sh`: **Fast-track fix**. Injects code directly into running containers (UI & Worker) bypassing build time.
- **Critical Fixes:**
    - **UI Magic Error:** Fixed `DeltaGenerator` rendering issue in `Market_Intelligence.py`.
    - **UUID Error:** Fixed `NameError: uuid` by hot-patching `common.py` to sync with server.
    - **Worker API:** Added missing `/trigger/ingest` endpoint to `worker_api.py`.
    - **Config:** Optimized `.dockerignore` (Image size down to ~500MB).

## Current Branch: `ui-refactor`
**Status:** **STABLE & PROD-READY**

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
  *(Use this for quick logic fixes. Persistent changes must still be committed to Git).*

---

## 💾 Database State
- **Active:** `scout_a.duckdb` (Synced & Compacted).
- **Standby:** `scout_b.duckdb` (Synced & Compacted).

---

## ⏭️ Next Mission (Roadmap)
- **Immediate:** Verify Social Scout AI (Trend Bridge).
- **Module 4:** Social Scout AI Implementation.
