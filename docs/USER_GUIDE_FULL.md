# 📘 HƯỚNG DẪN SỬ DỤNG: PRODUCT INTELLIGENCE PLATFORM (PIP)

**Phiên bản:** 1.0 (Release Candidate)
**Ngày cập nhật:** 28/01/2026
**URL Ứng dụng:** [http://34.87.30.120:8501/](http://34.87.30.120:8501/)
**Tài khoản Demo:**
*   **User:** `user_1000`
*   **Pass:** `123456`

---

## 1. GIỚI THIỆU CHUNG
**Product Intelligence Platform (PIP)** là công cụ hỗ trợ chuyên sâu cho **R&D và Phát triển Sản phẩm**. Hệ thống giúp kỹ sư và chuyên gia sản phẩm "đọc vị" hàng ngàn phản hồi của khách hàng để tìm ra công thức cải tiến sản phẩm tối ưu.

---

## 2. QUY TRÌNH ĐĂNG NHẬP & TIẾP CẬN

### 2.1. Đăng nhập
Truy cập URL ứng dụng, nhập thông tin tài khoản được cấp.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/login_screen.png" width="600" alt="Login Screen">
  <img src="../analysis_workspace/PIP-screenshot/login_panel.png" width="400" alt="Login Panel">
  <p><i>Hình 1a, 1b: Giao diện đăng nhập và Panel nhập liệu</i></p>
</div>

Sau khi đăng nhập thành công, hệ thống sẽ xác nhận:

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/logged_in_successfully.png" width="400" alt="Login Success">
  <p><i>Hình 2: Thông báo đăng nhập thành công</i></p>
</div>

### 2.2. Thanh Sidebar & Chọn ASIN
Thanh điều hướng bên trái (Sidebar) là trung tâm điều khiển.
*   **Ẩn/Hiện Sidebar:** Dùng nút mũi tên để mở rộng không gian làm việc.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/sidebar_details_and_hide_button.png" width="300" alt="Sidebar Toggle">
  <img src="../analysis_workspace/PIP-screenshot/sidebar_inside.png" width="300" alt="Sidebar Content">
  <p><i>Hình 3a, 3b: Chi tiết Sidebar</i></p>
</div>

---

## 3. QUẢN LÝ YÊU CẦU PHÂN TÍCH (REQUEST FLOW)

### 3.1. Yêu cầu ASIN Mới
Nếu sản phẩm bạn cần nghiên cứu chưa có trong Database, hãy nhập mã ASIN vào ô **Request New ASIN**.
*   **Lưu ý:** Hệ thống ưu tiên xử lý **Parent ASIN** để có cái nhìn tổng quát về cả dòng sản phẩm.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/request_totally_new_parent_asin.png" width="600" alt="Request New Parent ASIN">
  <p><i>Hình 4: Nhập Parent ASIN mới hoàn toàn</i></p>
</div>

### 3.2. Các trường hợp đặc biệt khi Request
*   **Nhập Child ASIN:** Hệ thống sẽ tự động phát hiện và gợi ý chuyển sang Parent ASIN.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/request_child_asin_instead_of_parent_asin.png" width="600" alt="Child ASIN Warning">
  <p><i>Hình 5: Cảnh báo khi nhập Child ASIN</i></p>
</div>

*   **ASIN chưa có Review:** Hệ thống sẽ cảnh báo nếu sản phẩm quá mới chưa có dữ liệu.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/request_new_parent_asin_not_have_review_yet.png" width="600" alt="No Review Warning">
  <p><i>Hình 6: Cảnh báo sản phẩm chưa có review</i></p>
</div>

*   **ASIN đã tồn tại:** Nếu ASIN đã có, hệ thống sẽ báo để bạn không cần chờ đợi.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/request_existed_asin.png" width="600" alt="Existed ASIN">
  <p><i>Hình 7: Thông báo ASIN đã có sẵn</i></p>
</div>

---

## 4. DASHBOARD TỔNG QUAN (EXECUTIVE SUMMARY)
Góc nhìn để nắm bắt nhanh tình hình tổng quát.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/executive_summary_dashboard.png" width="800" alt="Executive Dashboard">
  <p><i>Hình 8: Giao diện Executive Summary</i></p>
</div>

---

## 5. THẤU HIỂU KHÁCH HÀNG (CUSTOMER X-RAY)
Công cụ cốt lõi để tìm kiếm ý tưởng cải tiến sản phẩm (Product Improvement).

### 5.1. Chế độ mặc định & Heatmap
Màn hình mặc định hiển thị bản đồ nhiệt (Heatmap) của các khía cạnh sản phẩm (Vải, Kích thước, Độ bền...).

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/customer_xray_default.png" width="800" alt="X-Ray Default">
  <img src="../analysis_workspace/PIP-screenshot/customer_xray_mass_mode_head.png" width="800" alt="Mass Mode Header">
  <p><i>Hình 9a, 9b: Giao diện mặc định và Header chế độ Mass Mode</i></p>
</div>

### 5.2. Phân tích Heatmap (Mass Mode)
Dùng để quét nhanh điểm yếu của cả dòng sản phẩm. Màu vàng/nhạt là các vùng cần cải thiện kỹ thuật.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/customer_xray_mass_mode_heatmap.png" width="800" alt="Heatmap Detail">
  <p><i>Hình 10: Chi tiết Heatmap phân tích đa chiều</i></p>
</div>

### 5.3. Chỉ số Impact Score
Công cụ định lượng mức độ nghiêm trọng của vấn đề kỹ thuật. Giúp R&D ưu tiên sửa lỗi nào trước.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/customer_xray_impact_score.png" width="800" alt="Impact Score Chart">
  <img src="../analysis_workspace/PIP-screenshot/customer_xray_impact_score_explained.png" width="600" alt="Impact Score Logic">
  <p><i>Hình 11a, 11b: Biểu đồ Impact Score  Giải thích logic</i></p>
</div>

### 5.4. Truy xuất dẫn chứng (Quote Extraction)
Xem chi tiết khách hàng nói gì về một lỗi cụ thể để đội kỹ thuật có hướng xử lý.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/customer_xray_quote_extraction_table.png" width="800" alt="Quote Table">
  <img src="../analysis_workspace/PIP-screenshot/customer_xray_jump_list.png" width="400" alt="Jump List">
  <p><i>Hình 12a, 12b: Bảng trích dẫn review  Danh sách nhảy nhanh</i></p>
</div>

---

## 6. SO SÁNH ĐỐI THỦ (MARKET SHOWDOWN)
Dùng để Benchmarking thông số kỹ thuật với đối thủ.

### 6.1. Chọn đối thủ
*   **Smart Match:** Tự động tìm đối thủ cùng phân khúc.
*   **Manual Match:** Tự chọn đối thủ cụ thể.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/showdown_head_smart_match.png" width="800" alt="Smart Match Header">
  <img src="../analysis_workspace/PIP-screenshot/showdown_head_manual_match.png" width="800" alt="Manual Match Header">
  <p><i>Hình 13a, 13b: Hai chế độ chọn đối thủ</i></p>
</div>

### 6.2. So sánh chi tiết
Giao diện so sánh trực diện (Side-by-side) các chỉ số kỹ thuật.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/showdown_body.png" width="800" alt="Showdown Body">
  <p><i>Hình 14: Giao diện so sánh tổng thể</i></p>
</div>

### 6.3. Phân tích Điểm mạnh/Yếu (SWOT Kỹ thuật)
*   **Unique Aspects:** Tính năng độc nhất.
*   **Weakness:** Điểm yếu cần khắc phục.
*   **Shared Features:** Các tính năng tương đồng.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/showdown_unique_aspects.png" width="400" alt="Unique Aspects">
  <img src="../analysis_workspace/PIP-screenshot/showdown_weakness.png" width="400" alt="Weakness">
  <img src="../analysis_workspace/PIP-screenshot/showdown_shared_feat_explained.png" width="400" alt="Shared Features">
  <p><i>Hình 15a, 15b, 15c: Phân tích sâu các khía cạnh kỹ thuật</i></p>
</div>

---

## 7. TRỢ LÝ R&D (STRATEGY HUB)
Công cụ AI hỗ trợ Brainstorming ý tưởng sản phẩm mới.

### 7.1. Giao diện Chat & Quick Actions
Các phím tắt giúp tạo nhanh báo cáo R&D hoặc tóm tắt Insight.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/strat_hub_quick_actions_and_AI_chat.png" width="600" alt="Quick Actions">
  <p><i>Hình 16: Phím tắt tác vụ nhanh cho R&D</i></p>
</div>

### 7.2. Hỏi đáp chuyên sâu (Deep Dive)
Hỏi AI về các vấn đề kỹ thuật cụ thể (Ví dụ: "Độ dày vải", "Đường may").

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/strat_hub_AI_chat_example.png" width="600" alt="AI Chat Generic">
  <p><i>Hình 17: Giao diện Chat AI</i></p>
</div>

### 7.3. Dẫn chứng kỹ thuật (Evidence Based)
AI cung cấp bằng chứng từ review gốc để R&D validate thông tin.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/strat_hub_AI_chat_example_Thickness-aspect_evidence.png" width="800" alt="AI Evidence">
  <p><i>Hình 18: AI phân tích độ dày vải kèm dẫn chứng</i></p>
</div>

---

## 8. DÀNH CHO QUẢN TRỊ VIÊN (ADMIN ONLY)
Khu vực duyệt yêu cầu và giám sát Pipeline dữ liệu.

<div align="center">
  <img src="../analysis_workspace/PIP-screenshot/admin_console_for_approving_request.png" width="800" alt="Admin Approving">
  <img src="../analysis_workspace/PIP-screenshot/admin_pipeline_dashboard.png" width="800" alt="Admin Pipeline">
  <p><i>Hình 19a, 19b: Console quản trị & Dashboard hệ thống</i></p>
</div>

---
**END OF GUIDE**
