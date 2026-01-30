import pandas as pd
import plotly.express as px
import streamlit as st

from scout_app.ui.common import (
    get_evidence_data,
    get_precalc_stats,
    get_raw_sentiment_data,
    get_weighted_sentiment_data,
    query_df,
    query_one,
    time_it,
)


@st.fragment
@time_it
def render_xray_tab(selected_asin):
    """
    Renders Tab 2: Customer X-Ray (Sentiment, Ratings, Evidence)
    """
    precalc = get_precalc_stats(selected_asin)
    
    # --- MODE SELECTION (Robust State) ---
    mode_key = f"xray_view_mode_final"
    if mode_key not in st.session_state:
        st.session_state[mode_key] = "📦 Từng sản phẩm"

    view_mode = st.radio(
        "Chế độ hiển thị (Display Mode):",
        ["📦 Từng sản phẩm", "🔥 So sánh thị trường (Top 50)"],
        index=0 if st.session_state[mode_key] == "📦 Từng sản phẩm" else 1,
        horizontal=True,
        help="So sánh sản phẩm hiện tại hoặc xem bức tranh toàn cảnh 50 đối thủ hàng đầu.",
        key="xray_radio_widget"
    )
    # Sync widget back to state
    st.session_state[mode_key] = view_mode

    if "thị trường" in view_mode:
        render_mass_mode(selected_asin)
        return

    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📊 Aspect Sentiment Analysis")

        # --- TOGGLE SWITCH ---
        analysis_mode = st.radio(
            "Chế độ phân tích (Analysis Mode):",
            ["Tần suất (Volume)", "Tác động (Impact Score)"],
            horizontal=True,
            help="""
            **Tần suất (Volume):** Khách hàng nhắc đến cái gì nhiều nhất? (Nhiều chưa chắc đã quan trọng).\n
            **Tác động (Impact):** Yếu tố nào quyết định việc khách cho 1 sao (Tiêu cực) hay 5 sao (Tích cực)?
            """,
        )

        if "Tác động" in analysis_mode:
            # PRE-CALC WEIGHTED
            if precalc and "sentiment_weighted" in precalc:
                df_w = pd.DataFrame(precalc["sentiment_weighted"])
                st.caption("⚡ Source: Pre-calculated (Instant)")
            else:
                # Fallback needed if using old logic? For now, assume stats are updated.
                # If fallback is needed, we should implement get_weighted_sentiment_data to match new logic
                # But to save time, let's rely on re-calc.
                st.warning("Please re-calculate stats for this ASIN to see new Impact Chart.")
                df_w = pd.DataFrame()

            if not df_w.empty:
                # Sort by Total Volume (Impact Magnitude)
                df_w = df_w.sort_values("total_impact_vol", ascending=False)

                # Rename cols for display
                df_disp = df_w.rename(
                    columns={
                        "aspect": "Khía cạnh",
                        "est_positive": "😍 Khen (Est.)",
                        "est_negative": "😠 Chê (Est.)",
                        "net_impact": "⚖️ Net Impact",
                    }
                )

                st.dataframe(
                    df_disp[["Khía cạnh", "😍 Khen (Est.)", "😠 Chê (Est.)", "⚖️ Net Impact"]],
                    use_container_width=True,
                    column_config={
                        "😍 Khen (Est.)": st.column_config.ProgressColumn(
                            "😍 Khen (Est.)",
                            format="%d",
                            min_value=0,
                            max_value=int(df_w["est_positive"].max()),
                            help="Ước tính số khách hàng HÀI LÒNG về khía cạnh này.",
                        ),
                        "😠 Chê (Est.)": st.column_config.ProgressColumn(
                            "😠 Chê (Est.)",
                            format="%d",
                            min_value=0,
                            max_value=int(df_w["est_negative"].max()),
                            help="Ước tính số khách hàng THẤT VỌNG về khía cạnh này.",
                        ),
                        "⚖️ Net Impact": st.column_config.NumberColumn(
                            "⚖️ Net Impact", format="%d", help="Hiệu số (Khen - Chê). Dương = Lợi thế. Âm = Vấn đề."
                        ),
                    },
                    hide_index=True,
                )

                st.info("""
                ℹ️ **Cách tính số liệu ước tính (Estimated Impact):**
                
                Hệ thống sử dụng tỷ lệ xuất hiện trong mẫu review (Sample) để suy rộng ra toàn bộ khách hàng thực tế (Population) theo từng mức sao.
                
                **Ví dụ minh họa:**
                - Sản phẩm có **10,000 rating** (trong đó **5% là 1 sao** = 500 khách).
                - Chúng tôi phân tích mẫu **100 review 1 sao**, thấy có **20 người** chê "Vải rách" (Tỷ lệ 20% trong nhóm 1 sao).
                - 👉 Hệ thống ước tính: Có khoảng **100 khách hàng** (500 x 20%) thực tế đang gặp vấn đề "Vải rách".
                
                *Việc tính toán được thực hiện độc lập cho từng nhóm sao (1-5) rồi tổng hợp lại, giúp bạn hình dung quy mô thật sự của vấn đề trên toàn bộ dữ liệu.*
                """)
            else:
                st.warning("Weighted Analysis unavailable.")

        else:
            # PRE-CALC RAW
            if precalc and "sentiment_raw" in precalc:
                df_aspect = pd.DataFrame(precalc["sentiment_raw"])
                st.caption("⚡ Source: Pre-calculated (Instant)")
            else:
                df_aspect = get_raw_sentiment_data(selected_asin)
                st.caption("🐢 Source: Live Query (Slow - Cache Miss)")

            if not df_aspect.empty:
                fig_aspect = px.bar(
                    df_aspect,
                    y="aspect",
                    x=["positive", "negative"],
                    orientation="h",
                    title="Tần suất nhắc đến (Review Volume)",
                    labels={"value": "Số lần nhắc (Mentions)", "variable": "Cảm xúc", "aspect": "Khía cạnh"},
                    color_discrete_map={"positive": "#00CC96", "negative": "#EF553B"},
                    height=400,
                )
                st.plotly_chart(fig_aspect, use_container_width=True)
            else:
                st.info("Not enough data for Aspect Analysis.")

    with c2:
        st.subheader("⚠️ Real Rating Distribution")
        # Fetch JSON breakdown from Products
        dist_json = query_one("SELECT rating_breakdown FROM products WHERE asin = ?", [selected_asin])

        if dist_json:
            import json

            try:
                # Handle DuckDB returning dict or str
                if isinstance(dist_json, str):
                    data = json.loads(dist_json)
                else:
                    data = dist_json  # Already dict if DuckDB python client handles JSON type

                # Data: {"5": 70, "4": 10...}
                # Ensure keys are sorted 5->1
                sorted_keys = sorted(data.keys(), reverse=True)

                df_dist = pd.DataFrame(
                    {"Star Rating": [f"{k} Star" for k in sorted_keys], "Percentage": [data[k] for k in sorted_keys]}
                )

                st.plotly_chart(
                    px.pie(
                        df_dist,
                        names="Star Rating",
                        values="Percentage",
                        hole=0.4,
                        color_discrete_sequence=px.colors.sequential.RdBu_r,  # Reversed for 5 star = Blue
                        title="Market Reality (Population)",
                    ),
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"Could not parse rating distribution: {e}")
        else:
            st.info("No rating breakdown available.")

    st.markdown("---")
    st.subheader("📈 Rating Trend over Time")
    if precalc and "rating_trend" in precalc:
        df_trend = pd.DataFrame(precalc["rating_trend"])
    else:
        df_trend = query_df(
            "SELECT DATE_TRUNC('month', review_date) as month, AVG(rating_score) as avg_score FROM reviews WHERE parent_asin = ? GROUP BY 1 ORDER BY 1",
            [selected_asin],
        )

    if not df_trend.empty:
        st.plotly_chart(
            px.line(
                df_trend,
                x="month",
                y="avg_score",
                markers=True,
                labels={"avg_score": "Average Rating", "month": "Date"},  # Renamed
            ),
            use_container_width=True,
        )

    # --- Evidence (Quotes) ---
    st.write("---")
    with st.expander("🔍 View Evidence (Quotes)"):
        df_ev = get_evidence_data(selected_asin)
        if df_ev is not None and not df_ev.empty:
            st.dataframe(
                df_ev,
                use_container_width=True,
                column_config={
                    "Aspect (Status)": st.column_config.TextColumn("Aspect (Status)"),
                    "Evidence Quote": st.column_config.TextColumn("Quote", width="large"),
                },
                height=500,
            )
        else:
            st.info("No detailed quotes available.")


def render_mass_mode(selected_asin):
    st.subheader("🔥 Market Sentiment Heatmap (Mass Mode)")

    # --- 1. SELECTION LOGIC ---
    base_info = query_df("""
        SELECT p.brand, p.title, p.product_line, p.real_total_ratings, pp.category, pp.niche 
        FROM products p 
        LEFT JOIN product_parents pp ON p.asin = pp.parent_asin
        WHERE p.asin = ?
    """, [selected_asin])
    
    my_line = base_info.iloc[0]['product_line'] if not base_info.empty else None
    my_ratings = base_info.iloc[0]['real_total_ratings'] or 0
    my_cat = base_info.iloc[0]['category'] if not base_info.empty else None
    my_niche = base_info.iloc[0]['niche'] if not base_info.empty else None

    # Get all potential candidates with ROBUST BRAND fetching
    all_parents = query_df("""
        SELECT 
            p.parent_asin as asin, 
            MAX(COALESCE(pp.brand, p.brand)) as brand, 
            ANY_VALUE(COALESCE(pp.title, p.title)) as title,
            ANY_VALUE(pp.category) as category,
            ANY_VALUE(pp.niche) as niche
        FROM products p 
        LEFT JOIN product_parents pp ON p.parent_asin = pp.parent_asin
        GROUP BY 1 
        ORDER BY MAX(p.real_total_ratings) DESC
    """)
    parent_list = all_parents['asin'].tolist()
    parent_map = all_parents.set_index('asin')['brand'].to_dict()

    st.markdown("##### 🛠️ Bộ lọc thị trường")
    f_c1, f_c2 = st.columns(2)
    with f_c1:
        unique_cats = sorted([c for c in all_parents['category'].dropna().unique() if c])
        selected_cat = st.selectbox("Lọc theo Category:", ["Tất cả"] + unique_cats, index=unique_cats.index(my_cat) + 1 if my_cat in unique_cats else 0)
    
    with f_c2:
        # Filter niches based on category
        niche_df = all_parents if selected_cat == "Tất cả" else all_parents[all_parents['category'] == selected_cat]
        unique_niches = sorted([n for n in niche_df['niche'].dropna().unique() if n])
        selected_niche = st.selectbox("Lọc theo Niche:", ["Tất cả"] + unique_niches, index=unique_niches.index(my_niche) + 1 if my_niche in unique_niches else 0)

    # Filter candidates based on selection
    filtered_parents = all_parents.copy()
    if selected_cat != "Tất cả":
        filtered_parents = filtered_parents[filtered_parents['category'] == selected_cat]
    if selected_niche != "Tất cả":
        filtered_parents = filtered_parents[filtered_parents['niche'] == selected_niche]

    auto_candidates = filtered_parents[filtered_parents['asin'] != selected_asin]['asin'].tolist()[:15]

    st.markdown("##### 🤝 Tùy chỉnh danh sách so sánh")
    selected_list = st.multiselect(
        "Chọn các ASIN đối thủ để đưa vào bản đồ nhiệt:",
        options=parent_list,
        default=[selected_asin] + [c for c in auto_candidates if c in parent_list],
        format_func=lambda x: f"{x} - {str(parent_map.get(x, 'Unknown Brand'))[:15]}...",
        key=f"mass_sel_list_v3_{selected_asin}"
    )

    if len(selected_list) < 2:
        st.info("Vui lòng chọn ít nhất 2 sản phẩm để so sánh.")
        return

    # --- 2. FETCH DATA IN BATCH ---
    sql = """
        SELECT p.asin, COALESCE(pp.brand, p.brand, 'Unknown') as brand, COALESCE(pp.title, p.title) as title, ps.metrics_json, p.real_total_ratings 
        FROM products p 
        JOIN product_stats ps ON p.asin = ps.asin 
        LEFT JOIN product_parents pp ON p.asin = pp.parent_asin
        WHERE p.asin IN ({})
    """.format(','.join(['?']*len(selected_list)))
    df_batch = query_df(sql, selected_list)

    # --- 3. PROCESS HEATMAP DATA ---
    import json
    heatmap_data = []
    
    for _, row in df_batch.iterrows():
        try:
            m = json.loads(row["metrics_json"]) if isinstance(row["metrics_json"], str) else row["metrics_json"]
            brand_clean = row['brand'] if row['brand'] and row['brand'] != 'None' else 'Unknown'
            label = f"{brand_clean[:10]} ({row['asin']})"
            real_total = row['real_total_ratings'] or 0
            
            for item in m.get("sentiment_weighted", []):
                score = item["est_positive"] # Use Volume instead of %
                heatmap_data.append({
                    "Sản phẩm": label,
                    "ASIN": row['asin'],
                    "Khía cạnh": item["aspect"],
                    "Khách khen (Est)": score,
                    "Tổng Rating": real_total
                })
        except: continue

    if not heatmap_data:
        st.warning("Dữ liệu cảm xúc chưa đủ.")
        return

    df_hm = pd.DataFrame(heatmap_data)
    df_pivot = df_hm.pivot(index="Khía cạnh", columns="Sản phẩm", values="Khách khen (Est)")
    
    # FIX: Fill NaN with 0 for missing aspects (Clean Heatmap)
    df_pivot = df_pivot.fillna(0)
    
    # Sort aspects by total volume of positive feedback across all products
    df_pivot = df_pivot.reindex(df_pivot.sum(axis=1).sort_values(ascending=False).index)

    # Create a mapping for total ratings to use in hover
    rating_map = df_hm.set_index("Sản phẩm")["Tổng Rating"].to_dict()
    hover_ratings = [[rating_map.get(col, 0) for col in df_pivot.columns] for _ in range(len(df_pivot))]

    # --- 4. RENDER HEATMAP ---
    fig = px.imshow(
        df_pivot,
        labels=dict(y="Khía cạnh", x="Sản phẩm", color="Khách khen (Est)"),
        color_continuous_scale="YlGnBu", # Yellow-Green-Blue for density/volume
        aspect="auto",
        title="Market Strength Map (Weighted Volume)",
    )
    
    # Add Grid Lines (using gaps)
    fig.update_traces(
        xgap=1, # 1 pixel gap between columns
        ygap=1, # 1 pixel gap between rows
        customdata=hover_ratings,
        hovertemplate="<b>%{x}</b><br>Khía cạnh: %{y}<br>Khách khen: %{z:,.0f} người<br>Tổng Rating: %{customdata:,.0f}<extra></extra>"
    )
    fig.update_layout(height=max(500, len(df_pivot) * 25))
    st.plotly_chart(fig, use_container_width=True)

    # --- 5. QUICK DRILL-DOWN (INTERACTIVE) ---
    st.markdown("##### 🚀 Quick Drill-down")
    st.caption("Click vào một dòng để chuyển sang xem chi tiết sản phẩm đó.")
    
    df_summary = df_batch[['brand', 'asin', 'real_total_ratings']].copy()
    df_summary.columns = ['Brand', 'ASIN', 'Reviews']
    df_summary['Brand'] = df_summary['Brand'].fillna('Unknown')
    
    event = st.dataframe(
        df_summary,
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True,
        use_container_width=True,
        key="jump_table_market"
    )

    if event and event.get("selection", {}).get("rows"):
        idx = event["selection"]["rows"][0]
        if idx < len(df_summary):
            target_asin = df_summary.iloc[idx]['ASIN']
            # Update Main Selector (Sidebar will pick this up on rerun)
            st.session_state["main_asin_selector"] = target_asin
            # Switch back to Single View
            st.session_state["xray_view_mode_final"] = "📦 Từng sản phẩm"
            st.rerun()
