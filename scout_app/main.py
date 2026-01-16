import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import os

# --- Config ---
st.set_page_config(
    page_title="RnD Scout - Market Intelligence",
    page_icon="🕵️",
    layout="wide"
)

DB_PATH = "scout_app/database/scout.duckdb"

# --- Database Helpers (SAFE MODE) ---
def query_df(sql, params=None):
    """Run query and return DataFrame. Auto-closes connection."""
    try:
        with duckdb.connect(DB_PATH, read_only=True) as conn:
            return conn.execute(sql, params).df()
    except Exception as e:
        st.error(f"DB Error: {e}")
        return pd.DataFrame()

def query_one(sql, params=None):
    """Run query and return single value. Auto-closes connection."""
    try:
        with duckdb.connect(DB_PATH, read_only=True) as conn:
            res = conn.execute(sql, params).fetchone()
            return res[0] if res else None
    except Exception as e:
        st.error(f"DB Error: {e}")
        return None

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
    st.stop()

selected_asin = st.sidebar.selectbox(
    "Select Competitor (ASIN)", 
    df_asins['parent_asin'].tolist(),
    format_func=lambda x: f"{x} (⭐{df_asins[df_asins['parent_asin']==x]['avg_rating'].values[0]})"
)

# --- Common Data Fetching ---
if selected_asin:
    # Lay thong tin DNA dùng chung cho cả 2 view
    dna_query = f"""
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
        
        # 0. Product DNA Card (PRO VERSION)
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
        kpi_query = f"""
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
        
        # Check if we have tags for this ASIN
        tag_count = query_one("SELECT COUNT(*) FROM review_tags WHERE parent_asin = ?", [selected_asin]) or 0

        if tag_count > 0:
            ai_col1, ai_col2 = st.columns([1, 2])
            
            with ai_col1:
                # 1. Top Pain Points (Negative Sentiments)
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
                # 2. Aspect Heatmap
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
            
            # 3. Evidence Board
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
            st.warning("⚠️ No AI analysis found for this ASIN. Run the Mining Agent to extract insights.")
            if st.button("🚀 Run AI Miner (Background)"):
                st.info("Feature coming soon: Trigger AI Miner from UI.")

        st.markdown("---")

        # --- COMPETITOR BATTLE SECTION ---
        st.subheader("⚔️ The Arena: Competitor Battle")
        
        # Lay danh sach cac ASIN co data AI Tags
        ai_asins_df = query_df("SELECT DISTINCT parent_asin FROM review_tags WHERE parent_asin != ?", [selected_asin])
        ai_asins = ai_asins_df['parent_asin'].tolist() if not ai_asins_df.empty else []
        
        if ai_asins:
            challenger_asin = st.selectbox("Select Challenger to Compare:", ai_asins)
            
            if challenger_asin:
                # 1. Top Row: Direct Comparison & Issues
                battle_row_top_c1, battle_row_top_c2 = st.columns(2)
                
                # Query lay het stats cua ca 2 thang
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
                        # Convert to list and SORT to ensure consistent order
                        shared_aspects = sorted(list(aspects_selected.intersection(aspects_challenger)))
                        
                        if shared_aspects:
                            # --- PAGINATION LOGIC ---
                            ITEMS_PER_PAGE = 5
                            total_items = len(shared_aspects)
                            
                            # Only show controls if needed
                            page = 1
                            if total_items > ITEMS_PER_PAGE:
                                total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
                                c_page_1, c_page_2 = st.columns([2, 1])
                                with c_page_1:
                                    st.caption(f"Found {total_items} shared features. Page {page}/{total_pages}")
                                with c_page_2:
                                    page = st.number_input("Page", 1, total_pages, 1, key="battle_page", label_visibility="collapsed")
                            
                            start_idx = (page - 1) * ITEMS_PER_PAGE
                            end_idx = start_idx + ITEMS_PER_PAGE
                            current_aspects = shared_aspects[start_idx:end_idx]
                            
                            # Filter & Sort Data for Chart
                            df_shared = df_all[df_all['aspect'].isin(current_aspects)].copy()
                            # Sort by Aspect Name so bars align perfectly side-by-side
                            df_shared.sort_values(by=['aspect', 'parent_asin'], inplace=True)

                            fig_battle = px.bar(
                                df_shared, x="pos_pct", y="aspect", color="parent_asin", 
                                barmode="group", labels={"pos_pct": "Satisfaction (%)", "aspect": ""},
                                height=350, color_discrete_sequence=['#636EFA', '#FFA15A'],
                                text_auto='.0f' # Show value on bar to fix "invisible bar" issue
                            )
                            fig_battle.update_layout(
                                margin=dict(l=0, r=0, t=30, b=0),
                                yaxis={'categoryorder':'category descending'}, # Keep sort order
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            st.plotly_chart(fig_battle, use_container_width=True)
                        else:
                            st.info("No direct shared features.")

                with battle_row_top_c2:
                    st.markdown("##### ⚠️ Top Weaknesses Comparison")
                    issue_col_a, issue_col_b = st.columns(2)
                    
                    def get_top_issues(asin):
                        q = """
                            SELECT COALESCE(am.standard_aspect, rt.aspect) as aspect, COUNT(*) as cnt 
                            FROM review_tags rt
                            LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
                            WHERE rt.parent_asin = ? AND rt.sentiment = 'Negative' 
                            GROUP BY 1 ORDER BY 2 DESC LIMIT 5
                        """
                        return query_df(q, [asin])

                    df_issue_a = get_top_issues(selected_asin)
                    df_issue_b = get_top_issues(challenger_asin)

                    with issue_col_a:
                        st.caption(f"Issues: {selected_asin}")
                        if not df_issue_a.empty:
                            for _, row in df_issue_a.iterrows():
                                st.error(f"{row['aspect']} ({row['cnt']})")
                        else: st.success("No major issues.")

                    with issue_col_b:
                        st.caption(f"Issues: {challenger_asin}")
                        if not df_issue_b.empty:
                            for _, row in df_issue_b.iterrows():
                                st.error(f"{row['aspect']} ({row['cnt']})")
                        else: st.success("No major issues.")

                # 2. Exclusive Features
                st.markdown("---")
                st.markdown("##### 💎 Exclusive Features (Differentiation Factors)")
                battle_row_bot_c1, battle_row_bot_c2 = st.columns(2)
                
                if not df_all.empty:
                    unique_selected = aspects_selected - aspects_challenger
                    unique_challenger = aspects_challenger - aspects_selected
                    
                    with battle_row_bot_c1:
                        st.caption(f"Only found in {selected_asin}")
                        if unique_selected:
                            df_unique_sel = df_all[(df_all['parent_asin'] == selected_asin) & (df_all['aspect'].isin(unique_selected))]
                            for _, row in df_unique_sel.iterrows():
                                label = f"**{row['aspect']}**: {row['pos_pct']:.0f}% Positive ({row['total_mentions']})"
                                if row['pos_pct'] > 70: st.success(label)
                                else: st.info(label)
                        else: st.write("None.")

                    with battle_row_bot_c2:
                        st.caption(f"Only found in {challenger_asin}")
                        if unique_challenger:
                            df_unique_cha = df_all[(df_all['parent_asin'] == challenger_asin) & (df_all['aspect'].isin(unique_challenger))]
                            for _, row in df_unique_cha.iterrows():
                                label = f"**{row['aspect']}**: {row['pos_pct']:.0f}% Positive ({row['total_mentions']})"
                                if row['pos_pct'] > 70: st.success(label)
                                else: st.info(label)
                        else: st.write("None.")

        st.markdown("---")
        # Charts
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("📈 Rating Trend")
            trend_query = "SELECT DATE_TRUNC('month', review_date) as month, AVG(rating_score) as avg_score FROM reviews WHERE parent_asin = ? GROUP BY 1 ORDER BY 1"
            df_trend = query_df(trend_query, [selected_asin])
            if not df_trend.empty:
                st.plotly_chart(px.line(df_trend, x='month', y='avg_score', markers=True), use_container_width=True)
        with c2:
            st.subheader("⚠️ Issues Distribution")
            df_dist = query_df("SELECT rating_score, COUNT(*) as count FROM reviews WHERE parent_asin = ? GROUP BY 1", [selected_asin])
            st.plotly_chart(px.pie(df_dist, names='rating_score', values='count', hole=0.4), use_container_width=True)

        # 3. Deep Dive Table
        st.subheader("📝 Latest Reviews (Deep Dive)")
        
        filter_col1, _ = st.columns([1, 1])
        with filter_col1:
            show_bad_only = st.checkbox("Show Negative Reviews Only (<= 3 stars)")
        
        base_query = "SELECT review_date, rating_score, title, text, variation_text, is_verified FROM reviews WHERE parent_asin = ?"
        if show_bad_only:
            base_query += " AND rating_score <= 3"
        base_query += " ORDER BY review_date DESC LIMIT 50"
        
        df_reviews = query_df(base_query, [selected_asin])
        st.dataframe(
            df_reviews, 
            column_config={
                "review_date": st.column_config.DateColumn("Date"),
                "rating_score": st.column_config.NumberColumn("Rating", format="%.1f ⭐"),
                "is_verified": st.column_config.CheckboxColumn("Verified"),
                "text": st.column_config.TextColumn("Review Content", width="large"),
            },
            use_container_width=True,
            hide_index=True
        )

    else:
        # ==========================================
        # NEW: DETECTIVE UI WITH PRODUCT CARD
        # ==========================================
        st.header("🕵️ AI Detective")
        
        # --- PROMINENT PRODUCT SCORECARD ---
        with st.container(border=True):
            col_icon, col_txt = st.columns([1, 6])
            with col_icon:
                st.markdown("<h1 style='text-align: center;'>🎯</h1>", unsafe_allow_html=True)
            with col_txt:
                st.markdown(f"**Investigating Product:**")
                st.subheader(product_display_title)
                if not dna.empty:
                    d = dna.iloc[0]
                    st.markdown(f"**ASIN:** `{selected_asin}` | **Brand:** `{d.get('brand','N/A')}` | **Material:** `{d.get('material','N/A')}` | **Target:** `{d.get('target_audience','N/A')}`")
                else:
                    st.markdown(f"**ASIN:** `{selected_asin}` | Metadata not found in sheet.")
        
        st.warning(f"⚠️ All questions below will be answered based on reviews for **{selected_asin}** unless you specify another ASIN.")
        
        # Chat Logic
        try:
            from core.detective import DetectiveAgent
        except ImportError:
            from scout_app.core.detective import DetectiveAgent
        
        if "detective" not in st.session_state:
            st.session_state.detective = DetectiveAgent()
        
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask the Detective (e.g., 'Compare quality with B0...','What are the pain points?')"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("🕵️ Detective is analyzing evidence..."):
                    # Use default_asin to help the agent
                    response = st.session_state.detective.answer(prompt, default_asin=selected_asin)
                    st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.info("Please select an ASIN from the sidebar to start analysis.")
