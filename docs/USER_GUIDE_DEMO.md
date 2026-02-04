# 📘 Hướng Dẫn Sử Dụng Bright Scraper (Demo Version)

**Tài khoản Demo:**
- **Username:** `user_1000`
- **Password:** `123456`
**Link app Demo:**
- https://http://34.87.30.120:8501/
---

## 1. Bắt Đầu (Getting Started)

### Đăng nhập & Chọn Sản phẩm
1.  Truy cập hệ thống và đăng nhập với tài khoản trên.
2.  Tại thanh điều hướng bên trái (**Sidebar**), bạn có thể chọn đối tượng phân tích:
    *   **Cách 1: Chọn ASIN có sẵn (Khuyên dùng):** Chọn mã sản phẩm (ASIN) từ danh sách xổ xuống (Ví dụ: `B00I9JJ50K`). Dữ liệu đã được xử lý sẵn sàng.
    *   **Cách 2:** Nếu ASIN bạn cần chưa có trong hệ thống, hoặc ASINs đang có trong hệ thống đã cũ, cần cập nhật, vui lòng nhập vào ô Request New ASIN -> Hệ thống sẽ xử lý và trả kết quả trong vòng 10 phút/ASIN
---

## 2. Market Intelligence (Trung Tâm Tình Báo)

Hệ thống cung cấp 4 góc nhìn bao quát và chi tiết về ASINs và thị trường:

### 🟢 Tab 1: Executive Summary (Tổng Quan)
*Góc nhìn nhanh*

*   **KPIs Thực tế:** Hiển thị Rating, Tổng Review, Tỷ lệ tiêu cực thực tế (đã lọc review ảo).
*   **Biến thể (Variations):** Hệ thống tự động phát hiện và liệt kê các **ASIN con** (Child ASINs) có review, giúp lược bớt các biến thể ít bán chạy.
*   **Product DNA:** Bóc tách thông số sản phẩm (Brand, Material, Niche...) từ dữ liệu cào được.
*   **Priority Actions:** Tự động cảnh báo Top 3 "nỗi đau" (Pain Points) lớn nhất của khách hàng cần khắc phục ngay ==> Lưu ý, đây là raw volume tức là đếm trên dữ liệu review thực tế đổ về.

---

### 🔵 Tab 2: Customer X-Ray (Thấu Hiểu Khách Hàng)
*Góc nhìn sâu trải nghiệm mua hàng.*

**Chế độ 1: Từng sản phẩm (Single Mode)**
*   **Phân tích cảm xúc (Sentiment Analysis):**
    *   **Raw Volume:** Đếm tần suất xuất hiện thô của từ khóa có trong kho reviews --> dùng để tham khảo các điểm mạnh, yếu **nhỏ** khác của ASINs
    *   **Impact Score (Quan trọng):** Quy đổi số lượng nhắc đến theo tỷ trọng phân bổ sao (Star Distribution). Giúp **ước tính** chính xác số lượng khách hàng thực tế đang gặp vấn đề (chứ không chỉ đếm trên mẫu thử).
*   **Phân bổ sao thực tế:** Biểu đồ tròn hiển thị tỷ lệ hài lòng thực sự của khách hàng.

**Chế độ 2: So sánh thị trường (Mass Mode)**
*   **Market Strength Map (Heatmap):** Bản đồ nhiệt so sánh sức mạnh của nhiều sản phẩm cùng lúc.
    *   **Màu sắc:** Thang màu (Vàng -> Xanh Đậm) thể hiện mật độ khách hàng hài lòng. Xanh đậm = Nhiều khách khen => phần nào phản ánh độ quan tâm về các khía cạnh nào đó của nhóm ASINs
    *   **Tương tác:** Di chuột vào ô để xem chi tiết số lượng khách khen và tổng rating của sản phẩm đó.
    *   **Quick Jump:** Click vào bất kỳ dòng sản phẩm nào trong bảng tóm tắt bên dưới để chuyển ngay sang phân tích chi tiết sản phẩm đó (Single Mode).

---

### ⚔️ Tab 3: Market Showdown (So Găng Đối Thủ)
*Chiến trường so sánh trực diện 1-vs-1.*

*   **Smart Match (Tìm đối thủ thông minh):**
    *   Hệ thống tự động tìm đối thủ "cùng hạng cân" (Rating chênh lệch trong khoảng **+/- 30%**) và ưu tiên cùng Ngách (Niche) / Dòng sản phẩm (Line).
    *   *Fallback:* Nếu không tìm thấy đối thủ phù hợp, hệ thống sẽ nới lỏng biên độ lên **+/- 50%** để đảm bảo luôn có đối tượng so sánh.
*   **Battle Matrix (Bảng tỉ số):**
    *   So sánh trực diện các tính năng chung (Shared Features).
    *   **Cơ chế trọng tài (Weighted Win):** Người thắng được xác định bởi **Số lượng khách hài lòng thực tế (Proven Quality)**, không dựa vào tỷ lệ % ảo.
    *   *Ví dụ:* Sản phẩm có 1,000 khách khen sẽ thắng sản phẩm chỉ có 10 khách khen (dù tỷ lệ hài lòng của bên 10 người là 100%).
*   **Unique Features:**
    *   Liệt kê các tính năng mà **chỉ mình bạn (ASINs chủ lực bạn chọn) được khen** (đối thủ không có hoặc bị chê).
*   **Weaknesses Comparison:** Soi điểm yếu chí mạng của cả hai bên để.

---

### 🧠 Tab 4: Strategy Hub 
*Trợ lý AI cao cấp & Công cụ tác nghiệp.*

*   **Detective Agent Chat:** Khung chat trực tiếp với AI để hỏi đáp sâu về dữ liệu (Ví dụ: "Tại sao khách chê vải nóng?", "So sánh giá với đối thủ") hoặc đọc các trích dẫn reviews để hiểu sâu insight của khía cạnh được nêu.
*   **12 Phím Tắt Quick Prompts:**
    *   Hệ thống cung cấp sẵn 12 kịch bản phân tích nhanh (Prompt Templates) cho 3 làm việc: Nghiên cứu, lên **Content** (Nội dung), các vấn đề **Growth** (Tăng trưởng).
    *   *Ví dụ:* Nhấn nút **"Viết mô tả sản phẩm"** -> AI tự động viết đoạn mô tả chuẩn dựa trên các từ khóa khách hàng sử dụng trong review => tận dụng quote và khía cạnh của review để định hướng.

---

## 3. Lưu ý Kỹ Thuật (Technical Notes)
*   **Dữ liệu mẫu (Sampling):** Dữ liệu phân tích được lấy từ 10 trang review mới nhất (tối đa) trên amazon và được lấy về theo số sao-tức là maximum 1 loại sao là 100 reviews, sau đó được thuật toán ngoại suy (Extrapolate), phân bổ ngược lại với tỷ trọng total ratings để phản ánh bức tranh toàn cảnh.
*   **Độ trễ:** Dữ liệu mới cào (Live Scraping) cần khoảng 5-10 phút để hệ thống xử lý và cập nhật vào Dashboard.
