# System Architecture: Entry Points

## 1. User Interface (Streamlit)
- **Primary App**: `scout_app/Market_Intelligence.py`
    - *Port:* 8501
    - *Role:* Main Dashboard, Analytics, and AI Strategy.
- **Admin Console**: `scout_app/pages/99_Admin_Console.py`
    - *Role:* System Control, Pipeline Orchestration, Logs.
- **Feedback App**: `scout_app/feedback_app.py`
    - *Role:* Standalone feedback collector (decoupled from main app logic).

## 2. Background Worker (FastAPI)
- **Entry**: `worker_api.py`
- *Port:* 8000
- **Role:** Async Task Runner. Accepts HTTP triggers from UI/Admin.
- **Key Endpoints:**
    - `/trigger/scrape`: Amazon Deep Scrape.
    - `/trigger/miner` & `/janitor`: AI processing.
    - `/social/trigger`: Social Media Scrape.
    - `/admin/dedup/run`: Database Maintenance.

## 3. Operations CLI (`manage.py`)
- **Entry**: `python manage.py <command>`
- **Role:** Heavy-duty operations and Cloud Batch management.
- **Commands:**
    - `batch-submit-miner`: Uploads huge datasets to Google Batch.
    - `batch-collect`: Retrieves AI results.
    - `reset`: Unlocks stuck jobs in DB.
    - `run`: Manual execution of the full pipeline (Scrape -> Ingest -> AI).

## 4. Subprocess Workers
- **Scripts**: `scripts/worker_parent_asin.py`, `scripts/worker_product_details.py`.
- **Role:** Isolated execution units for unstable tasks (e.g., Headless Browsing). Called by `worker_api` via `subprocess`.
