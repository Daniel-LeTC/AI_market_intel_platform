# TASK: 16 - Product Metadata Ingestion (1500 ASINs)
- **Status**: [IN-PROGRESS] 🚧
- **Created**: 2026-02-05
- **Objective**: Ingest metadata cho khoảng 1500 ASINs (từ Parquet 3 tháng cuối 2025) vào bảng `products` và làm giàu dữ liệu Rating Breakdown.

## 1. Context & Constraints
- **DB Path**: `/app/scout_app/database/scout_a.duckdb`
- **Source Data**: Silver Parquet files from `perf_analysis_assistant` (2025/10, 11, 12).
- **Key Columns**: `ASIN`, `Main niche`, `Product Type`.
- **Logic Constraints**:
  - Không fallback dữ liệu ảo. Rỗng là rỗng.
  - Không chạm vào logic core của `StatsEngine`.
  - Phải tuân thủ quy trình: **Tìm Parent -> Nạp Parent -> Nạp Child -> Scrape Rating Breakdown**.

## 2. Tools & Scripts Mapping
- **Finding Parent**: `scripts/worker_parent_asin.py` (Lấy quan hệ Cha-Con).
- **Getting Metadata**: Parquet (Có sẵn Title/Brand/Niche - Skip `worker_product_details.py` cho đám Child này để tiết kiệm).
- **Getting Rating Breakdown**: `scripts/worker_api.py` (Review Scraper mode).
  - *Strategy*: Scrape limit 1 review/ASIN.
  - *Goal*: Lấy `reviewSummary` (5-star distribution) từ API trả về để update cột `rating_breakdown`.

## 3. Execution Plan (Refined - "Self-Parenting" Strategy)

### Step 1: Data Extraction (DONE)

- Script: `workspace_task_16/extract_parquet_metadata.py`.

- Output: `workspace_task_16/raw_metadata_from_parquet.csv` (1,380 ASINs).

- Flag: `verification_status` = 'TEMP_ORPHAN', `parent_asin` = `asin`.



### Step 2: Bootstrap Ingestion (After Recalc)

- Nạp data từ CSV vào `product_parents` và `products`.

- Mục tiêu: Giữ chân ASIN trong hệ thống với Metadata cơ bản từ Parquet.



### Step 3: Metadata Enrichment (The "1-Review Trick")

- Chạy `worker_api.py` (Review Scraper) cho 1,380 ASIN này.

- Config: `max_reviews=1`.

- Goal: Lấy `reviewSummary` để update `rating_breakdown`.



## 4. Progress Log



| Date | Action | Result |



| --- | --- | --- |



| 2026-02-05 | Created Task 16 | Task Initialized |



| 2026-02-05 | Logic Analysis | Defined role of 3 workers & The 1-Review Trick |



| 2026-02-05 | Data Extraction | 1380 ASINs ready with 'TEMP_ORPHAN' flag |



| 2026-02-05 | Batch 1 (100) | ✅ COMPLETED. Metadata & Breakdown for 100 ASINs ingested. |



| 2026-02-05 | Current State | 🛑 PAUSED. 1,279 ASINs remaining in CSV list. |




