# RnD Scout - The Gatekeeper Engine 🚀

> **Advanced Amazon Market Intelligence System** utilizing **Apify** for parallel scraping, **DuckDB** for lightning-fast storage, and **Gemini 2.5 Flash** for hybrid AI analysis.

---

## 🛠️ System Overview

This repository houses the **Worker Engine** (The Gatekeeper). Its primary responsibility is managing the end-to-end data pipeline: **Scrape -> Ingest -> Mine -> Clean**.

### Key Components
- **manage.py**: The orchestrator. All commands must go through this CLI.
- **scout_app/database/scout.duckdb**: The primary analytical database.
- **core/miner.py**: Extracts raw aspects and sentiments from reviews.
- **core/normalizer.py**: Standardizes raw aspects using a "Double Shield" RAG strategy.

---

## 🚀 Operations Guide

### 1. Setup Environment
Create a `.env` file in the root directory:
```env
APIFY_TOKEN=...
GEMINI_API_KEY=...    # Main key for UI/Detective
GEMINI_MINER_KEY=...  # Dedicated worker key
GEMINI_JANITOR_KEY=...# Dedicated cleaning key
```

### 2. Scraping & Ingestion
- **Live Scrape**: Scrape 100 reviews and process AI immediately.
  ```bash
  uv run python manage.py run ASIN_HERE
  ```
- **Batch Pending**: Process ASINs from `asin_marked_status.csv`.
  ```bash
  uv run python manage.py pending --limit 5
  ```

### 3. AI Pipeline (Batch Mode - 90% Cost Saving)
The pipeline is designed to handle thousands of reviews efficiently. Follow these steps:

**Step A: Submit Mining**
```bash
uv run python manage.py batch-submit-miner
```
*Wait for status to be `SUCCEEDED` (check via `uv run python manage.py batch-status`).*

**Step B: Collect Miner & Submit Janitor**
```bash
# Collect raw tags into DB
uv run python manage.py batch-collect

# Submit unmapped raw tags for standardization
uv run python manage.py batch-submit-janitor
```

**Step C: Final Collection**
```bash
uv run python manage.py batch-collect
```

### 4. Maintenance
- **Reset Stalled Jobs**: If jobs are stuck in `QUEUED` status.
  ```bash
  uv run python manage.py reset
  ```
- **Cancel Cloud Jobs**:
  ```bash
  uv run python manage.py batch-cancel batches/job-id
  ```

---

## 🛡️ Security & Privacy
- Source files and `.env` are ignored by Git.
- Large batch result files are stored in `staging_data/` and archived in `archived_data/`.