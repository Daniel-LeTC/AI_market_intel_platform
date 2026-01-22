import streamlit as st
import plotly.express as px
from scout_app.ui.common import query_df

@st.fragment
def render_showdown_tab(selected_asin):
    """
    Renders Tab 3: Market Showdown (Head-to-Head)
    """
    st.subheader("⚔️ Head-to-Head Comparison")
    
    ai_asins_df = query_df(
        "SELECT DISTINCT parent_asin FROM review_tags WHERE parent_asin != ? ORDER BY parent_asin", [selected_asin]
    )
    ai_asins = ai_asins_df["parent_asin"].tolist() if not ai_asins_df.empty else []

    if ai_asins:
        c_sel, c_blank = st.columns([1, 2])
        with c_sel:
            challenger_asin = st.selectbox(
                "Select Challenger:", 
                ai_asins,
                key=f"challenger_select_{selected_asin}"
            )
        
        if challenger_asin:
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

            # --- SECTION 1: SHARED FEATURES ---
            st.markdown("#### 🤝 Shared Features Face-off")
            if not df_all.empty:
                aspects_selected = set(df_all[df_all["parent_asin"] == selected_asin]["aspect"])
                aspects_challenger = set(df_all[df_all["parent_asin"] == challenger_asin]["aspect"])
                shared_aspects_list = sorted(list(aspects_selected.intersection(aspects_challenger)))
                
                if shared_aspects_list:
                    # Pagination Logic for Chart
                    ITEMS_PER_PAGE = 10
                    total_items = len(shared_aspects_list)
                    page = 1
                    
                    if total_items > ITEMS_PER_PAGE:
                        total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
                        c_pg1, c_pg2 = st.columns([3, 1])
                        with c_pg1:
                            st.caption(f"Showing {total_items} Shared Aspects | Page {page}/{total_pages}")
                        with c_pg2:
                            page = st.number_input("Chart Page", 1, total_pages, 1, key="battle_page")
                    
                    start_idx = (page - 1) * ITEMS_PER_PAGE
                    current_aspects = shared_aspects_list[start_idx : start_idx + ITEMS_PER_PAGE]
                    
                    # Filter Data for Chart
                    df_shared = df_all[df_all["aspect"].isin(current_aspects)].copy()
                    df_shared.sort_values(by=["aspect", "parent_asin"], inplace=True)
                    
                    fig_battle = px.bar(
                        df_shared,
                        x="pos_pct",
                        y="aspect",
                        color="parent_asin",
                        barmode="group",
                        height=400,
                        text_auto=".0f",
                        color_discrete_sequence=["#FF8C00", "#00CC96"],
                        title=f"Sentiment Comparison (Page {page})",
                        labels={"pos_pct": "Sentiment Score (%)", "aspect": "Feature", "parent_asin": "Product"} # Renamed
                    )
                    st.plotly_chart(fig_battle, use_container_width=True)
                else:
                    st.info("No shared features found to compare.")

            st.markdown("---")

            # --- SECTION 2: UNIQUE FEATURES ---
            st.markdown("#### 💎 Unique/Exclusive Features")
            c_uniq1, c_uniq2 = st.columns(2)
            
            # Logic: Aspects present in A but NOT in B
            unique_to_me = list(aspects_selected - aspects_challenger)
            unique_to_challenger = list(aspects_challenger - aspects_selected)

            def render_unique_list(aspects, owner_name, key_prefix):
                if not aspects:
                    st.info("None")
                    return
                
                df_uniq = df_all[
                    (df_all["parent_asin"] == owner_name) & 
                    (df_all["aspect"].isin(aspects))
                ][["aspect", "total_mentions", "pos_pct"]]

                # Rename columns for UX
                df_uniq.rename(columns={"aspect": "Unique Feature", "total_mentions": "Mentions", "pos_pct": "Sentiment Score (%)"}, inplace=True)

                df_uniq.sort_values("Mentions", ascending=False, inplace=True)

                # Pagination for Dataframe
                rows_per_page = 10
                total_rows = len(df_uniq)
                start_idx = 0
                end_idx = rows_per_page
                
                # Data Slice
                pg = 1
                if total_rows > rows_per_page:
                    t_pages = (total_rows + rows_per_page - 1) // rows_per_page
                    # Render dataframe FIRST, then pagination controls below
                    start_idx = 0 
                    
                    # Placeholder strategy
                    table_placeholder = st.empty()
                    
                    # Pagination Control BELOW
                    pg = st.number_input(f"Page ({key_prefix})", 1, t_pages, 1, key=f"pg_{key_prefix}")
                    
                    start_idx = (pg-1)*rows_per_page
                    end_idx = pg*rows_per_page
                    
                    # Render into placeholder
                    df_show = df_uniq.iloc[start_idx : end_idx].copy()
                    df_show["Sentiment Score (%)"] = df_show["Sentiment Score (%)"].map(lambda x: f"{x:.0f}%")
                    table_placeholder.dataframe(df_show, hide_index=True, use_container_width=True)
                else:
                    # No pagination needed
                    df_show = df_uniq.copy()
                    df_show["Sentiment Score (%)"] = df_show["Sentiment Score (%)"].map(lambda x: f"{x:.0f}%")
                    st.dataframe(df_show, hide_index=True, use_container_width=True)

            with c_uniq1:
                st.subheader(f"Only in {selected_asin}")
                render_unique_list(unique_to_me, selected_asin, "me")
            
            with c_uniq2:
                st.subheader(f"Only in {challenger_asin}")
                render_unique_list(unique_to_challenger, challenger_asin, "them")

            st.markdown("---")
            
            # --- SECTION 3: WEAKNESSES ---
            st.markdown("#### 💔 Top Weaknesses Comparison")
            cw1, cw2 = st.columns(2)
            
            def get_top_issues(asin):
                q = "SELECT COALESCE(am.standard_aspect, rt.aspect) as aspect, COUNT(*) as cnt FROM review_tags rt LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect WHERE rt.parent_asin = ? AND rt.sentiment = 'Negative' GROUP BY 1 ORDER BY 2 DESC LIMIT 5"
                return query_df(q, [asin])

            with cw1:
                st.error(f"Issues: {selected_asin}")
                df_iss = get_top_issues(selected_asin)
                if not df_iss.empty:
                    df_iss.rename(columns={"aspect": "Pain Point", "cnt": "Complaints Count"}, inplace=True) # Renamed
                    st.dataframe(df_iss, hide_index=True, use_container_width=True)
            
            with cw2:
                st.error(f"Issues: {challenger_asin}")
                df_iss_c = get_top_issues(challenger_asin)
                if not df_iss_c.empty:
                    df_iss_c.rename(columns={"aspect": "Pain Point", "cnt": "Complaints Count"}, inplace=True) # Renamed
                    st.dataframe(df_iss_c, hide_index=True, use_container_width=True)

    else:
        st.warning("No other products found in DB to compare.")
