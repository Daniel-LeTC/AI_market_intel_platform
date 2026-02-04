# TASK 02: Analyze Repo & UI Logic (Deep Dive)
- Target: `scout_app/` and `core/`
- Requirement: Nghiên cứu cấu trúc code thực tế để trích xuất tính năng cho bài thuyết trình.
    1.  **UI Logic:** Đọc `Market_Intelligence.py` và các file trong `ui/tabs/` để hiểu cách data chảy từ DB lên UI.
    2.  **Core Logic:** Check `detective.py` và `stats_engine.py` để hiểu cơ chế AI và tính toán Metric.
    3.  **Limitations:** Tìm các đoạn code xử lý "Sampling" hoặc "Wait time" để liệt kê vào phần Trade-offs.
- Result: Bản báo cáo phân tích chi tiết (Internal Report).

---

## 📋 BÁO CÁO PHÂN TÍCH HỆ THỐNG (INTERNAL REPORT)

### 1. Cơ chế Dữ liệu & Sampling (The Engine)
- **Scraping Strategy:** Sử dụng Apify Actor để cào Amazon. Giới hạn `maxPages=10` (khoảng 100-200 reviews/ASIN) để tối ưu chi phí và tốc độ.
- **Sampling Bias:** Do cào theo trang, dữ liệu thô bị lệch so với thực tế (ví dụ: Amazon có 90% 5-sao nhưng DB chỉ chứa mẫu 1-5 sao tương đương).
- **Extrapolation Logic (`stats_engine.py`):** Hệ thống tự động nhân ngược (scale) dữ liệu mẫu dựa trên `real_total_ratings` và `rating_distribution` thật từ Amazon. 
    - *Insight:* Khi demo, con số "Impact Score" là con số đã qua xử lý thuật toán, không phải đếm thô.

### 2. Market Intelligence UI (4 Tabs Logic)
- **Tab 1 (Executive):** Lấy data từ `products` table. Hiển thị "Product DNA" (Brand, Niche, Material) và "Priority Actions" (Top 3 Negative Aspects).
- **Tab 2 (X-Ray):** 
    - **Single Mode:** Phân tích Sentiment dựa trên `review_tags`.
    - **Mass Mode:** Heatmap so sánh nhiều sản phẩm. Có tính năng "Quick Jump" chuyển đổi ASIN qua session state.
- **Tab 3 (Showdown):** 
    - **Smart Match:** Tìm đối thủ cùng Niche, rating lệch +/- 30%.
    - **Proven Quality:** So sánh "Số lượng khách hài lòng thực tế". Đây là key selling point.
- **Tab 4 (Strategy Hub):** 
    - **Detective Agent:** Tích hợp Gemini 3.0. 
    - **Context Injection:** Tự động nạp Metadata sản phẩm vào prompt để AI không trả lời sai lệch.

### 3. Trade-offs & Giới hạn (Dành cho Slide)
- **Latency:** Request mới mất 5-10 phút (Scrape -> Ingest -> AI Tagging).
- **Sampling Depth:** Chỉ lấy 10 trang review mới nhất -> Phản ánh xu hướng hiện tại (Trend) tốt hơn là lịch sử lâu đời.
- **Data Accuracy:** ~85-95% tùy vào độ ổn định của Amazon HTML.