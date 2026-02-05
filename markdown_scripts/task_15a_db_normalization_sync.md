# TASK: 15a - Sync Normalized Aspects (Canonical) to DB
- **Status**: [DONE] ✅
- **Target Categories**: Tumbler, Comforter, Book
- **Objective**: Thêm cột `nom_aspect` vào DB và đồng bộ bộ từ điển chuẩn mới vào làm chuẩn thay thế cho Janitor.

## 1. Safety Measures
- **Snapshot**: Đã tạo bản lưu trữ `clean_manual/scout_a_final_sync_...duckdb`.
- **Archiving**: Đổi tên cột `standard_aspect` cũ thành `pre_nom_aspects`.

## 2. DB Schema Migration
- SQL: `ALTER TABLE aspect_mapping ADD COLUMN nom_aspect VARCHAR;`
- Data Sync: `python clean_manual/sync_to_db.py` (Đã nạp 21,546 dòng).
- Final Step: 
  - `standard_aspect` -> `pre_nom_aspects`
  - `nom_aspect` -> `standard_aspect` (The New Truth)

## 3. Post-Action
- [ ] Run `docker exec -it scout_worker python scripts/recalc_all_stats.py` (User Action).
