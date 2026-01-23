# 🚀 Bright Scraper Tool - Backend & Infra

> **The Powerhouse of Amazon Market Intelligence.** 
> Utilizing **Apify** for deep scraping, **DuckDB** with Blue-Green architecture, and **Gemini 2.5 Flash Lite** for cost-effective mass sentiment mining.

---

## 🛠️ System Architecture

### 🛡️ Core Engines
- **`scout_app/core/ingest.py`**: Robust ingestion supporting multi-level ASINs, Nested JSONL, and Smart Upsert (COALESCE).
- **`scout_app/core/miner.py`**: AI Aspect Extraction with 3-layer protection (Locking, Deduplication, Penny Pincher Batch mode).
- **`scout_app/core/normalizer.py`**: Standardizes AI outputs using a RAG Shield to ensure data consistency.
- **`worker_api.py`**: FastAPI gateway for all background tasks (Scraping, Ingesting, Mining).

### 💾 Blue-Green Database Strategy
The system maintains two identical DuckDB files: `scout_a.duckdb` and `scout_b.duckdb`. 
- **Active:** Used by the UI for sub-second read operations.
- **Standby:** Targeted by the Worker for heavy write operations (Ingest/Mining).
- **Swap:** Automatic pointer switch occurs after every successful ingestion.

---

## 🚀 Operations & Deployment

### 🐳 Running with Docker
```bash
docker compose up -d
```
- **UI Dashboard**: `http://localhost:8501`
- **Worker API**: `http://localhost:8000`

### 📟 CLI Orchestration (`manage.py`)
Used for manual maintenance or batch jobs:
- **Reset Stuck Jobs**: `python manage.py reset`
- **Batch Submit Miner**: `python manage.py batch-submit-miner`
- **Collect Results**: `python manage.py batch-collect`

---

## 🛡️ Admin Console Guide
Access the **Admin Console** (Page 99) in the sidebar to control the engine:

1. **User Requests**: Approve or reject ASINs requested by the team.
2. **Scrape Room**: Hot-plug ASINs for immediate deep scraping.
3. **Staging Area**: Inspect raw `.xlsx` or `.jsonl` files and trigger "Safe Ingest" to DB.
4. **AI Ops**: Trigger Live Mining or Janitor (Cleaning) tasks.
5. **Terminal**: Run maintenance commands (Vacuum, du, ls) directly on the Active DB.

---

## 🔐 Environment Configuration
Create a `.env` file with:
```env
APIFY_TOKEN=...
GEMINI_API_KEY=...    # For UI Detective (Gemini 3 Flash)
GEMINI_MINER_KEY=...  # For Backend Miner (Gemini 2.5 Flash Lite)
GEMINI_JANITOR_KEY=...# For Backend Janitor (Gemini 2.5 Flash Lite)
ADMIN_PASSWORD=...
```
