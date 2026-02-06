# Code Deep Dive: `scout_app/core/ingest.py`

**Role:** The Data Ingestion Pipeline.
**Responsibility:** Loads data from external files (JSONL, XLSX) into the DuckDB database. It handles schema enforcement, data cleaning, and deployment safety (Blue-Green).

---

## 1. Class: `DataIngester`

### Initialization `__init__(self)`
- **Dependencies:** `scout_app.core.config.Settings`, `scout_app.core.metadata_parser.MetadataParser`.

---

## 2. Core Logic Functions

### `ingest_file(self, file_path: Path) -> Dict`
**Role:** Main Entry Point (Transactional).
- **Logic (Atomic):** "Blue-Green Deployment Strategy"
    1.  **Safety Check:** Gets `Settings.get_standby_db_path()` (e.g., if A is active, use B).
    2.  **Cloning:** Copies Active DB -> Standby DB (to preserve existing data).
    3.  **Schema Init:** Calls `_init_schema` on Standby DB.
    4.  **Format Handling:** Reads XLSX (Polars read_excel) or JSONL (Polars read_ndjson).
    5.  **Processing:** Calls `_ingest_products` (Metadata) and `_clean_dataframe` (Reviews).
    6.  **Swap:** Calls `Settings.swap_db()` ONLY if ingestion succeeds.
- **Returns:** Dict with stats (`total_rows`, `db_switched_to`).

### `_ingest_products(self, df, conn, category_hint=None)`
**Role:** Metadata Upsert & Enforcement.
- **Logic (Atomic):** "The Filial Son (Con báo hiếu)"
    1.  **Refinement:** Delegates to `MetadataParser.refine_metadata(df)` to standardize columns.
    2.  **Parent Upsert:** Inserts unique Parent ASINs into `product_parents`.
    3.  **Child Upsert:** Upserts Child ASINs into `products`.
    4.  **"Filial Son" Logic:**
        *   *Query:* `INSERT INTO products ... SELECT parent_asin FROM temp_p WHERE parent_asin != asin`
        *   *Purpose:* If a child refers to a parent that doesn't exist in `products`, create a placeholder parent record derived from the child's attributes (Brand, Niche). This prevents Foreign Key orphans.
    5.  **Niche Aggregation:** Updates `product_parents.niche` by aggregating niches from all children.

### `_clean_dataframe(self, df, filename)`
**Role:** Review Text Cleaning.
- **Logic:**
    - Renames columns (`reviewid` -> `review_id`).
    - Standardizes Dates (`September 10, 2024` -> `Date`).
    - Casts Ratings (`5.0 out of 5 stars` -> `5.0`).
- **Dependencies:** Polars (for high-performance transformations).

---

## 3. Schema Management

### `_init_schema(self, db_path)`
**Role:** DDL Execution.
- **Logic:** `CREATE TABLE IF NOT EXISTS` for:
    - `reviews`: Stores raw review text.
    - `products`: Stores ASIN metadata.
    - `review_tags`: Stores AI analysis results.
    - `product_stats`: Stores pre-calculated metrics.
    - `product_parents`: Stores Grouping logic.
    - `scrape_queue`: Stores user requests.
    - `aspect_mapping`: Stores canonical aspect names.

---

## 4. Helper Functions
- `_flatten_structs`: Flattens nested JSON structures in Polars (crucial for Apify JSONL).

---

## 5. Dependency Graph

### Calls
- **Polars**: High-performance DataFrame engine (faster than Pandas for IO).
- **DuckDB**: Storage engine.
- **MetadataParser**: `scout_app/core/metadata_parser.py` (for cleaning logic).
- **Settings**: Configuration management.

### Called By
- **Worker**: `worker_api.py` (Endpoint `/trigger/ingest`).
- **Scripts**: `workspace_task_16/ingest_to_db.py` (via import).
- **Tests**: `scripts/test_pipeline_flow.py`.
