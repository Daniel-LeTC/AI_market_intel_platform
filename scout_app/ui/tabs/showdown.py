import pandas as pd
import plotly.express as px
import streamlit as st

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
    my_niche = my_row.get("main_niche") or "NONE"
    my_ratings = float(my_row.get("real_total_ratings", 0) or 0)
    my_line = my_row.get("product_line") or "NONE"

    # 2. Smart Matchmaking (Strict Weight Class Strategy)
    # Logic:
    # - Round 1: Strict Range (+/- 30%). Only fight opponents in same weight class.
    # - Round 2 (Fallback): If no one found, broaden to +/- 50%.
    # - Sorting: Priority = Same Niche > Same Line > Closest Rating
    
    def fetch_candidates(rating_min, rating_max):
        sql = """
            SELECT 
                asin, title, image_url, real_total_ratings, real_average_rating, main_niche, product_line
            FROM products 
            WHERE asin != ? 
              AND real_total_ratings BETWEEN ? AND ?
            ORDER BY 
                (CASE WHEN main_niche = ? THEN 2 ELSE 0 END) + 
                (CASE WHEN product_line = ? THEN 1 ELSE 0 END) DESC,
                ABS(real_total_ratings - ?) ASC
            LIMIT 50
        """
        return query_df(sql, [selected_asin, rating_min, rating_max, my_niche, my_line, my_ratings])

    # Try Strict Match (+/- 30%)
    candidates = fetch_candidates(my_ratings * 0.7, my_ratings * 1.3)
    
    # Fallback (+/- 50%) if too few candidates
    if len(candidates) < 3:
        candidates = fetch_candidates(my_ratings * 0.5, my_ratings * 1.5)
    
    if candidates.empty:
        st.warning("No competitors found in similar weight class (+/- 50% ratings).")
        return

    # 3. Categorize Results (Smart vs Others)
    # Smart = Same Niche OR Same Line (High Relevance)
    # Others = Just same weight class
    
    # Check if Niche/Line matches
    candidates['is_smart'] = (candidates['main_niche'] == my_niche) | (candidates['product_line'] == my_line)
    
    smart_df = candidates[candidates['is_smart']].copy()
    others_df = candidates[~candidates['is_smart']].copy()

    def build_options(df):
        opts = []
        for _, row in df.iterrows():
            opts.append(
                {
                    "label": f"{row['asin']} - {row['title'][:40]}... (⭐{row['real_average_rating']:.1f} | {int(row['real_total_ratings'])} revs)",
                    "asin": row["asin"],
                }
            )
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
                key=f"smart_sel_{selected_asin}",
            )
            if choice:
                challenger_asin = choice["asin"]
        else:
            st.info("No close matches found. Try Manual Search.")

    with c_manual:
        # Fallback to big list
        all_opts = smart_picks + others
        choice_manual = st.selectbox(
            "Search by ASIN or Title:",
            options=all_opts,
            format_func=lambda x: x["label"],
            index=None,  # Default to None so it doesn't override Radio
            placeholder="Type to search...",
            key=f"manual_sel_{selected_asin}",
        )
        # Priority: Manual Search > Smart Pick (if Manual is selected)
        if choice_manual:
            challenger_asin = choice_manual["asin"]
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
            row_me = (
                df_tape[df_tape["asin"] == selected_asin].iloc[0]
                if not df_tape[df_tape["asin"] == selected_asin].empty
                else None
            )
            row_them = (
                df_tape[df_tape["asin"] == challenger_asin].iloc[0]
                if not df_tape[df_tape["asin"] == challenger_asin].empty
                else None
            )

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
                    st.metric(
                        "Rating",
                        f"{row_them['real_average_rating']:.1f} ⭐",
                        delta=f"{row_them['real_average_rating'] - (row_me['real_average_rating'] if row_me is not None else 0):.1f}",
                    )
                    st.metric(
                        "Total Ratings",
                        f"{row_them['real_total_ratings']:,.0f}",
                        delta=f"{row_them['real_total_ratings'] - (row_me['real_total_ratings'] if row_me is not None else 0):,.0f}",
                    )

        st.markdown("---")

        # --- SECTION 1: SHARED FEATURES (WEIGHTED MATRIX) ---
        from scout_app.ui.common import get_niche_benchmark, get_precalc_stats

        st.markdown("#### 🤝 Shared Features Face-off (Battle Matrix)")

        stats_me = get_precalc_stats(selected_asin)
        stats_them = get_precalc_stats(challenger_asin)

        niche = my_row.get("main_niche")
        benchmark = get_niche_benchmark(niche)

        if stats_me and stats_them:
            df_me_raw = pd.DataFrame(stats_me.get("sentiment_weighted", []))
            df_them_raw = pd.DataFrame(stats_them.get("sentiment_weighted", []))

            if not df_me_raw.empty and not df_them_raw.empty:
                # Calculate Satisfaction % and Volume
                df_me_raw["Me_Sat"] = (
                    df_me_raw["est_positive"] / (df_me_raw["est_positive"] + df_me_raw["est_negative"] + 1e-9)
                ) * 100
                df_them_raw["Them_Sat"] = (
                    df_them_raw["est_positive"] / (df_them_raw["est_positive"] + df_them_raw["est_negative"] + 1e-9)
                ) * 100

                # Align data - Use est_positive (Weighted Population) for Winner Logic
                m1 = df_me_raw[["aspect", "Me_Sat", "est_positive"]].rename(columns={"est_positive": "Me_Pop"})
                m2 = df_them_raw[["aspect", "Them_Sat", "est_positive"]].rename(columns={"est_positive": "Them_Pop"})

                df_battle = pd.merge(m1, m2, on="aspect", how="inner")

                # Ensure Market_Avg column exists even if benchmark is None
                if benchmark:
                    df_bench = pd.DataFrame(list(benchmark.items()), columns=["aspect", "Market_Avg"])
                    df_battle = pd.merge(df_battle, df_bench, on="aspect", how="left")
                else:
                    df_battle["Market_Avg"] = pd.NA

                # --- FILTER: Battle of Strengths Only ---
                # Only compare aspects where BOTH sides have at least some positive feedback.
                # If one side has 0 positive, it's not a battle, it's a slaughter (or irrelevant).
                df_battle = df_battle[(df_battle["Me_Pop"] > 0) & (df_battle["Them_Pop"] > 0)]

                if not df_battle.empty:
                    # Logic: Who wins? (Based on Proven Population - est_positive)
                    def determine_winner(row):
                        score_me = row["Me_Pop"]
                        score_them = row["Them_Pop"]

                        # Tie logic: If difference is less than 10% of the max score OR raw difference is trivial (<2 people)
                        max_score = max(score_me, score_them)
                        if max_score < 2:
                            return "⚪ Tie"  # Too little data

                        diff_pct = abs(score_me - score_them) / max_score

                        if diff_pct < 0.10:
                            return "⚪ Tie"  # < 10% diff considered margin of error

                        return "🔵 Bạn" if score_me > score_them else "🔴 Đối thủ"

                    df_battle["Winner"] = df_battle.apply(determine_winner, axis=1)

                    # Formatting for display
                    df_disp = df_battle.copy()
                    df_disp["Me_Sat"] = df_disp["Me_Sat"].map(lambda x: f"{x:.0f}%")
                    df_disp["Them_Sat"] = df_disp["Them_Sat"].map(lambda x: f"{x:.0f}%")
                    df_disp["Market_Avg"] = df_disp["Market_Avg"].map(lambda x: f"{x:.0f}%" if pd.notnull(x) else "N/A")

                    # Column renaming for UI
                    df_disp = df_disp.rename(
                        columns={
                            "aspect": "Feature",
                            "Me_Sat": "Bạn (%)",
                            "Them_Sat": "Đối thủ (%)",
                            "Market_Avg": "Thị trường",
                            "Me_Pop": "Khách khen (Bạn)",
                            "Them_Pop": "Khách khen (ĐT)",
                        }
                    )

                    st.dataframe(
                        df_disp[["Feature", "Bạn (%)", "Đối thủ (%)", "Winner", "Khách khen (Bạn)", "Khách khen (ĐT)"]],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Bạn (%)": st.column_config.TextColumn(help="Tỉ lệ hài lòng (Satisfaction Rate)"),
                            "Đối thủ (%)": st.column_config.TextColumn(help="Tỉ lệ hài lòng (Satisfaction Rate)"),
                            "Winner": st.column_config.TextColumn(
                                help="Bên thắng dựa trên SỐ LƯỢNG khách hàng hài lòng thực tế (Proven Quality)."
                            ),
                            "Khách khen (Bạn)": st.column_config.ProgressColumn(
                                format="%d",
                                min_value=0,
                                max_value=int(max(df_disp["Khách khen (Bạn)"].max(), df_disp["Khách khen (ĐT)"].max())),
                                help="Số lượng khách ước tính hài lòng (Weighted Volume)",
                            ),
                            "Khách khen (ĐT)": st.column_config.ProgressColumn(
                                format="%d",
                                min_value=0,
                                max_value=int(max(df_disp["Khách khen (Bạn)"].max(), df_disp["Khách khen (ĐT)"].max())),
                                help="Số lượng khách ước tính hài lòng (Weighted Volume)",
                            ),
                        },
                    )
                    st.caption("""
                    ℹ️ **Cơ chế trọng tài (Proven Quality):** Chúng tôi so sánh **Tổng số lượng khách hài lòng thực tế**, không chỉ so sánh tỷ lệ %.
                    
                    **Ví dụ minh họa:**
                    - **Sản phẩm A:** 100 Ratings. Có 50% khách khen "Bền". 👉 **Ước tính: 50 người khen.**
                    - **Sản phẩm B:** 80 Ratings. Có 80% khách khen "Bền". 👉 **Ước tính: 64 người khen.**
                    
                    🏆 **Kết quả:** **B Thắng** (64 > 50).
                    *Lý do: Dù A có tổng rating cao hơn, nhưng B làm khía cạnh "Bền" tốt hơn hẳn nên số lượng khách hàng thực tế hài lòng cao hơn.*
                    """)
                else:
                    st.info("No shared features found in analysis data.")
            else:
                st.warning("Insufficient data for detailed comparison.")
        else:
            st.info("Stats not yet fully calculated for both products.")

        st.markdown("---")

        # --- SECTION 2: UNIQUE FEATURES ---
        st.markdown("#### 💎 Unique/Exclusive Features (Lợi thế độc quyền)")
        c_uniq1, c_uniq2 = st.columns(2)

        aspects_me = set(df_me_raw["aspect"])
        aspects_them = set(df_them_raw["aspect"])

        unique_me_list = list(aspects_me - aspects_them)
        unique_them_list = list(aspects_them - aspects_me)

        def render_unique_table(asin, aspect_list, df_source):
            if not aspect_list:
                st.info("No unique features detected.")
                return
            
            df_u = df_source[df_source["aspect"].isin(aspect_list)].copy()
            # Rename est_positive for consistency
            df_u = df_u.rename(columns={"aspect": "Unique Feature", "est_positive": "Khách khen (Est)"})
            
            # FILTER: Only show features that actually have positive feedback (USPs)
            df_u = df_u[df_u["Khách khen (Est)"] > 0]
            
            if df_u.empty:
                st.info("No unique strengths detected (all unique aspects have 0 positive feedback).")
                return

            # Use fixed height for scrolling (Avoids misalignment)
            st.dataframe(
                df_u[["Unique Feature", "Khách khen (Est)"]].sort_values("Khách khen (Est)", ascending=False),
                hide_index=True, 
                use_container_width=True,
                height=300, # Fixed height ensures headers align
                column_config={
                    "Khách khen (Est)": st.column_config.ProgressColumn(
                        format="%d",
                        min_value=0,
                        max_value=int(df_u["Khách khen (Est)"].max() if not df_u.empty else 100),
                        help="Số lượng khách hàng ước tính hài lòng về tính năng độc quyền này."
                    )
                }
            )

        with c_uniq1:
            st.caption(f"🔵 Only in **{selected_asin}**")
            render_unique_table(selected_asin, unique_me_list, df_me_raw)

        with c_uniq2:
            st.caption(f"🔴 Only in **{challenger_asin}**")
            render_unique_table(challenger_asin, unique_them_list, df_them_raw)

        st.markdown("---")

        # --- SECTION 3: WEAKNESSES ---
        st.markdown("#### 💔 Top Weaknesses (Vấn đề nghiêm trọng)")
        cw1, cw2 = st.columns(2)

        def render_top_weakness(df_source):
            if df_source.empty:
                st.info("No data available.")
                return
            # Filter for negative impact aspects and sort by magnitude
            df_w_list = df_source[df_source["net_impact"] < 0].sort_values("est_negative", ascending=False).head(5)

            if not df_w_list.empty:
                df_w_list = df_w_list.rename(columns={"aspect": "Pain Point", "est_negative": "Khách chê (Est)"})
                st.dataframe(
                    df_w_list[["Pain Point", "Khách chê (Est)"]],
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Khách chê (Est)": st.column_config.ProgressColumn(
                            format="%d",
                            min_value=0,
                            max_value=int(df_w_list["Khách chê (Est)"].max()),
                            help="Số lượng khách hàng ước tính đang gặp vấn đề này.",
                        )
                    },
                )
            else:
                st.success("✅ No major weaknesses detected.")

        with cw1:
            st.caption(f"Issues: {selected_asin}")
            render_top_weakness(df_me_raw if "df_me_raw" in locals() else pd.DataFrame())

        with cw2:
            st.caption(f"Issues: {challenger_asin}")
            render_top_weakness(df_them_raw if "df_them_raw" in locals() else pd.DataFrame())

        st.caption(
            "ℹ️ **Khách chê (Est):** Số lượng khách hàng thực tế ước tính đang gặp vấn đề (Dựa trên tỷ lệ review tiêu cực 1-3 sao nhân với tổng số lượng khách hàng)."
        )
