import streamlit as st
import pandas as pd
from scout_app.ui.common import query_df, get_precalc_stats


def render_overview_tab(selected_asin, product_brand, dna_data):
    """
    Renders Tab 1: Executive Summary (KPIs, DNA, Pain Points)
    """
    precalc = get_precalc_stats(selected_asin)

    # 1. KPIs
    if precalc and "kpis" in precalc:
        kpis = precalc["kpis"]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Ratings (Real)", f"{kpis.get('total_reviews', 0):,.0f}")
        with c2:
            st.metric("Average Rating (Real)", f"{kpis.get('avg_rating', 0.0):.1f} ⭐")
        with c3:
            st.metric("Variations Tracked", f"{kpis.get('total_variations', 0)}")
        with c4:
            st.metric("Negative Rating %", f"{kpis.get('neg_pct', 0.0):.0f}%", delta_color="inverse")
    else:
        # Fallback to direct query if precalc missing (Join with product_parents for robust metadata)
        kpi_query = """
            SELECT 
                COALESCE(p.real_total_ratings, 0) as total_reviews,
                COALESCE(p.real_average_rating, 0.0) as avg_rating,
                COALESCE(p.variation_count, 0) as total_variations,
                (
                    CAST(json_extract(p.rating_breakdown, '$."1"') AS INT) + 
                    CAST(json_extract(p.rating_breakdown, '$."2"') AS INT)
                ) as negative_pct
            FROM product_parents pp
            LEFT JOIN products p ON pp.parent_asin = p.asin
            WHERE pp.parent_asin = ?
        """
        kpis_df = query_df(kpi_query, [selected_asin])
        if not kpis_df.empty:
            kpis = kpis_df.iloc[0]
            neg_pct = kpis["negative_pct"] if pd.notnull(kpis["negative_pct"]) else 0.0
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total Ratings (Real)", f"{kpis['total_reviews']:,.0f}")
            with c2:
                st.metric("Average Rating (Real)", f"{kpis['avg_rating']:.1f} ⭐")
            with c3:
                st.metric("Variations Tracked", f"{kpis['total_variations']}")
            with c4:
                st.metric("Negative Rating %", f"{neg_pct:.0f}%", delta_color="inverse")
        else:
            st.warning("No KPI data found for this product.")

    st.markdown("---")

    # 2. Product DNA & Priority Actions
    c_dna, c_action = st.columns([1, 1])

    with c_dna:
        st.subheader("🧬 Product DNA")
        with st.container(border=True):
            if not dna_data.empty:
                # Robust metadata extraction: find first non-null value for each field
                def get_first_valid(col_name):
                    if col_name not in dna_data.columns:
                        return "N/A"
                    valid_rows = dna_data[dna_data[col_name].notnull()]
                    return valid_rows[col_name].iloc[0] if not valid_rows.empty else "N/A"

                # Fetch standardized metadata from product_parents
                parent_meta = query_df(
                    "SELECT category, niche FROM product_parents WHERE parent_asin = ?", [selected_asin]
                )

                brand = get_first_valid("brand") if product_brand == "N/A" else product_brand
                material = get_first_valid("material")

                if not parent_meta.empty:
                    category = parent_meta.iloc[0]["category"] or "N/A"
                    niche = parent_meta.iloc[0]["niche"] or get_first_valid("main_niche")
                else:
                    category = "N/A"
                    niche = get_first_valid("main_niche")

                target = (
                    f"{get_first_valid('gender') or ''} {get_first_valid('target_audience') or ''}".strip() or "N/A"
                )

                st.markdown(f"**Brand:** `{brand}`")
                st.markdown(f"**Material:** `{material}`")
                st.markdown(f"**Product Type (Category):** `{category}`")
                st.markdown(f"**Design Theme (Niche):** `{niche}`")

                # --- Variations Detail ---
                st.markdown("**Variations Detected:**")
                df_vars = dna_data[["asin", "main_niche", "size_capacity", "num_pieces"]].copy()
                df_vars.columns = ["ASIN", "Niche (Theme)", "Size/Capacity", "Pcs"]

                st.dataframe(df_vars, height=200, use_container_width=True, hide_index=True)
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
