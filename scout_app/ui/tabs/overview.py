import streamlit as st
import pandas as pd
from scout_app.ui.common import query_df

def render_overview_tab(selected_asin, product_brand, dna_data, precalc):
    """
    Renders Tab 1: Executive Summary (KPIs, DNA, Pain Points)
    """
    
    # 1. KPIs
    if precalc and "kpis" in precalc:
        kpis = precalc["kpis"]
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Ratings (Real)", f"{kpis.get('total_reviews', 0):,.0f}")
        with c2: st.metric("Average Rating (Real)", f"{kpis.get('avg_rating', 0.0):.1f} ⭐")
        with c3: st.metric("Variations Tracked", f"{kpis.get('total_variations', 0)}") 
        with c4: st.metric("Negative Rating %", f"{kpis.get('neg_pct', 0.0):.0f}%", delta_color="inverse")
    else:
        # Fallback to direct query if precalc missing
        kpi_query = """
            SELECT 
                real_total_ratings as total_reviews,
                real_average_rating as avg_rating,
                variation_count as total_variations,
                (
                    CAST(json_extract(rating_breakdown, '$."1"') AS INT) + 
                    CAST(json_extract(rating_breakdown, '$."2"') AS INT)
                ) as negative_pct
            FROM products
            WHERE asin = ?
        """
        kpis_df = query_df(kpi_query, [selected_asin])
        if not kpis_df.empty:
            kpis = kpis_df.iloc[0]
            neg_pct = kpis['negative_pct'] if pd.notnull(kpis['negative_pct']) else 0.0
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Total Ratings (Real)", f"{kpis['total_reviews']:,.0f}")
            with c2: st.metric("Average Rating (Real)", f"{kpis['avg_rating']:.1f} ⭐")
            with c3: st.metric("Variations Tracked", f"{kpis['total_variations']}") 
            with c4: st.metric("Negative Rating %", f"{neg_pct:.0f}%", delta_color="inverse")

    st.markdown("---")

    # 2. Product DNA & Priority Actions
    c_dna, c_action = st.columns([1, 1])
    
    with c_dna:
        st.subheader("🧬 Product DNA")
        with st.container(border=True):
            if not dna_data.empty:
                d = dna_data.iloc[0]
                st.markdown(f"**Brand:** `{product_brand}`")
                st.markdown(f"**Material:** `{d['material'] or 'N/A'}`")
                st.markdown(f"**Niche:** `{d['main_niche'] or 'N/A'}`")
                st.markdown(f"**Target:** `{d['gender'] or ''} {d['target_audience'] or 'N/A'}`")
                st.markdown(f"**Specs:** `{d['size_capacity'] or 'N/A'}` | `{d['num_pieces'] or d['pack'] or 'N/A'} pcs`")
            else:
                st.info("Metadata not found in DB.")

    with c_action:
        st.subheader("🚨 Priority Actions (Top Pain Points)")
        with st.container(border=True):
            pain_query = """
                SELECT 
                    COALESCE(am.standard_aspect, rt.aspect) as aspect,
                    COUNT(*) as count
                FROM review_tags rt
                LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
                WHERE rt.parent_asin = ? AND rt.sentiment = 'Negative'
                GROUP BY 1
                ORDER BY 2 DESC
                LIMIT 3
            """
            df_pain = query_df(pain_query, [selected_asin])
            if not df_pain.empty:
                for i, row in df_pain.iterrows():
                    st.error(f"**Fix '{row['aspect']}'**: {row['count']} complaints detected.")
            else:
                st.success("✅ No critical pain points detected yet.")
