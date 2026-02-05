# TASK: 14 - Janitor Training & Canonical Aspect Mapping
- **Status**: [DONE] ✅
- **Created**: 2026-02-05
- **Completed**: 2026-02-05
- **Objective**: Tạo bộ từ điển "Canonical Aspects" chuẩn cho từng Category để đồng bộ hóa Janitor (normalize.py).

## 1. Environment & State
- **Workspace**: `clean_manual/`
- **DB Path**: `/app/scout_app/database/scout_a.duckdb`
- **Snapshot**: `clean_manual/scout_a_final_sync_20260205.duckdb`

## 2. Execution Steps
### Step 1: Extraction & Refinement (DONE)
- Đã trích xuất và gom nhóm 1,316 aspects của Book, 488 của Tumbler, 139 của Comforter.
- Đã chạy 15 phiên bản Regex (V1-V15) để siết chặt các nhóm đặc thù (Bedding, Story, Technical).

### Step 2: Canonical Results
- **Tumbler**: 73 groups.
- **Comforter**: 32 groups.
- **Book**: 286 groups.

## 3. Results
- Bộ từ điển sạch sẽ đã sẵn sàng cho Janitor học tập.
