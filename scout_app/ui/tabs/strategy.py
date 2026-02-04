import streamlit as st
import streamlit.components.v1 as components

@st.fragment
def render_strategy_tab(selected_asin, current_user_id):
    """
    Renders Tab 4: Strategy Hub (AI Agent)
    """
    st.header("🧠 Strategy Hub")
    st.caption("Coordinate with your AI Detective to build winning strategies.")

    # --- LAZY IMPORT (Fix Performance & Circular Import) ---
    # Only load DetectiveAgent when this function is actually called
    try:
        from core.detective import DetectiveAgent
    except ImportError:
        # Fallback if sys.path is tricky
        from scout_app.core.detective import DetectiveAgent

    if "detective" not in st.session_state:
        st.session_state.detective = DetectiveAgent()
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- 1. Render Chat History (TOP) ---
    # This ensures that when we rerun, the full history (including new msg) appears first
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            # Anchor for the latest assistant response
            if message["role"] == "assistant" and i == len(st.session_state.messages) - 1:
                st.markdown("<div id='latest-answer'></div>", unsafe_allow_html=True)
            st.markdown(message["content"])

    # Auto-Scroll JS (Runs on every render)
    # If 'latest-answer' exists, scroll to it smoothly.
    auto_scroll_js = """
    <script>
        setTimeout(function() {
            var target = window.parent.document.getElementById('latest-answer');
            if (target) {
                target.scrollIntoView({behavior: "smooth", block: "start"});
            }
        }, 300);
    </script>
    """
    components.html(auto_scroll_js, height=0)

    st.markdown("---")

    # --- 2. Quick Action Buttons (MIDDLE) ---
    st.markdown("##### 🚀 Quick Strategy Actions")
    
    quick_prompt = None

    # Row 1: R&D & Strategy
    st.markdown("##### 🧠 Nghiên cứu & Chiến lược (R&D)")
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
    if r1_c1.button("🧠 Tâm lý khách", use_container_width=True, help="Tại sao khách mua?"):
        quick_prompt = "Phân tích các yếu tố thúc đẩy quyết định mua dựa trên dữ liệu thực tế. Sử dụng tool `analyze_customer_context`. Trình bày dạng bảng: [Yếu tố tâm lý] | [Dữ liệu chứng minh] | [Tác động]."
    if r1_c2.button("🚧 Rào cản mua", use_container_width=True, help="Tại sao khách chê?"):
        quick_prompt = "Xác định 3 lý do chính khiến khách hàng do dự hoặc đánh giá thấp sản phẩm. Sử dụng dữ liệu từ tool `get_product_swot`. Liệt kê trực diện, không văn vẻ."
    if r1_c3.button("💡 Ý tưởng SP mới", use_container_width=True, help="Cải tiến V2"):
        quick_prompt = "Đề xuất 3 cải tiến kỹ thuật cụ thể cho phiên bản V2.0 dựa trên điểm yếu của đối thủ cạnh tranh. Sử dụng tool `analyze_competitors`. Định dạng: [Cải tiến] | [Lý do/Dữ liệu] | [Độ ưu tiên]."
    if r1_c4.button("👥 Chân dung khách", use_container_width=True, help="Targeting"):
        quick_prompt = "Phân loại 3 nhóm khách hàng mục tiêu dựa trên dữ liệu review. Sử dụng tool `analyze_customer_context`. Định dạng bảng: [Phân khúc] | [Đặc điểm] | [Nhu cầu chính]."

    # Row 2: Execution & Content
    st.markdown("##### ⚡ Thực thi (Content & Media)")
    r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
    if r2_c1.button("🤖 Review Insights", use_container_width=True, help="Tóm tắt review"):
        quick_prompt = "Tóm tắt ngắn gọn các điểm khen/chê chính. Sử dụng tool `get_product_dna`. Không chào hỏi, vào thẳng danh sách gạch đầu dòng."
    if r2_c2.button("✍️ Viết Listing", use_container_width=True, help="Title & Bullets"):
        quick_prompt = "Tạo Title và 5 Bullet Points chuẩn SEO Amazon bằng tool `generate_listing_content`. Tập trung vào việc giải quyết các Pain Points thực tế từ review. Trả lời bằng Tiếng Anh (Listing) và Tiếng Việt (Giải thích)."
    if r2_c3.button("❓ Tạo Q&A", use_container_width=True, help="15 câu thắc mắc"):
        quick_prompt = "Soạn 10 cặp câu hỏi và trả lời (Q&A) dựa trên các thắc mắc và khiếu nại thực tế của khách hàng trong review. Sử dụng tool `search_review_evidence`."
    if r2_c4.button("📸 Media Brief", use_container_width=True, help="Gợi ý Media"):
        quick_prompt = "Đề xuất 5 concept hình ảnh/video để xử lý nỗi sợ của khách hàng. Liên kết mỗi concept với một điểm đau (Pain Point) cụ thể từ dữ liệu tool `get_product_swot`."

    # Row 3: Growth & Support
    st.markdown("##### 🚀 Tăng trưởng & Hỗ trợ")
    r3_c1, r3_c2, r3_c3, r3_c4 = st.columns(4)
    if r3_c1.button("⚔️ Soi Đối Thủ", use_container_width=True, help="So sánh với Brand khác"):
        quick_prompt = "So sánh sản phẩm hiện tại với các đối thủ cùng phân khúc. Sử dụng tool `analyze_competitors`. Chỉ ra chính xác đối thủ nào mạnh hơn ở điểm nào. Trình bày dạng bảng so sánh."
    if r3_c2.button("🔥 Roast Sản phẩm", use_container_width=True, help="Bóc phốt cực gắt"):
        quick_prompt = "Liệt kê những lời chê tệ nhất và gắt nhất về sản phẩm này dựa trên review. Không nói giảm nói tránh, không múa văn. Vào thẳng vấn đề."
    if r3_c3.button("💣 Kịch bản Seeding", use_container_width=True, help="Điều hướng dư luận"):
        quick_prompt = "Viết kịch bản seeding xử lý khủng hoảng dựa trên các điểm yếu thực tế. Sử dụng dữ liệu từ tool `search_review_evidence` để viết nội dung phản hồi thuyết phục."
    if r3_c4.button("📞 Kịch bản CSKH", use_container_width=True, help="Xử lý khiếu nại song ngữ"):
        quick_prompt = "Viết 3 mẫu kịch bản trả lời khiếu nại cho 3 vấn đề bị chê nhiều nhất. Nội dung giải thích bằng Tiếng Việt, văn mẫu phản hồi bằng Tiếng Anh chuyên nghiệp."

    st.markdown("---")

    # --- 3. Input Logic (BOTTOM) ---
    # Handle Quick Buttons (Set prompt directly)
    final_prompt = None
    if quick_prompt:
        final_prompt = quick_prompt
    
    # Handle Chat Input
    # Note: Streamlit's chat_input is separate from buttons. 
    # If button is clicked, quick_prompt is set -> We run logic.
    # If chat_input is used, prompt is set -> We run logic.
    
    if (prompt := st.chat_input("Ask Strategy Hub...")) or final_prompt:
        if not final_prompt:
            final_prompt = prompt

        # 1. Append User Msg & Draw immediately
        st.session_state.messages.append({"role": "user", "content": final_prompt})
        with st.chat_message("user"):
            st.markdown(final_prompt)
        
        # 2. Generate Answer (Streamed/Spinner)
        with st.chat_message("assistant"):
            with st.spinner("🕵️ Detective is thinking..."):
                try:
                    # Run Agent
                    response = st.session_state.detective.answer(
                        final_prompt, default_asin=selected_asin, user_id=current_user_id
                    )
                    st.markdown(response)
                    
                    # 3. Append Assistant Msg to History
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    st.error(f"Agent Error: {e}")
                    st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Error: {e}"})

    # Note: No st.rerun() needed here. 
    # The new messages are drawn. Next time user interacts, history loop at top handles re-drawing.
