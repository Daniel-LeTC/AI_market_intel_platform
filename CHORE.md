# 🧹 Infrastructure Audit & Cleanup (Jan 23, 2026)

## 🏗️ Core Pipelines Detail (One-by-One)

### 1. `scout_app/core/ingest.py`
- **Purpose:** Nạp dữ liệu từ file Excel/JSONL vào DuckDB (Active/Standby).
- **Findings:**
    - ✅ **Strengths:** Có cơ chế Blue-Green Swap xịn, tự động trigger StatsEngine.
    - 🔴 **Weaknesses:**
        - Chỉ `INSERT` dòng cho `parent_asin`, bỏ qua `child_asin` -> Gây hiện tượng bảng `products` thiếu biến thể.
        - Mapping metadata lỏng lẻo, dễ bị đè dữ liệu rác (NULL) lên dữ liệu xịn nếu file input thiếu cột.
        - Không có bước `VACUUM` sau khi ingest -> Gây phình DB (vừa fix bằng tay xong).
- **Status:** **CRITICAL REFACTOR REQUIRED**
- **Action:** Sửa logic `_ingest_products` để hỗ trợ đa cấp ASIN.

### 2. `worker_api.py`
- **Purpose:** FastAPI backend xử lý các task background (Miner, Scraper, Janitor).
- **Findings:**
    - ✅ **Strengths:** Cấu trúc tốt, dùng `BackgroundTasks` để không block API. Đã tích hợp Social Module.
    - 🔴 **Weaknesses:**
        - API `/trigger/ingest` bị hardcode chỉ nhận file trong `staging_data`, gây khó khăn khi nạp batch cũ.
        - Thiếu API để theo dõi Progress của các task đang chạy (chỉ thấy trong log).
        - Endpoint `/admin/exec_cmd` có whitelist nhưng vẫn là tiềm ẩn rủi ro nếu mở Public.
- **Status:** **STABLE BUT NEEDS POLISH**
- **Action:** Mở rộng đường dẫn cho Ingest và thêm cơ chế báo cáo Progress.

### 3. `scout_app/core/miner.py`
- **Purpose:** Trích xuất Aspect/Sentiment từ review bằng AI (Gemini).
- **Findings:**
    - ✅ **Strengths:** Hỗ trợ cả Live (real-time) và Batch (tiết kiệm token cho data lớn). Xử lý tốt JSONL format của Google.
    - 🔴 **Weaknesses:**
        - **DUPLICATION BUG:** Không có check trùng khi lưu tag. Chạy Miner nhiều lần trên 1 review sẽ làm nhân đôi/ba số liệu thống kê.
        - Phụ thuộc vào `parent_asin` có sẵn trong bảng `reviews`.
- **Status:** **STABLE BUT REQUIRES DATA INTEGRITY FIX**.
- **Action:** Thêm cơ chế `INSERT OR IGNORE` hoặc xóa tag cũ trước khi Miner chạy lại.

### 4. `scout_app/core/normalizer.py`
- **Purpose:** Chuẩn hóa (Normalize) các aspect rác về Standard Terms.
- **Findings:**
    - ✅ **Strengths:** Thiết kế **RAG Shield** cực tốt, ép AI dùng lại từ vựng cũ để đảm bảo tính nhất quán của Dashboard.
    - ✅ **Logic:** Loại bỏ tính từ, gom nhóm đồng nghĩa tốt.
    - 🔴 **Weaknesses:** Chưa tự động hóa hoàn toàn (vẫn phải trigger bằng tay).
- **Status:** **HEALTHY**.
- **Action:** Tích hợp vào Pipeline tự động sau Miner.

### 6. `manage.py`
- **Purpose:** CLI Orchestrator (Tổng quản điều phối luồng Scrape -> Ingest -> AI).
- **Findings:**
    - ✅ **Strengths:** Tích hợp tốt các module core. Có lệnh `batch-collect` và `batch-status` rất hữu ích.
    - 🔴 **Weaknesses:**
        - **BLUE-GREEN DESYNC:** Khi chạy Ingest từ CLI, nó thực hiện Swap DB. Nếu UI đang chạy, UI có thể bị mất kết nối hoặc nhìn thấy data cũ cho đến khi restart.
        - Phụ thuộc vào file `asin_marked_status.csv` (Legacy tracking). Nên chuyển sang DB tracking hoàn toàn.
- **Status:** **STABLE BUT NEEDS SYNC LOGIC**.
- **Action:** Quy hoạch các lệnh này vào Admin UI để đồng bộ hóa hoàn toàn với Streamlit Session.

---

## 🗑️ Script Directory Audit (`scripts/`) - Detail by Group

### Group: Migrations (Move to `archived/legacy_scripts/migrations/`)
- `migration_add_metadata_v3.py`: Thêm cột metadata. (Done)
- `migration_create_stats_table.py`: Tạo bảng stats. (Done)

### Group: One-off Fixes (Move to `archived/legacy_scripts/one_off/`)
- `backfill_brands_v5.py`: Fix brand cha. (Done)
- `backfill_brands_from_excel_v6.py`: Fix brand từ Excel. (Done)
- `fix_missing_parents_v7.py`: Tạo dòng cha. (Done)
- `fix_variation_counts.py`: Fix số biến thể. (Done)
- `ingest_historical_batches.py`: Nạp data cũ. (Done)

### Group: Debug & Research (Move to `archived/legacy_scripts/debug/`)
- `check_detective_bug.py`: Tìm lỗi AI.
- `check_normalization_result.py`: Soi janitor.
- `supermetrics_puller.py`: Research cũ.
- `test_detective_tool.py`: Test lẻ AI.
- `test_social_dry_run*.py`: Test TikTok/Meta.

### Group: Essential Maintenance (KEEP in `scripts/`)
- `recalc_all_stats.py`: Công cụ bảo trì stats.
- `test_detective_v2.py`: Stress test AI chính thức.
- `test_stats_engine.py`: Test logic tính toán.
- `seed_users.py`: Khởi tạo hệ thống.

### 5. `scout_app/core/batch_processor.py`
- **Purpose:** (LEGACY) Điều phối Batch Job cho AI Miner.
- **Findings:**
    - 🔴 **DUPLICATED LOGIC:** Chức năng giống hệt `miner.py` nhưng dùng code cũ hơn.
    - 🔴 **HARDCODED PATHS:** Trỏ vào `scout.duckdb` (Legacy), không hỗ trợ Blue-Green. Sẽ gây mất data nếu dùng nhầm.
- **Status:** **DEPRECATED / TO BE REMOVED**.
- **Action:** Chuyển các tính năng CLI xịn (submit, download) sang `miner.py` hoặc `manage.py`, sau đó dọn dẹp file này.