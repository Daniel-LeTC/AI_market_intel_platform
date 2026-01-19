import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import os
import re
import sys
import uuid
from pathlib import Path

# Add root to sys.path to find core
sys.path.append(str(Path(__file__).resolve().parent.parent))
from core.config import Settings

# --- Config ---
st.set_page_config(
    page_title="RnD Scout - Market Intelligence",
    page_icon="🕵️",
    layout="wide"
)

# --- Database Helpers (Blue-Green Aware) ---
def get_db_path():
    """Get the current ACTIVE database path (Read-Only Target)"""
    return str(Settings.get_active_db_path())

def query_df(sql, params=None):
    """Run query against ACTIVE DB."""
    try:
        db_path = get_db_path()
        with duckdb.connect(db_path, read_only=True) as conn:
            return conn.execute(sql, params).df()
    except Exception as e:
        st.error(f"DB Error: {e}")
        return pd.DataFrame()

def query_one(sql, params=None):
    try:
        db_path = get_db_path()
        with duckdb.connect(db_path, read_only=True) as conn:
            res = conn.execute(sql, params).fetchone()
            return res[0] if res else None
    except Exception as e:
        st.error(f"DB Error: {e}")
        return None

def request_new_asin(asin_input, note="", force_update=False):
    """
    Smart Request Handler V2:
    1. Lookup 'products' table to map Child -> Parent ASIN.
    2. Check 'reviews' table for existing data (Last Scrape Date).
    3. Check for Duplicates in Queue.
    4. Flag Unknown ASINs.
    """
    db_path = get_db_path()
    
    final_asin = asin_input
    system_note = ""
    is_unknown = False

    try:
        with duckdb.connect(db_path, read_only=True) as conn:
            # 1. Lookup Product Logic
            row = conn.execute("SELECT parent_asin FROM products WHERE asin = ? OR parent_asin = ? LIMIT 1", [asin_input, asin_input]).fetchone()
            
            if row:
                mapped_parent = row[0]
                if mapped_parent and mapped_parent != asin_input:
                    final_asin = mapped_parent
                    system_note = f"[Auto-Map] Child {asin_input} -> Parent {final_asin}"
            else:
                is_unknown = True
                system_note = f"[Unknown ASIN] Not in Product DB. Admin verify Parent."

            # 2. Check Existing Data (Reviews)
            rev_stats = conn.execute("SELECT COUNT(*), MAX(review_date) FROM reviews WHERE parent_asin = ?", [final_asin]).fetchone()
            has_data = rev_stats[0] > 0
            last_date = rev_stats[1]
            
            if has_data and not force_update:
                return False, f"🛑 Đã có dữ liệu! Tìm thấy {rev_stats[0]} reviews (Mới nhất: {last_date}). Nếu cần cập nhật, hãy tick 'Force Update'."

            if has_data and force_update:
                system_note += f" | [Force Update] Last Data: {last_date}"

            # 3. Check Duplicate Queue
            check_sql = "SELECT status FROM scrape_queue WHERE asin = ? AND status IN ('PENDING_APPROVAL', 'READY_TO_SCRAPE', 'PROCESSING')"
            existing = conn.execute(check_sql, [final_asin]).fetchone()
            if existing:
                return False, f"⚠️ Yêu cầu cho {final_asin} đang chờ xử lý (Trạng thái: {existing[0]})."

    except Exception as e:
        return False, f"Lỗi hệ thống: {e}"

    # Append User Note
    full_note = f"{system_note} | {note}" if note else system_note

    # Insert
    req_id = str(uuid.uuid4())
    sql = """
        INSERT INTO scrape_queue (request_id, asin, status, requested_by, note)
        VALUES (?, ?, 'PENDING_APPROVAL', 'user', ?)
    """
    try:
        with duckdb.connect(db_path, read_only=False) as conn:
            conn.execute(sql, [req_id, final_asin, full_note])
        
        # Success Messages
        if is_unknown:
            return False, f"⚠️ Đã gửi yêu cầu cho {final_asin}. (Lưu ý: Không tìm thấy trong Product DB)."
        elif final_asin != asin_input:
            return True, f"✅ Đã tự động chuyển về ASIN Cha: {final_asin}. Yêu cầu đã được gửi!"
        else:
            return True, f"✅ Đã gửi yêu cầu thành công cho {final_asin}!"
            
    except Exception as e:
        return False, str(e)

# --- Sidebar ---
st.sidebar.title("🕵️ RnD Scout")
st.sidebar.markdown("---")

# View Mode Selection
view_mode = st.sidebar.radio(
    "Select Mode:", 
    ["🏠 Home Dashboard", "🕵️ AI Detective"],
    index=0
)
st.sidebar.markdown("---")

# Request Form
with st.sidebar.expander("➕ Yêu cầu Scrape ASIN Mới"):
    with st.form("req_form"):
        new_asin = st.text_input("Nhập ASIN:", placeholder="B0...")
        req_note = st.text_input("Ghi chú (Note):", placeholder="Tại sao cần scrape con này?")
        force_chk = st.checkbox("Force Update (Nếu đã có data)")
        
        submitted = st.form_submit_button("Gửi Yêu Cầu")
        if submitted:
            if not new_asin or not new_asin.startswith("B0"):
                st.error("ASIN không hợp lệ (Phải bắt đầu bằng 'B0')")
            else:
                ok, msg = request_new_asin(new_asin.strip(), req_note, force_chk)
                if ok:
                    if "⚠️" in msg: st.warning(msg) # Yellow for Unknown/Warning
                    else: st.success(msg)           # Green for Auto-Correct/Success
                else: st.warning(msg)               # Yellow for Error/Stop
    
    # Show History
    st.caption("🕒 Các yêu cầu gần đây")
    st.caption("🕒 Your Recent Requests")
    try:
        hist_df = query_df("SELECT asin, status FROM scrape_queue ORDER BY created_at DESC LIMIT 5")
        if not hist_df.empty:
            st.dataframe(hist_df, use_container_width=True, hide_index=True)
    except: pass

st.sidebar.markdown("---")

# Load danh sach ASIN
df_asins = query_df("""
    SELECT 
        parent_asin, 
        COUNT(*) as review_count, 
        ROUND(AVG(rating_score), 2) as avg_rating
    FROM reviews 
    GROUP BY parent_asin
    ORDER BY review_count DESC, parent_asin ASC
""")

if df_asins.empty:
    st.warning("No data found. Please ingest some reviews first.")
else:
    selected_asin = st.sidebar.selectbox(
        "Select Competitor (ASIN)", 
        df_asins['parent_asin'].tolist(),
        format_func=lambda x: f"{x} (⭐{df_asins[df_asins['parent_asin']==x]['avg_rating'].values[0]})"
    )

    # --- Common Data Fetching ---
    if selected_asin:
        # Lay thong tin DNA dùng chung cho cả 2 view
        dna_query = """
            SELECT 
                title, material, main_niche, gender, design_type, 
                target_audience, size_capacity, product_line, 
                num_pieces, pack, brand
            FROM products 
            WHERE asin = ? OR parent_asin = ? 
            LIMIT 1
        """
        dna = query_df(dna_query, [selected_asin, selected_asin])
        
        # Lay Real-time variations tu Review DB
        real_vars_count = query_one("SELECT COUNT(DISTINCT child_asin) FROM reviews WHERE parent_asin = ?", [selected_asin])
        
        # Header: Product Title
        product_display_title = selected_asin
        if not dna.empty and dna.iloc[0]['title']:
            product_display_title = f"{dna.iloc[0]['title'][:100]}..."

        # --- MAIN CONTENT ---
        if view_mode == "🏠 Home Dashboard":
            st.title(f"🔍 {product_display_title}")
            
            # 0. Product DNA Card
            if not dna.empty:
                d = dna.iloc[0]
                with st.container(border=True):
                    dna_col, var_col = st.columns([4, 1])
                    with dna_col:
                        st.markdown(f"🧶 **Material:** `{d['material'] or 'N/A'}` | 🏷️ **Brand:** `{d['brand'] or 'N/A'}`")
                        st.markdown(f"🎨 **Niche:** `{d['main_niche'] or 'N/A'}` | 🎯 **Target:** `{d['gender'] or ''} {d['target_audience'] or 'N/A'}`")
                        st.markdown(f"📏 **Specs:** `{d['num_pieces'] or d['pack'] or 'N/A'} Pieces` | 📐 **Size:** `{d['size_capacity'] or 'N/A'}` | 🚀 **Line:** `{d['product_line'] or 'N/A'}`")
                    with var_col:
                        st.metric("Active Variations", real_vars_count)
            else:
                st.info(f"🧬 **Product DNA:** Active Variations: **{real_vars_count}** (Metadata not found in RnD sheet)")

            # 1. KPI Cards
            kpi_query = """
                SELECT 
                    COUNT(*) as total_reviews,
                    AVG(rating_score) as avg_rating,
                    COUNT(DISTINCT child_asin) as total_variations,
                    SUM(CASE WHEN is_verified = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as verified_pct,
                    SUM(CASE WHEN rating_score <= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as negative_pct
                FROM reviews
                WHERE parent_asin = ?
            """
            kpis_df = query_df(kpi_query, [selected_asin])
            if not kpis_df.empty:
                kpis = kpis_df.iloc[0]
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Reviews", f"{kpis['total_reviews']}")
                col2.metric("Avg Rating", f"{kpis['avg_rating']:.2f} ⭐")
                col3.metric("Variations", f"{kpis['total_variations']}")
                col4.metric("Negative Rate", f"{kpis['negative_pct']:.1f}%", delta_color="inverse")

            st.markdown("---")

            # --- AI INTELLIGENCE SECTION ---
            st.subheader("🤖 AI Intelligence (RnD Scout)")
            tag_count = query_one("SELECT COUNT(*) FROM review_tags WHERE parent_asin = ?", [selected_asin]) or 0

            if tag_count > 0:
                ai_col1, ai_col2 = st.columns([1, 2])
                with ai_col1:
                    st.markdown("##### 🚨 Top Pain Points")
                    pain_query = """
                        SELECT 
                            COALESCE(am.standard_aspect, rt.aspect) as aspect,
                            COUNT(*) as count
                        FROM review_tags rt
                        LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
                        WHERE rt.parent_asin = ? AND rt.sentiment = 'Negative'
                        GROUP BY 1
                        ORDER BY 2 DESC
                        LIMIT 5
                    """
                    df_pain = query_df(pain_query, [selected_asin])
                    if not df_pain.empty:
                        for i, row in df_pain.iterrows():
                            st.error(f"**{row['aspect']}**: {row['count']} complaints")
                    else:
                        st.success("No major pain points detected yet!")

                with ai_col2:
                    st.markdown("##### 📊 Aspect Sentiment Analysis")
                    aspect_query = """
                        SELECT 
                            COALESCE(am.standard_aspect, rt.aspect) as aspect,
                            SUM(CASE WHEN rt.sentiment = 'Positive' THEN 1 ELSE 0 END) as positive,
                            SUM(CASE WHEN rt.sentiment = 'Negative' THEN 1 ELSE 0 END) as negative
                        FROM review_tags rt
                        LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
                        WHERE rt.parent_asin = ?
                        GROUP BY 1
                        HAVING (positive + negative) > 1 
                        ORDER BY (positive + negative) DESC
                        LIMIT 10
                    """
                    df_aspect = query_df(aspect_query, [selected_asin])
                    if not df_aspect.empty:
                        fig_aspect = px.bar(
                            df_aspect, y='aspect', x=['positive', 'negative'], 
                            orientation='h', 
                            labels={"value": "Mentions", "variable": "Sentiment"},
                            color_discrete_map={'positive': '#00CC96', 'negative': '#EF553B'}
                        )
                        st.plotly_chart(fig_aspect, use_container_width=True)
                
                with st.expander("🔍 View Evidence (Quotes)"):
                    ev_query = """
                        SELECT 
                            COALESCE(am.category, rt.category) as "Category",
                            CASE 
                                WHEN am.standard_aspect IS NOT NULL THEN '✅ ' || am.standard_aspect
                                ELSE '⏳ ' || rt.aspect 
                            END as "Aspect (Status)",
                            rt.sentiment as "Sentiment", 
                            rt.quote as "Evidence Quote"
                        FROM review_tags rt
                        LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
                        WHERE rt.parent_asin = ?
                        ORDER BY rt.sentiment, "Category"
                    """
                    st.dataframe(
                        query_df(ev_query, [selected_asin]), 
                        use_container_width=True,
                        column_config={
                            "Aspect (Status)": st.column_config.TextColumn("Aspect (Status)"),
                            "Evidence Quote": st.column_config.TextColumn("Quote", width="large")
                        }
                    )
            else:
                st.warning("⚠️ No AI analysis found for this ASIN.")

            st.markdown("---")

            # --- COMPETITOR BATTLE SECTION ---
            st.subheader("⚔️ The Arena: Competitor Battle")
            ai_asins_df = query_df("SELECT DISTINCT parent_asin FROM review_tags WHERE parent_asin != ?", [selected_asin])
            ai_asins = ai_asins_df['parent_asin'].tolist() if not ai_asins_df.empty else []
            
            if ai_asins:
                challenger_asin = st.selectbox("Select Challenger to Compare:", ai_asins)
                if challenger_asin:
                    battle_row_top_c1, battle_row_top_c2 = st.columns(2)
                    battle_query = f"""
                        WITH normalized AS (
                            SELECT 
                                rt.parent_asin,
                                rt.sentiment,
                                COALESCE(am.standard_aspect, rt.aspect) as aspect_norm
                            FROM review_tags rt
                            LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
                            WHERE rt.parent_asin IN ('{selected_asin}', '{challenger_asin}')
                        ),
                        stats AS (
                            SELECT 
                                parent_asin,
                                aspect_norm as aspect,
                                COUNT(*) as total_mentions,
                                SUM(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pos_pct
                            FROM normalized
                            GROUP BY 1, 2
                            HAVING total_mentions > 1
                        )
                        SELECT * FROM stats ORDER BY pos_pct DESC
                    """
                    df_all = query_df(battle_query)

                    with battle_row_top_c1:
                        st.markdown(f"##### ⚔️ Shared Features Face-off")
                        if not df_all.empty:
                            aspects_selected = set(df_all[df_all['parent_asin'] == selected_asin]['aspect'])
                            aspects_challenger = set(df_all[df_all['parent_asin'] == challenger_asin]['aspect'])
                            shared_aspects = sorted(list(aspects_selected.intersection(aspects_challenger)))
                            if shared_aspects:
                                ITEMS_PER_PAGE = 5
                                total_items = len(shared_aspects)
                                page = 1
                                if total_items > ITEMS_PER_PAGE:
                                    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
                                    c_page_1, c_page_2 = st.columns([2, 1])
                                    with c_page_1: st.caption(f"Page {page}/{total_pages}")
                                    with c_page_2: page = st.number_input("P", 1, total_pages, 1, key="battle_page", label_visibility="collapsed")
                                start_idx = (page - 1) * ITEMS_PER_PAGE
                                current_aspects = shared_aspects[start_idx : start_idx + ITEMS_PER_PAGE]
                                df_shared = df_all[df_all['aspect'].isin(current_aspects)].copy()
                                df_shared.sort_values(by=['aspect', 'parent_asin'], inplace=True)
                                fig_battle = px.bar(
                                    df_shared, x="pos_pct", y="aspect", color="parent_asin", 
                                    barmode="group", height=350, text_auto='.0f',
                                    color_discrete_sequence=['#FF8C00', '#00CC96'] # Orange for main, Teal for challenger
                                )
                                st.plotly_chart(fig_battle, use_container_width=True)
                            else:
                                st.info("No shared features.")

                    with battle_row_top_c2:
                        st.markdown("##### ⚠️ Top Weaknesses Comparison")
                        issue_col_a, issue_col_b = st.columns(2)
                        def get_top_issues(asin):
                            q = """SELECT COALESCE(am.standard_aspect, rt.aspect) as aspect, COUNT(*) as cnt FROM review_tags rt LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect WHERE rt.parent_asin = ? AND rt.sentiment = 'Negative' GROUP BY 1 ORDER BY 2 DESC LIMIT 5"""
                            return query_df(q, [asin])
                        df_issue_a = get_top_issues(selected_asin)
                        df_issue_b = get_top_issues(challenger_asin)
                        with issue_col_a:
                            st.caption(f"Issues: {selected_asin}")
                            if not df_issue_a.empty:
                                for _, row in df_issue_a.iterrows(): st.error(f"{row['aspect']} ({row['cnt']})")
                        with issue_col_b:
                            st.caption(f"Issues: {challenger_asin}")
                            if not df_issue_b.empty:
                                for _, row in df_issue_b.iterrows(): st.error(f"{row['aspect']} ({row['cnt']})")

            st.markdown("---")
            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader("📈 Rating Trend")
                df_trend = query_df("SELECT DATE_TRUNC('month', review_date) as month, AVG(rating_score) as avg_score FROM reviews WHERE parent_asin = ? GROUP BY 1 ORDER BY 1", [selected_asin])
                if not df_trend.empty: st.plotly_chart(px.line(df_trend, x='month', y='avg_score', markers=True), use_container_width=True)
            with c2:
                st.subheader("⚠️ Issues Distribution")
                df_dist = query_df("SELECT rating_score, COUNT(*) as count FROM reviews WHERE parent_asin = ? GROUP BY 1", [selected_asin])
                if not df_dist.empty: st.plotly_chart(px.pie(df_dist, names='rating_score', values='count', hole=0.4), use_container_width=True)

            st.subheader("📝 Latest Reviews (Deep Dive)")
            show_bad_only = st.checkbox("Show Negative Reviews Only (<= 3 stars)")
            base_query = "SELECT review_date, rating_score, title, text, variation_text, is_verified FROM reviews WHERE parent_asin = ?"
            if show_bad_only: base_query += " AND rating_score <= 3"
            base_query += " ORDER BY review_date DESC LIMIT 50"
            df_reviews = query_df(base_query, [selected_asin])
            st.dataframe(df_reviews, use_container_width=True, hide_index=True)

        else:
            st.header("🕵️ AI Detective")
            with st.container(border=True):
                col_icon, col_txt = st.columns([1, 6])
                with col_icon: st.markdown("<h1 style='text-align: center;'>🎯</h1>", unsafe_allow_html=True)
                with col_txt:
                    st.markdown(f"**Investigating Product:**")
                    st.subheader(product_display_title)
                    if not dna.empty:
                        d = dna.iloc[0]
                        st.markdown(f"**ASIN:** `{selected_asin}` | **Brand:** `{d.get('brand','N/A')}`")
            
            try: from scout_app.core.detective import DetectiveAgent
            except: from core.detective import DetectiveAgent
            
            if "detective" not in st.session_state: st.session_state.detective = DetectiveAgent()
            if "messages" not in st.session_state: st.session_state.messages = []
            for message in st.session_state.messages:
                with st.chat_message(message["role"]): st.markdown(message["content"])
            if prompt := st.chat_input("Ask the Detective..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("🕵️ Analyzing..."):
                        response = st.session_state.detective.answer(prompt, default_asin=selected_asin)
                        st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.info("Please select an ASIN from the sidebar to start analysis.")