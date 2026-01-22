import streamlit as st
import pandas as pd
import plotly.express as px
from scout_app.ui.common import query_df, query_one, get_weighted_sentiment_data, get_raw_sentiment_data, get_evidence_data, time_it

@st.fragment
@time_it
def render_xray_tab(selected_asin, precalc):
    """
    Renders Tab 2: Customer X-Ray (Sentiment, Ratings, Evidence)
    """
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📊 Aspect Sentiment Analysis")
        
        # --- TOGGLE SWITCH ---
        analysis_mode = st.radio(
            "Analysis Mode:", 
            ["Raw Mentions (Volume)", "Weighted Impact (Star-Adjusted)"],
            horizontal=True,
            help="Raw: Count of mentions. Weighted: Adjusted by Star Rating (what drives 1-star vs 5-star)."
        )

        if "Weighted" in analysis_mode:
            # PRE-CALC WEIGHTED
            if precalc and "sentiment_weighted" in precalc:
                df_w = pd.DataFrame(precalc["sentiment_weighted"])
                st.caption("⚡ Source: Pre-calculated (Instant)")
            else:
                df_w = get_weighted_sentiment_data(selected_asin)
                st.caption("🐢 Source: Live Query (Slow - Cache Miss)")

            if not df_w.empty:
                fig_w = px.bar(
                    df_w,
                    x="score_pct",
                    y="aspect",
                    orientation="h",
                    title="Weighted Sentiment Impact",
                    labels={"score_pct": "Impact Score (0-100)", "aspect": "Feature"},
                    color="score_pct",
                    color_continuous_scale="RdBu", # Red (Low) to Blue (High)
                    height=500
                )
                st.plotly_chart(fig_w, use_container_width=True)
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
                    labels={"value": "Mentions", "variable": "Sentiment"},
                    color_discrete_map={"positive": "#00CC96", "negative": "#EF553B"},
                    height=400
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
                    data = dist_json # Already dict if DuckDB python client handles JSON type
                    
                # Data: {"5": 70, "4": 10...}
                # Ensure keys are sorted 5->1
                sorted_keys = sorted(data.keys(), reverse=True)
                
                df_dist = pd.DataFrame({
                    "Star Rating": [f"{k} Star" for k in sorted_keys],
                    "Percentage": [data[k] for k in sorted_keys]
                })
                
                st.plotly_chart(
                    px.pie(
                        df_dist, 
                        names="Star Rating", 
                        values="Percentage", 
                        hole=0.4, 
                        color_discrete_sequence=px.colors.sequential.RdBu_r, # Reversed for 5 star = Blue
                        title="Market Reality (Population)"
                    ),
                    use_container_width=True
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
                labels={"avg_score": "Average Rating", "month": "Date"} # Renamed
            ),
            use_container_width=True
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
                height=500
            )
        else:
            st.info("No detailed quotes available.")
