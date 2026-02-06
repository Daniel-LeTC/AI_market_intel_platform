# Code Deep Dive: Admin Console & Feedback Loop

**Role:** Control Plane & Quality Assurance.
**Responsibility:** Providing the tools to manage the end-to-end data pipeline and capturing user feedback for iterative improvements.

---

## 1. Gatekeeper Control Center (`99_Admin_Console.py`)
**Role:** The Command & Control (C2) interface for the system.

### Key Logic & Atomic Flows

#### **Pipeline Intelligence (`get_pipeline_stats`)**
- **Debt Detection (Atomic):** Queries `review_tags` vs `aspect_mapping` to count unique unstandardized aspects. This tells the Admin if the "Janitor" needs to run.
- **Update Detection:** Compares `reviews.ingested_at` with `product_stats.last_updated`. If reviews are newer, the ASIN is added to the "Recalc Queue".

#### **ASIN Request Management**
- **Workflow:** `PENDING_APPROVAL` (User Request) -> `READY_TO_SCRAPE` (Admin Approval) -> `IN_PROGRESS` (Dispatched to Worker).
- **Atomic Tooling:** The **Parent Finder** button launches a Playwright subprocess to resolve Parent ASINs before actual scraping starts.

#### **Remote Command Terminal**
- **Logic:** Wraps the `/admin/exec_cmd` worker endpoint.
- **Capability:** Allows executing `python manage.py` commands (Batch submissions, DB resets) directly from the UI without SSH access to the server.

#### **Maintenance Dashboard**
- **Deduplication:** Triggers the "Smart Tag Dedup" logic in the worker.
- **Compaction:** Forces a DuckDB `CHECKPOINT` and `VACUUM` to reclaim disk space from deleted rows (crucial for DuckDB performance).

---

## 2. Feedback Loop (`98_Feedback_Loop.py` & `feedback_app.py`)
**Role:** Collecting User Insights.

### Key Logic & Atomic Flows

#### **System DB Integration**
- **Logic:** Unlike product data which lives in `scout_a/b.duckdb`, feedback is stored in `system.duckdb`.
- **Purpose:** Ensures feedback is preserved even if the application database is reset or swapped.

#### **Data Structure (`user_feedback` table)**
- `user_identity`: Trace who provided the feedback.
- `rating`: 1-5 star satisfaction score.
- `feature_request` / `bug_report`: Categorized text fields for AI analysis of feedback.

---

## 3. Dependency Graph

### Upstream
- **User (Admin)** -> `99_Admin_Console.py`
- **User (Standard)** -> `98_Feedback_Loop.py`

### Downstream
- **Worker API** (`worker_api.py`) -> For all heavy tasks.
- **System DB** (`system.duckdb`) -> For feedback and request queue.
- **Application DB** (`scout_a.duckdb`) -> For pipeline stats and data modification.

### Side Effects
- **File System:** Deletes files in `staging_data/` via UI buttons.
- **DB Mutations:** Changes status of `scrape_queue`, updates `product_parents`.
