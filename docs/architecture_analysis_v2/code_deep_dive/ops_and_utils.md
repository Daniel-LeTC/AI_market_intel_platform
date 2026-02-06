# Code Deep Dive: Operations & Utilities

**Role:** The Support Infrastructure.
**Responsibility:** Authentication, Cloud Batch Integration, CLI Management, and Pricing Logic.

---

## 1. Batch Processing Engine

### `AIBatchHandler` (`scout_app/core/ai_batch.py`)
**Role:** The Google Cloud Bridge.
- **Problem:** Running AI on 10,000 reviews synchronously is slow and expensive.
- **Solution:** Uses Google Gemini Batch API (Async) for 50% cost reduction.
- **Atomic Logic:**
    1.  **Upload:** Streams JSONL to Google Storage.
    2.  **Submit:** Triggers a Batch Job.
    3.  **Poll & Download:** Checks status and retrieves results once `SUCCEEDED`.

### `manage.py` (CLI)
**Role:** The Operations Commander.
- **Capabilities:**
    - `batch-submit-miner`: Orchestrates the flow from `AIMiner.prepare_batch_file` -> `AIBatchHandler.submit`.
    - `batch-collect`: Automates the retrieval and ingestion of completed jobs.
    - `reset`: "Unlocks" reviews stuck in `QUEUED` state (due to worker crashes) back to `PENDING`.

---

## 2. Security & Identity

### `AuthManager` (`scout_app/core/auth.py`)
**Role:** Gatekeeper of User Identity.
- **Logic:**
    - **Hashing:** Uses `bcrypt` for password verification (Secure).
    - **Storage:** Reads from `system.duckdb` (Isolated from app data).
    - **Session:** Returns a User Dict `{role, budget}` used by Streamlit `session_state`.

---

## 3. Business Logic Helpers

### `SocialPricing` (`scout_app/core/social_pricing.py`)
**Role:** Pricing Configuration.
- **Logic:** Defines unit costs (e.g., $0.30/1k TikTok posts) and base fees.
- **Usage:** Used by `SocialScraper` and UI to display cost estimates before execution.

### `config.py` (`scout_app/core/config.py`)
**Role:** Central Configuration.
- **Logic:**
    - **Blue-Green Pathing:** Dynamically determines `ACTIVE_DB` vs `STANDBY_DB`.
    - **Environment Variables:** Loads API Keys and settings from `.env`.

### `Logger` (`scout_app/core/logger.py`)
**Role:** High-Performance Audit Logging.
- **Atomic Logic:**
    - **Format:** JSON Lines (JSONL).
    - **Strategy:** Daily Rotation (`log_2026-02-06.jsonl`).
    - **Performance:** Append-only mode (`"a"`), minimizing I/O blocking. Ideally suited for log shippers like Filebeat.
