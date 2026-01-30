# TASK 08: Clean Ghost Parents Script
- Target: `clean_scripts/fix_ghost_parents.py`
- Objective: Tạo script Python (dùng Polars) để xử lý file Excel đầu vào, tự động tạo dòng dữ liệu cho các "Ghost Parents" (ASIN cha thiếu dòng định nghĩa).
- Context:
    - File Excel RnD hiện tại có 569 Parent ASINs không có dòng dữ liệu riêng.
    - Điều này khiến Metadata (Niche, Material...) của Parent bị NULL trong DB.
- Logic:
    1.  Load file Excel gốc.
    2.  Identify "Ghost Parents" (Parent có trong cột `Parent Asin` nhưng không có trong `ASIN`).
    3.  Với mỗi Ghost Parent:
        - Lọc ra tất cả dòng con (Children).
        - Chọn 1 dòng con đại diện (Ưu tiên bán chạy nhất hoặc Random).
        - Tạo một dòng mới: `ASIN` = Parent, `Parent Asin` = Parent.
        - Copy Metadata từ con sang cha (Title, Brand, Material, Niche, v.v.).
    4.  Merge dòng mới vào DataFrame gốc.
    5.  Export ra file mới `_fixed.xlsx`.

## DEPLOYMENT NOTE
- Thư mục `clean_scripts/` phải được add vào `.dockerignore` để không bị đẩy lên Production. Script này chỉ chạy local hoặc ad-hoc.
