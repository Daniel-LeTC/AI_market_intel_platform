import os
from datetime import datetime

import duckdb
import streamlit as st

# --- CONFIG & DB ---
DB_PATH = "scout_app/database/system.duckdb"


def init_db():
    """Ensure feedback table exists in system database."""
    try:
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        conn = duckdb.connect(DB_PATH)
        conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_feedback_id START 1;
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER DEFAULT nextval('seq_feedback_id'),
                user_identity VARCHAR,
                rating INTEGER,
                feature_request TEXT,
                bug_report TEXT,
                other_comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.close()
    except Exception as e:
        st.error(f"⚠️ Lỗi khởi tạo Database: {e}")


def save_feedback(identity, rating, feature, bug, comment):
    """Save user entry to DuckDB."""
    try:
        conn = duckdb.connect(DB_PATH)
        conn.execute(
            """
            INSERT INTO user_feedback (user_identity, rating, feature_request, bug_report, other_comment)
            VALUES (?, ?, ?, ?, ?)
        """,
            [identity, rating, feature, bug, comment],
        )
        conn.close()
        return True
    except Exception as e:
        st.error(f"⚠️ Lỗi lưu feedback: {e}")
        return False


# --- UI APP ---
st.set_page_config(page_title="PIP - User Feedback Form (Phase 1)", page_icon="🧬", layout="centered")

init_db()

st.title("🧬 PIP - Feedback Loop (Phase 1)")
st.info(
    "Ý kiến của bạn giúp chúng tôi hoàn thiện sản phẩm. Mọi đóng góp đều tập trung vào khía cạnh R&D và Cải tiến sản phẩm."
)

with st.form("feedback_form", clear_on_submit=True):
    # Identity (Optional)
    user_identity = st.text_input("Tên hoặc User ID (Optional)", placeholder="Để trống nếu muốn ẩn danh...")

    st.divider()

    # Rating
    rating = st.select_slider(
        "Mức độ hài lòng chung với Phase 1 (Market Intelligence)",
        options=[1, 2, 3, 4, 5],
        value=5,
        help="1: Rất tệ - 5: Tuyệt vời",
    )

    # Feature Request
    feature_req = st.text_area(
        "🚀 Tính năng mới đề xuất", placeholder="Bạn cần thêm ngóc ngách nào của sản phẩm để soi kỹ hơn?"
    )

    # Bug Report
    bug_rep = st.text_area("🐞 Báo lỗi (nếu có)", placeholder="Mô tả lỗi hoặc các chỗ dữ liệu chưa khớp...")

    # Other
    other_comment = st.text_area("💬 Góp ý khác", placeholder="Bất kỳ điều gì bạn muốn nhắn nhủ đội ngũ R&D...")

    submit = st.form_submit_button("Gửi Phản Hồi")

if submit:
    if save_feedback(user_identity, rating, feature_req, bug_rep, other_comment):
        st.balloons()
        st.success("✅ Cảm ơn bạn! Thông tin đã được gửi tới đội ngũ phát triển.")
        st.info("Bạn có thể đóng trình duyệt hoặc quay lại app chính.")
    else:
        st.error("❌ Có lỗi xảy ra. Vui lòng thử lại sau.")

st.caption("© 2026 PIP - Internal R&D Project")
