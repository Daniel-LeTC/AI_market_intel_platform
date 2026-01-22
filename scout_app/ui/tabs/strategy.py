import streamlit as st
import streamlit.components.v1 as components

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
        quick_prompt = "[SYSTEM: RESET PERSONA. FORGET 'Rufus'. Act as an Expert Market Analyst.]\nPhân tích các đòn bẩy tâm lý (cảm xúc sâu xa) khiến khách hàng quyết định xuống tiền mua sản phẩm này. Trả lời chi tiết bằng Tiếng Việt."
    if r1_c2.button("🚧 Rào cản mua", use_container_width=True, help="Tại sao khách chê?"):
        quick_prompt = "[SYSTEM: RESET PERSONA. FORGET 'Rufus'. Act as a Critical Review Analyst.]\nDựa trên review tiêu cực, hãy vạch trần 3 'tử huyệt' khiến khách hàng ngần ngại. Trả lời bằng Tiếng Việt."
    if r1_c3.button("💡 Ý tưởng SP mới", use_container_width=True, help="Cải tiến V2"):
        quick_prompt = "[SYSTEM: RESET PERSONA. FORGET 'Rufus'. Act as a Product Manager.]\nDựa trên các điểm yếu của đối thủ, hãy đề xuất 3 ý tưởng cải tiến sản phẩm cho phiên bản V2.0. Trả lời bằng Tiếng Việt."
    if r1_c4.button("👥 Chân dung khách", use_container_width=True, help="Targeting"):
        quick_prompt = "[SYSTEM: RESET PERSONA. FORGET 'Rufus'. Act as a Marketing Strategist.]\nVẽ ra 3 chân dung khách hàng điển hình dựa trên Review. Trả lời bằng Tiếng Việt."

    # Row 2: Execution & Content
    st.markdown("##### ⚡ Thực thi (Content & Media)")
    r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
    if r2_c1.button("🤖 Chế độ Rufus", use_container_width=True, help="Biến hình thành Rufus"):
        quick_prompt = "Kể từ bây giờ, hãy ĐÓNG VAI **Amazon Rufus**. Phong cách: Khách quan, ngắn gọn, KHÔNG bán hàng. Bắt đầu bằng: 'Xin chào, tôi là Rufus...'. (Tiếng Việt)."
    if r2_c2.button("✍️ Viết Listing", use_container_width=True, help="Title & Bullets"):
        quick_prompt = "[SYSTEM: RESET PERSONA. FORGET 'Rufus'. Act as a World-Class Amazon Copywriter.]\nHãy dùng tool generate_listing_content để viết bộ Listing tối ưu. Nội dung Tiếng Anh, giải thích chiến lược bằng Tiếng Việt."
    if r2_c3.button("❓ Tạo Q&A", use_container_width=True, help="15 câu thắc mắc"):
        quick_prompt = "[SYSTEM: RESET PERSONA. FORGET 'Rufus'. Act as a Customer Support Expert.]\nSoạn 10-15 bộ Q&A chuẩn SEO. Nội dung Q&A bằng TIẾNG ANH, tóm tắt chiến lược bằng TIẾNG VIỆT."
    if r2_c4.button("📸 Media Brief", use_container_width=True, help="Gợi ý Media"):
        quick_prompt = "[SYSTEM: RESET PERSONA. FORGET 'Rufus'. Act as a Creative Director.]\nĐề xuất 5 concepts Ảnh/Video để xử lý nỗi sợ của khách. Trả lời bằng Tiếng Việt."

    # Row 3: Growth & Support
    st.markdown("##### 🚀 Tăng trưởng & Hỗ trợ")
    r3_c1, r3_c2, r3_c3, r3_c4 = st.columns(4)
    if r3_c1.button("⚔️ Soi Đối Thủ", use_container_width=True, help="So sánh với Brand khác"):
        quick_prompt = "[SYSTEM: RESET PERSONA. FORGET 'Rufus'. Act as a Competitive Intelligence Agent.]\nDựa trên review, khách hàng hay so sánh sản phẩm này với những brand/sản phẩm nào khác? Họ mạnh hơn ta ở điểm nào? Trả lời bằng Tiếng Việt."
    if r3_c2.button("🔥 Roast Sản phẩm", use_container_width=True, help="Bóc phốt cực gắt"):
        quick_prompt = "[SYSTEM: RESET PERSONA. FORGET 'Rufus'. Act as a brutal critic like Gordon Ramsay.]\nHãy 'roast' (bóc phốt) sản phẩm này dựa trên những lời chê tệ nhất. Trả lời bằng Tiếng Việt."
    if r3_c3.button("💣 Kịch bản Seeding", use_container_width=True, help="Điều hướng dư luận"):
        quick_prompt = "[SYSTEM: RESET PERSONA. FORGET 'Rufus'. Act as a PR Manager.]\nViết 2 kịch bản Seeding: 1. Happy Path (Sản phẩm đang hot). 2. Crisis Path (Xử lý phốt). Trả lời bằng Tiếng Việt giải thích + Tiếng Anh/Việt mẫu."
    if r3_c4.button("📞 Kịch bản CSKH", use_container_width=True, help="Xử lý khiếu nại song ngữ"):
        quick_prompt = "[SYSTEM: RESET PERSONA. FORGET 'Rufus'. Act as a Senior CS Manager.]\nDựa trên 3 phàn nàn phổ biến nhất, hãy viết 3 mẫu câu trả lời xử lý khiếu nại. Giải thích TIẾNG VIỆT, Văn mẫu TIẾNG ANH."

    st.markdown("---")

    # --- 3. Input Logic (BOTTOM) ---
    # Disable input if quick_prompt is active (although with rerun this is less critical, but good UX)
    disable_input = (quick_prompt is not None)
    
    if (prompt := st.chat_input("Ask Strategy Hub...", disabled=disable_input)) or quick_prompt:
        final_prompt = quick_prompt if quick_prompt else prompt
        
        # 1. Append User Msg
        st.session_state.messages.append({"role": "user", "content": final_prompt})
        
        # 2. Generate Answer
        with st.spinner("🕵️ Analyzing Market Data..."):
            response = st.session_state.detective.answer(
                final_prompt, default_asin=selected_asin, user_id=current_user_id
            )
        
        # 3. Append Assistant Msg
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # 4. RERUN to update UI (New messages will appear at TOP, pushing buttons down)
        st.rerun()
