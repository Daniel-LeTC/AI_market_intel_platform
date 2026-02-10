# SYSTEM NODES DECOMPOSITION (ALIGNED WITH AI BU STRATEGY)

## 🎯 Mục tiêu
Phân rã "Bright Scraper Platform" thành các đơn vị cơ bản (Atomic Nodes) để:
1. Xác định chính xác giá trị (Time saved / Accuracy gain) cho từng bước.
2. Tái sử dụng các node cho các workflow khác (Social Scout, Media Prompt).
3. Thu thập feedback của user theo từng node thao tác.

---

## 🏗️ Layer 1: Acquisition Nodes (Thu thập dữ liệu)
*Các node xử lý việc lấy dữ liệu thô từ môi trường ngoài.*

| Node ID | Chức năng | Input | Output | Automation Level |
| :--- | :--- | :--- | :--- | :--- |
| **ACQ-01** | **ASIN Discovery** | Niche/Category | List of Target ASINs | Manual/Semi-Auto |
| **ACQ-02** | **Metadata Scraper** | ASIN | Product DNA (Title, Brand, Specs) | 100% Auto |
| **ACQ-03** | **Review Scraper** | ASIN + Filter | Raw Review Data (Text, Date, Rating) | 100% Auto |
| **ACQ-04** | **Social Linker** | ASIN | TikTok/Meta URLs | 50% Auto (W.I.P) |

---

## 🧠 Layer 2: Intelligence Nodes (Phân tích & Xử lý)
*Các node chuyển hóa dữ liệu thô thành insight.*

| Node ID | Chức năng | Logic | Impact (Con số) | AI Role |
| :--- | :--- | :--- | :--- | :--- |
| **INT-01** | **Tag Miner** | Trích xuất Aspect/Sentiment từ text | Giảm 95% thời gian đọc review | Gemini 2.5/3.0 |
| **INT-02** | **Janitor/Normalizer** | Quy chuẩn hóa Aspect (Standardization) | Tăng 80% độ chính xác của biểu đồ | RAG + Dict Mapping |
| **INT-03** | **Stats Calculator** | Tính Weighted Impact Score | Cung cấp Source of Truth | Math Engine |
| **INT-04** | **Detective Summary** | Tóm tắt Pain Points/SWOT | Thay thế 100% việc viết report tay | Agentic AI |

---

## 📢 Layer 3: Distribution Nodes (Phân phối Insight)
*Các node đưa kết quả đến đúng người, đúng thời điểm.*

| Node ID | Chức năng | Phương thức | Target User | Chế độ |
| :--- | :--- | :--- | :--- | :--- |
| **DIS-01** | **Interactive Chat** | Streamlit UI | Toàn bộ BU | On-demand |
| **DIS-02** | **Weekly Mailer** | SendGrid / SMTP | R&D, Management | Scheduled (Thứ 6) |
| **DIS-03** | **Data Export** | CSV/XLSX/API | Data Analysts | Manual Trigger |

---

## 📈 Đo lường Hiệu quả (Sample KPI for User)
*Dành cho việc thuyết phục user:*

1. **Trước AI:** 1 nhân viên R&D mất **4-8 tiếng** để đọc 500 reviews và viết báo cáo lỗi sản phẩm. Độ chính xác cảm tính ~60%.
2. **Sau AI (Nodes INT-01 + DIS-02):** Hệ thống mất **5 phút** để phân tích và gửi báo cáo tự động vào mail. Độ chính xác dữ liệu ~95%.
3. **Giá trị:** Tiết kiệm **~98% thời gian** và tăng **35% độ tin cậy** của báo cáo.

---

## 🛠️ Roadmap Tích hợp
- **Giai đoạn 1:** Ổn định các Node INT (Intelligence) - Đang thực hiện.
- **Giai đoạn 2:** Map các Node này vào Workflow của từng BU sau khi làm việc với PIC.
- **Giai đoạn 3:** Biến các Node thành Standalone Tools (Micro-apps) nếu cần thiết.
