# Repository Status & Refactor Plan

## 1. Thông tin chung
- **Repository:** `bright_scraper_tool`
- **Branch hiện tại:** `refactor-db-agent`
- **Mục tiêu:** Hoàn thiện việc refactor DB Agent, ổn định hệ thống hot-patch và chuẩn bị merge vào branch `ui-refactor`.

## 2. Đánh giá tình hình hiện tại
Hệ thống đang trong trạng thái "lai" giữa việc phát triển tính năng mới và vá lỗi trực tiếp trên production.
- **Database:** Đang dùng cơ chế switch DB qua file `scout_app/database/current_db.txt` (Hiện tại là `A`).
- **Deployment:** Phụ thuộc vào script `hot_patch_all.sh` để đẩy code trực tiếp vào Docker containers.
- **Tính năng mới:** Đang thêm trang `98_Feedback_Loop.py` để ghi nhận phản hồi.

## 3. Danh sách File Code thực sự đang sử dụng (Core Files)
Dựa trên script vận hành và cấu trúc app, đây là các file quan trọng nhất:

### UI & Pages (Streamlit)
- `scout_app/Market_Intelligence.py`: Entry point của giao diện chính.
- `scout_app/ui/common.py`: Các thành phần giao diện dùng chung.
- `scout_app/ui/tabs/xray.py`: Logic hiển thị chi tiết sản phẩm.
- `scout_app/ui/tabs/showdown.py`: Logic so sánh đối đầu.
- `scout_app/pages/05_Social_Scout.py`: Tính năng tìm kiếm mạng xã hội.
- `scout_app/pages/98_Feedback_Loop.py`: (Mới) Hệ thống feedback loop.

### Core Logic & Backend
- `scout_app/core/detective.py`: Module phân tích và audit dữ liệu.
- `scout_app/core/ingest.py`: Xử lý nạp dữ liệu vào DuckDB.
- `worker_api.py`: API service cho các tác vụ nền (Worker).
- `scout_app/database/current_db.txt`: File cấu hình database active.

### Scripts & DevOps
- `scripts/hot_patch_all.sh`: Script đồng bộ code lên production.
- `scripts/seed_users.py`: Quản lý tài khoản người dùng.
- `pyproject.toml`: Quản lý dependencies qua `uv`.

## 4. Kế hoạch hành động chi tiết (Refactor Stable)
| Bước | Công việc | Chi tiết | Trạng thái |
|:---:|:---|:---|:---:|
| **1** | **Sidebar UX** | Hiển thị Brand + Title + ASIN để user dễ chọn sản phẩm | **Completed** |
| **2** | **Aspect Alignment** | Đồng bộ logic mapping giữa X-Ray, Evidence và AI Chatbot | **Completed** |
| **3** | **Detective Agent Fix** | Sửa Prompt, fix Tool Calling logic và lỗi Context | **Completed** |
| **4** | **Data Consistency** | Kiểm tra và fix lỗi lệch dữ liệu giữa biểu đồ và bảng chứng cứ | **Completed** |
| **5** | **Sidebar 2.0** | Phân tầng lọc: Category -> Niche -> Search -> ASIN List | **Completed** |
| **6** | **Mass Mode Fix** | Sửa lỗi bộ lọc Category/Niche trong trang X-Ray thị trường | **Completed** |
| **7** | **Bug Fix (Hot)** | Sửa lỗi crash `.contains()` và trùng lặp dữ liệu sidebar | **Completed** |
| **8** | **Mass Mode Crash Fix** | Sửa lỗi `StreamlitAPIException` khi default value không nằm trong bộ lọc | **Completed** |
| **13** | **Dynamic Niche UI** | Hiển thị "Niche (Theme)" trong bảng biến thể và lọc Niche thông minh | **Completed** |
| **14** | **Review Parent Correction** | Đính chính quan hệ Cha-Con cho Review dựa trên SSOT Excel (né lỗi Scraper ngu) | **Pending** |
| **15** | **Final Population Audit** | Đưa quân số về chuẩn: 902 Comforter, 43 Tumbler, 108 Book | **Pending** |

## 5. Nhật ký thay đổi (Change Log)
- [x] Đã backup Database vật lý (`.bak_refactor`).
- [x] Nâng cấp Sidebar hiển thị đầy đủ thông tin sản phẩm.
- [x] Đồng bộ hóa logic Aspect Mapping trên toàn hệ thống (UI & AI).
- [x] Sửa lỗi AI Chatbot context và tool calling logic.
- [x] Tái cấu trúc Sidebar thành bộ lọc thông minh (Category/Niche/Search).
- [x] Sửa lỗi bộ lọc Mass Mode và lỗi crash Multiselect.
- [x] Fix lỗi AttributeError và trùng lặp ASIN trong Sidebar.
- [x] Phẫu thuật dữ liệu: Chuẩn hóa Category và sửa lỗi typo (tumber -> tumbler).
- [x] Cứu dữ liệu Comforter: Nạp thành công 10,000+ metadata xịn từ Excel vào DB A & B.
- [x] Triển khai Niche Aggregation: Một Parent ASIN giờ đây chứa đầy đủ danh sách các chủ đề thiết kế.
- [x] Nâng cấp bảng Variations: Thay cột Pack bằng cột Niche để đối ứng chính xác từng mẫu mã.
- [x] Gắn nhãn trạng thái xác thực (`GOLDEN`, `RECOVERED`) để quản trị dữ liệu.
- [x] Làm đẹp dữ liệu Brand: Xóa bỏ các tiền tố "Visit the", "Store", "by (Author)" thừa thãi.
- [ ] (Sắp làm) Đại tu Ingester: Chuyển sang logic Lookup Cha từ Con để khắc phục lỗi Scraper tự tiện gán mã Request làm Parent.



## 6. Ghi chú về Schema Dữ liệu chuẩn (Golden Schema)
- **Category:** Nhóm sản phẩm lớn (`comforter`, `tumbler`, `book`).
- **Main Niche:** Chủ đề/Ngách sản phẩm (Ví dụ: `Rainbow`, `Game`, `Doodle`).
- **Source of Truth:** 
    - Comforter: Lấy từ file `./Kid Comforter Set_Thoai RnD_19-12-2025.xlsx`.
    - Book/Tumbler: Lấy từ `staging_data_local/**/new_product_metadata/*.jsonl`.
