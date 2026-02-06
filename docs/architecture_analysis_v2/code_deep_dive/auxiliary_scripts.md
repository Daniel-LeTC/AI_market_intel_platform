# Code Deep Dive: Auxiliary Scripts

**Role:** The Maintenance & Quality Assurance Layer.
**Responsibility:** Data synchronization, AI verification, and one-off database fixes.

---

## 1. Synchronization Tools

### `db_source_of_truth_sync.py`
**Role:** The Ultimate Re-linker.
- **Problem:** Data from different scraping batches often has inconsistent Parent-Child relationships.
- **Logic (Atomic):**
    1.  **Multi-Source Ingestion:** Reads from Excel (RnD Manual Mapping), JSONL (Tumbler), and JSONL (Books).
    2.  **Parent Reconstruction:** Wipes `product_parents` and rebuilds it from the union of all sources.
    3.  **Relinking:** Performs a massive update on the `products` table to point every child to its verified Source-of-Truth Parent.
- **Why?** Ensures that the "Showdown" and "Strategy" tabs display accurate family-level data.

### `db_sync_parents.py` / `fix_parent_mapping.py`
- **Role:** Specialized variants of the sync logic, often used to bridge gaps between old V1 data and new V3 schema.

---

## 2. AI Audit & Verification

### `audit_detective.py`
**Role:** The Hallucination Detector.
- **Logic (Atomic):** 
    - Takes a sample ASIN.
    - Queries `review_tags` for extracted quotes.
    - Performs an `ILIKE` search in the `reviews` table to confirm if the quote actually exists.
- **Metrics:** Provides a "FOUND/NOT FOUND" status for every AI-extracted evidence.

### `test_detective_v2.py`
**Role:** Functional testing for the AI Agent.
- **Logic:** Simulates user queries and verifies that the `DetectiveAgent` can successfully call tools like `get_product_dna` and `search_review_evidence`.

---

## 3. Data Backfilling & Recovery

### `backfill_from_jsonl.py`
**Role:** Historical Data Recovery.
- **Logic:** Scans directories for raw JSONL files from Apify and re-runs the ingestion pipeline. Crucial for recovering data if a DB file is corrupted or accidentally deleted during maintenance.

---

## 4. Script Execution Model

All scripts are designed to be run from the project root via `uv`:
```bash
docker exec scout_worker uv run python scripts/<script_name>.py
```
They use `sys.path.append` to ensure they can import core modules from `scout_app/core/`.
