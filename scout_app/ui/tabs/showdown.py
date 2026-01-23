import streamlit as st
import pandas as pd
import plotly.express as px
from scout_app.ui.common import query_df

@st.fragment
def render_showdown_tab(selected_asin):
    """
    Renders Tab 3: Market Showdown (Head-to-Head)
    """
    st.subheader("⚔️ Head-to-Head Comparison")
    
    # 1. Get My DNA
    my_dna = query_df("SELECT * FROM products WHERE asin = ?", [selected_asin])
    if my_dna.empty:
        st.warning("Product data not found.")
        return
        
    my_row = my_dna.iloc[0]
    my_niche = my_row.get('main_niche') or 'NONE'
    my_ratings = float(my_row.get('real_total_ratings', 0) or 0)
    my_line = my_row.get('product_line') or 'NONE'
    
    # 2. Smart Matchmaking via SQL (Sub-millisecond performance)
    # Tier 1: Same Niche (3 pts)
    # Tier 2: Same Line (2 pts)
    # Tier 3: Same Weight Class (+/- 25% = 3 pts, +/- 50% = 1 pt)
    
    match_sql = f"""
        SELECT 
            asin, title, image_url, real_total_ratings, real_average_rating, main_niche, product_line,
            (
                (CASE WHEN main_niche = ? THEN 3 ELSE 0 END) +
                (CASE WHEN product_line = ? THEN 2 ELSE 0 END) +
                (CASE 
                    WHEN real_total_ratings BETWEEN ? AND ? THEN 3
                    WHEN real_total_ratings BETWEEN ? AND ? THEN 1
                    ELSE 0 
                 END)
            ) as match_score
        FROM products 
        WHERE asin != ? AND real_total_ratings > 0
        ORDER BY match_score DESC, real_total_ratings DESC
        LIMIT 100
    """
    
    params = [
        my_niche, my_line, 
        my_ratings * 0.75, my_ratings * 1.25, # 25% margin
        my_ratings * 0.5, my_ratings * 1.5,   # 50% margin
        selected_asin
    ]
    
    candidates = query_df(match_sql, params)
    
    if candidates.empty:
        st.warning("No competitors found in database.")
        return

    # 3. Categorize Results
    smart_df = candidates[candidates['match_score'] >= 3].copy()
    others_df = candidates[candidates['match_score'] < 3].copy()

    def build_options(df):
        opts = []
        for _, row in df.iterrows():
            opts.append({
                "label": f"{row['asin']} - {row['title'][:40]}... (⭐{row['real_average_rating']:.1f} | {int(row['real_total_ratings'])} revs)",
                "asin": row['asin']
            })
        return opts

    smart_picks = build_options(smart_df)
    others = build_options(others_df)
    
    # 4. Render Selection UI
    challenger_asin = None
    c_smart, c_manual = st.tabs(["🤖 Smart Picks (Recommended)", "🔍 Manual Search"])
    
    with c_smart:
        if smart_picks:
            st.caption(f"Found {len(smart_picks)} relevant competitors based on Niche & Volume.")
            # Use Radio for better visibility than Selectbox
            choice = st.radio(
                "Select a Smart Match:",
                options=smart_picks,
                format_func=lambda x: f"✨ {x['label']}",
                key=f"smart_sel_{selected_asin}"
            )
            if choice:
                challenger_asin = choice['asin']
        else:
            st.info("No close matches found. Try Manual Search.")
            
    with c_manual:
        # Fallback to big list
        all_opts = smart_picks + others
        choice_manual = st.selectbox(
            "Search by ASIN or Title:",
            options=all_opts,
            format_func=lambda x: x['label'],
            index=None, # Default to None so it doesn't override Radio
            placeholder="Type to search...",
            key=f"manual_sel_{selected_asin}"
        )
        # Priority: Manual Search > Smart Pick (if Manual is selected)
        if choice_manual:
            challenger_asin = choice_manual['asin']
        # Else: Keep challenger_asin from Smart Pick (Radio)

    # --- MAIN LOGIC ---
    if challenger_asin:
        # st.write(f"DEBUG: Challenger = {challenger_asin}") # Uncomment to debug
        
        # --- 0. TALE OF THE TAPE (REAL STATS) ---
        st.markdown("#### 🥊 Tale of the Tape (Market Reality)")
        tape_sql = """
            SELECT asin, real_average_rating, real_total_ratings 
            FROM products WHERE asin IN (?, ?)
        """
        df_tape = query_df(tape_sql, [selected_asin, challenger_asin])
        
        if not df_tape.empty:
            row_me = df_tape[df_tape['asin'] == selected_asin].iloc[0] if not df_tape[df_tape['asin'] == selected_asin].empty else None
            row_them = df_tape[df_tape['asin'] == challenger_asin].iloc[0] if not df_tape[df_tape['asin'] == challenger_asin].empty else None
            
            c_t1, c_t2, c_t3 = st.columns([1, 0.2, 1])
            with c_t1:
                st.caption(f"🔵 {selected_asin}")
                if row_me is not None:
                    st.metric("Rating", f"{row_me['real_average_rating']:.1f} ⭐")
                    st.metric("Total Ratings", f"{row_me['real_total_ratings']:,.0f}")
            with c_t2:
                st.markdown("<h2 style='text-align: center;'>VS</h2>", unsafe_allow_html=True)
            with c_t3:
                st.caption(f"🔴 {challenger_asin}")
                if row_them is not None:
                    st.metric("Rating", f"{row_them['real_average_rating']:.1f} ⭐", 
                              delta=f"{row_them['real_average_rating'] - (row_me['real_average_rating'] if row_me is not None else 0):.1f}")
                    st.metric("Total Ratings", f"{row_them['real_total_ratings']:,.0f}",
                              delta=f"{row_them['real_total_ratings'] - (row_me['real_total_ratings'] if row_me is not None else 0):,.0f}")
        
        st.markdown("---")

        # --- SECTION 1: SHARED FEATURES (WEIGHTED MATRIX) ---
        from scout_app.ui.common import get_precalc_stats, get_niche_benchmark
        
        st.markdown("#### 🤝 Shared Features Face-off (Battle Matrix)")
        
        stats_me = get_precalc_stats(selected_asin)
        stats_them = get_precalc_stats(challenger_asin)
        
        niche = my_row.get('main_niche')
        benchmark = get_niche_benchmark(niche)
        
        if stats_me and stats_them:
            df_me_raw = pd.DataFrame(stats_me.get("sentiment_weighted", []))
            df_them_raw = pd.DataFrame(stats_them.get("sentiment_weighted", []))
            
            if not df_me_raw.empty and not df_them_raw.empty:
                # Calculate Satisfaction % and Volume
                df_me_raw["Me_Sat"] = (df_me_raw["est_positive"] / (df_me_raw["est_positive"] + df_me_raw["est_negative"] + 1e-9)) * 100
                df_them_raw["Them_Sat"] = (df_them_raw["est_positive"] / (df_them_raw["est_positive"] + df_them_raw["est_negative"] + 1e-9)) * 100
                
                # Align data
                m1 = df_me_raw[["aspect", "Me_Sat", "total_impact_vol"]].rename(columns={"total_impact_vol": "Me_Vol"})
                m2 = df_them_raw[["aspect", "Them_Sat", "total_impact_vol"]].rename(columns={"total_impact_vol": "Them_Vol"})
                
                df_battle = pd.merge(m1, m2, on="aspect", how="inner")
                
                # Ensure Market_Avg column exists even if benchmark is None
                if benchmark:
                    df_bench = pd.DataFrame(list(benchmark.items()), columns=["aspect", "Market_Avg"])
                    df_battle = pd.merge(df_battle, df_bench, on="aspect", how="left")
                else:
                    df_battle["Market_Avg"] = pd.NA
                
                if not df_battle.empty:
                    # Logic: Who wins?
                    def determine_winner(row):
                        diff = row['Me_Sat'] - row['Them_Sat']
                        if abs(diff) < 1: return "⚪ Tie"
                        return "🔵 Bạn" if diff > 0 else "🔴 Đối thủ"

                    df_battle["Winner"] = df_battle.apply(determine_winner, axis=1)
                    
                    # Formatting for display
                    df_disp = df_battle.copy()
                    df_disp["Me_Sat"] = df_disp["Me_Sat"].map(lambda x: f"{x:.0f}%")
                    df_disp["Them_Sat"] = df_disp["Them_Sat"].map(lambda x: f"{x:.0f}%")
                    df_disp["Market_Avg"] = df_disp["Market_Avg"].map(lambda x: f"{x:.0f}%" if pd.notnull(x) else "N/A")
                    
                    # Column renaming for UI
                    df_disp = df_disp.rename(columns={
                        "aspect": "Feature",
                        "Me_Sat": "Bạn",
                        "Them_Sat": "Đối thủ",
                        "Market_Avg": "Thị trường",
                        "Me_Vol": "Lượt nhắc (Bạn)",
                        "Them_Vol": "Lượt nhắc (ĐT)"
                    })

                    st.dataframe(
                        df_disp[["Feature", "Bạn", "Đối thủ", "Winner", "Thị trường", "Lượt nhắc (Bạn)", "Lượt nhắc (ĐT)"]],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Bạn": st.column_config.TextColumn(help="Tỉ lệ hài lòng của bạn"),
                            "Đối thủ": st.column_config.TextColumn(help="Tỉ lệ hài lòng của đối thủ"),
                            "Winner": st.column_config.TextColumn(help="Thằng nào đang làm tốt hơn ở khía cạnh này"),
                            "Lượt nhắc (Bạn)": st.column_config.NumberColumn(format="%d", help="Số người quan tâm/nhắc tới ở phía bạn"),
                        }
                    )
                    st.caption(f"ℹ️ **Ghi chú:** Người thắng là bên có tỷ lệ hài lòng cao hơn ít nhất 5%. Nếu lượt nhắc quá thấp, kết quả chỉ mang tính tham khảo.")
                else:
                    st.info("No shared features found in analysis data.")
            else:
                st.warning("Insufficient data for detailed comparison.")
        else:
            st.info("Stats not yet fully calculated for both products.")

        st.markdown("---")

        # --- SECTION 2: UNIQUE FEATURES ---
        st.markdown("#### 💎 Unique/Exclusive Features")
        c_uniq1, c_uniq2 = st.columns(2)
        
        aspects_me = set(df_me_raw["aspect"])
        aspects_them = set(df_them_raw["aspect"])
        
        unique_me_list = list(aspects_me - aspects_them)
        unique_them_list = list(aspects_them - aspects_me)

        def render_unique_table(asin, aspect_list, df_source, key_prefix):
            if not aspect_list:
                st.info("No unique features detected.")
                return
            
            df_u = df_source[df_source["aspect"].isin(aspect_list)].copy()
            df_u["Satisfaction"] = (df_u["est_positive"] / (df_u["est_positive"] + df_u["est_negative"] + 1e-9) * 100).map(lambda x: f"{x:.0f}%")
            
            # Pagination if too many unique features
            rows_per_page = 10
            if len(df_u) > rows_per_page:
                t_pages = (len(df_u) + rows_per_page - 1) // rows_per_page
                pg = st.number_input(f"Page ({key_prefix})", 1, t_pages, 1, key=f"pg_u_{key_prefix}_{selected_asin}")
                start = (pg-1)*rows_per_page
                df_show = df_u.iloc[start : start+rows_per_page]
            else:
                df_show = df_u

            st.dataframe(df_show[["aspect", "Satisfaction"]].rename(columns={"aspect": "Unique Feature"}), hide_index=True, use_container_width=True)

        with c_uniq1:
            st.subheader(f"Only in {selected_asin}")
            render_unique_table(selected_asin, unique_me_list, df_me_raw, "me")
        
        with c_uniq2:
            st.subheader(f"Only in {challenger_asin}")
            render_unique_table(challenger_asin, unique_them_list, df_them_raw, "them")

        st.markdown("---")
        
        # --- SECTION 3: WEAKNESSES ---
        st.markdown("#### 💔 Top Weaknesses Comparison")
        cw1, cw2 = st.columns(2)
        
        def render_top_weakness(df_source, title):
            if df_source.empty:
                st.info("No data available.")
                return
            # Filter for negative impact aspects and sort by magnitude
            df_w_list = df_source[df_source["net_impact"] < 0].sort_values("est_negative", ascending=False).head(5)
            if not df_w_list.empty:
                st.dataframe(df_w_list[["aspect", "est_negative"]].rename(columns={"aspect": "Pain Point", "est_negative": "Est. Complaints"}), hide_index=True, use_container_width=True)
            else:
                st.success("No major weaknesses detected.")

        with cw1:
            st.error(f"Issues: {selected_asin}")
            render_top_weakness(df_me_raw if 'df_me_raw' in locals() else pd.DataFrame(), selected_asin)
        
        with cw2:
            st.error(f"Issues: {challenger_asin}")
            render_top_weakness(df_them_raw if 'df_them_raw' in locals() else pd.DataFrame(), challenger_asin)

    else:
        st.warning("No other products found in DB to compare.")
