import streamlit as st

st.set_page_config(page_title="Social Scout AI", page_icon="🛰️", layout="wide")

st.title("🛰️ Social Scout AI")

st.info("### 🚧 Under Construction")
st.markdown("""
Hệ thống Social Scout AI hiện đang được nâng cấp và tích hợp **Trend Bridge & Sentiment X-Ray**.
Trang này sẽ tạm đóng để đảm bảo an toàn cho các kết nối API Scraper.

**Dự kiến quay lại:** Sớm thôi! 🚀
""")

if st.button("⬅️ Quay lại Market Intelligence"):
    st.switch_page("Market_Intelligence.py")
