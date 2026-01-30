# TASK 06: Standalone Feedback Form
- Target: `scout_app/feedback_app.py`
- Objective: Tạo form thu thập ý kiến người dùng chạy độc lập (Standalone), không ảnh hưởng UI app chính.
- Features:
    - **Separate App:** Chạy process Streamlit riêng, URL riêng.
    - **Database:** Lưu vào bảng `user_feedback` trong `scout_app/database/system.duckdb`.
    - **Fields:**
        - User Identity (Optional - Text input hoặc Dropdown nếu muốn query DB).
        - Rating (Star/Slider).
        - Feature Request (Text).
        - Bug Report (Text).
        - General Comment.
    - **Deployment:** Cần cấu hình chạy trên port khác (ví dụ 8502) hoặc path riêng.

## ACTION PLAN
1.  **DB Schema:** Tạo bảng `user_feedback` (id, user_identity, rating, feature_request, bug_report, comment, created_at).
2.  **Coding:** Viết file `feedback_app.py`.
3.  **Deployment Script:** Update script deploy để chạy thêm process này.

## NOTES
- User Guide không cần cập nhật vì đây là link rời, gửi riêng cho tester.
- "Identity" để optional cho thoải mái.
