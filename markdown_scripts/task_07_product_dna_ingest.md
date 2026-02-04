# TASK 07: Product DNA Ingestion Improvement
- Target: `scout_app/core/ingest.py`
- Objective: Cải thiện quá trình Ingest để hỗ trợ nhập liệu "Product DNA" (Material, Niche, Target Audience, etc.) từ file nguồn do User cung cấp hoặc từ dữ liệu cào về.
- Constraint: **NO AI GUESSWORK**. Chỉ ingest đúng dữ liệu cứng có trong file đầu vào.
- Current Gap:
    - `DataIngester` hiện tại chỉ map các trường cơ bản (Title, Brand, Ratings).
    - Các trường DNA (Material, Niche, Audience...) trong bảng `products` chưa được map từ file nguồn.
- Input Source: User sẽ cung cấp list 10 ASINs kèm thông tin chi tiết (hoặc file cào về đã có cột này).

## ACTION PLAN
1.  **Schema Check:** Đảm bảo bảng `products` đã có đủ các cột: `material`, `main_niche`, `target_audience`, `design_type`, `size_capacity`, `product_line`, `num_pieces`.
2.  **Ingest Refactor:** Cập nhật hàm `_ingest_products` trong `scout_app/core/ingest.py` để map các cột này từ DataFrame (Polars) vào DuckDB.
    - Logic: Nếu file Excel/JSONL có cột `Material`, `Niche`... -> Insert vào DB.
    - Conflict: Nếu ASIN đã có, Update các trường này.

## EXPECTED MAPPING
| CSV/Excel Header | DB Column |
|---|---|
| Material / Fabric | `material` |
| Niche / Category | `main_niche` |
| Audience / Target | `target_audience` |
| Design / Style | `design_type` |
| Capacity / Size | `size_capacity` |
| Line / Series | `product_line` |
| Pieces / Count | `num_pieces` |

## NOTES
- User sẽ tự chịu trách nhiệm về độ chính xác của dữ liệu trong file upload.
