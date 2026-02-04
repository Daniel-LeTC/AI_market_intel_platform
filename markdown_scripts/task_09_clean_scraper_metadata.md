# TASK 09: Clean Scraper Metadata Script
- Target: `clean_scripts/clean_scraper_metadata.py`
- Objective: Chuyển đổi file Raw Scraper (dạng Flatten JSON với `productDetails/X`) thành file chuẩn Ingest (có cột `Material`, `Main Niche`, v.v.).
- Input: `dataset_amazon-product-details-scraper_2026-01-28_09-03-46-099.xlsx`
- Logic:
    1.  Load file Excel.
    2.  Iterate qua từng dòng.
    3.  Loop qua các cột `productDetails/0/name`, `productDetails/1/name`... để tìm các Key quan trọng (Material, Fabric, Style, Target...).
    4.  Extract Value tương ứng vào cột mới (`Material`, `Design Type`...).
    5.  Map các cột cơ bản: `productRating` -> `Reviews: Rating`, `countReview` -> `Reviews: Review Count`.
    6.  Save ra file `_cleaned.xlsx`.

## MAPPING DICTIONARY (Dynamic)
- "Material" / "Fabric Type" -> `Material`
- "Style" / "Pattern" -> `Design Type`
- "Target Audience" / "Department" -> `Target Audience`
- "Size" -> `Size/Capacity`
- "Included Components" -> `Number of Pieces` (Infer from count)
