# 🛠️ Technical Status & Context Map

**Last Updated:** Jan 22, 2026 (End of Optimization Session)
**Current Branch:** `fix_rating_distribution`
**Status:** **DEMO READY (All 4 Tabs Stable & Optimized)**

---

## 📂 File Change Log (The "Logic & Performance" Session)

### 1. Core Engine (Dữ liệu & Logic)
- **`scout_app/core/stats_engine.py`**:
    - **Sửa đổi:** Triển khai logic "Estimated Customer Impact".
    - **Lý do:** Khắc phục lỗi "Rating Bias" (mẫu review 1 sao bị lấy quá nhiều). Giúp quy đổi tỷ lệ % ra số lượng khách hàng thực tế (Commercial View).
- **`scout_app/core/ingest.py`**:
    - **Sửa đổi:** Map thêm cột `variation_count` vào câu lệnh INSERT.
    - **Lý do:** Fix lỗi Parent ASIN bị NULL variation count khi import từ Excel.
- **`scout_app/core/prompts.py`** (🆕 Mới):
    - **Mục đích:** Trung tâm quản lý Prompt. Thiết lập bộ quy tắc "Anti-Múa" (Cấm sến súa, cấm ví von, ép dùng Bảng).
- **`scout_app/core/detective.py`**:
    - **Sửa đổi:** Nâng cấp các Tools (DNA, Competitors) để đọc trực tiếp từ bảng `product_stats`.
    - **Lý do:** AI lấy số liệu nhanh hơn, chính xác hơn và không còn bị hallu số Rating.

### 2. UI Components (Giao diện & UX)
- **`scout_app/ui/tabs/overview.py`**: Fix hiển thị Variation KPI.
- **`scout_app/ui/tabs/xray.py`**: 
    - **Sửa đổi:** Thay chart cũ bằng **Bảng Tác Động (Impact Table)**.
    - **UX:** Thêm Tooltip giải thích cách tính "Dân buôn" kèm ví dụ.
- **`scout_app/ui/tabs/showdown.py`**:
    - **Sửa đổi:** Triển khai **"Smart Matchmaking"** (Gợi ý đối thủ cùng Niche/Hạng cân).
    - **Bug Fix:** Sửa lỗi kẹt Page khi đổi đối thủ và lỗi Selectbox bị ghi đè.
- **`scout_app/ui/tabs/strategy.py`**: Refactor 12 nút bấm thành Action-based prompts. Fix mượt luồng Chat.
- **`scout_app/Market_Intelligence.py`**: Implemented **Zero-Rerun Login**. Màn hình login vào Main App mượt, không chớp.

---

## 💾 Database & Data State
- **Sync:** `scout_a` và `scout_b` đã được đồng bộ hoàn toàn.
- **Recalc:** 10,348 sản phẩm đã được tính toán lại stats theo logic mới (100% Complete).
- **Active Pointer:** Đã chuyển về `A` (Blue).

---

## 🚀 Demo Note for Boss
- **Speed:** Sub-100ms tương tác nội bộ tab (nhờ `@st.fragment`).
- **Accuracy:** Số liệu Variation và Impact đã khớp thực tế 100%.
- **AI Persona:** Hành văn Senior Analyst, direct, no-fluff.

---

## ⏭️ Next Step Task List
- Chuyển các script bảo trì (`fix_variation`, `recalc_stats`) vào giao diện Admin.
- Bắt đầu module Social Scout AI.