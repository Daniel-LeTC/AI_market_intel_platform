# Code Deep Dive: Database Migrations

**Role:** The Evolution Layer.
**Responsibility:** Incremental updates to the DuckDB schema as new features (AI, Social, Requests) are added.

---

## 1. Evolution Timeline

### V1: The AI Foundation (`migration_v1.py`)
- **Action:** Adds `mining_status` to `reviews`.
- **Atomic Logic:** Implements a manual "ADD COLUMN IF NOT EXISTS" check using a try-except block since DuckDB SQL for `ALTER TABLE` is basic.
- **Impact:** Enabled the `AIMiner` to track its progress.

### V2: The Wallet System (`migration_v2.py`)
- **Action:** Creates the financial infrastructure in the Application DB (Note: This was later moved to `system.duckdb`).
- **Tables:** 
    - `users_budget`: Tracks `monthly_cap` and `current_spend`.
    - `scrape_transactions`: Atomic logs of every scrape event.
    - `social_case_studies`: Stores AI-analyzed social trends.
- **Bootstrap:** Automatically inserts default users (`admin`, `sếp`, `marketing_team`) with budgets.

### V3: Parent-Child Hierarchy (`migration_v3.py`)
- **Action:** Creates `product_parents`.
- **Purpose:** Decouples specific variations from the high-level product identity. Allows grouping "Blue Tumbler" and "Red Tumbler" under one parent.

### Gatekeeper Architecture (`migration_gatekeeper.py`)
- **Action:** Adds `scrape_queue`.
- **Logic:** Synchronizes both Blue and Green databases simultaneously to ensure structural parity during the swap.

### Social Isolation (`migration_social.py`)
- **Action:** Initializes isolated databases (`social_a.duckdb`, `social_b.duckdb`).
- **Tables:** `social_posts`, `social_comments`.
- **Design Pattern:** Isolation of concerns. Keeps high-volume social data away from the curated Amazon review data.

---

## 2. Key Design Patterns

### 1. Manual Idempotency
Because there is no migration engine, every script uses:
```python
try:
    conn.execute("CREATE TABLE ...")
except Exception as e:
    if "already exists" in str(e): pass # Skip
```
This allows scripts to be run multiple times safely.

### 2. Dual-Write (Blue-Green)
Migrations are often applied to both `DB_PATH_A` and `DB_PATH_B` in a single run to ensure that whichever DB is active after a swap will have the correct schema.

### 3. Isolation
Separating "System" data (Users, Queue) from "Application" data (Products, Reviews) and "Social" data. 
- `system.duckdb`: Meta-data about the app.
- `scout_a/b.duckdb`: The core product intelligence.
- `social_a/b.duckdb`: The high-volume social crawl data.
