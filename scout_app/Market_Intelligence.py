import os
import re
import sys
import uuid
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

import streamlit.components.v1 as components # Added for JS Injection

# Add root to sys.path to find core
sys.path.append(str(Path(__file__).resolve().parent.parent))
from core.auth import AuthManager
from core.config import Settings

# --- Config ---
st.set_page_config(page_title="Product Intelligence", page_icon="🕵️", layout="wide")

# --- AUTHENTICATION GATEKEEPER ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Ensure keys exist to avoid KeyError
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

if not st.session_state["authenticated"]:
    # Login Page Layout
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("# 🔐 Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                auth = AuthManager()
                user = auth.verify_user(username, password)
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user_id"] = user["user_id"]
                    st.session_state["username"] = user["username"]
                    st.session_state["role"] = user["role"]
                    st.success(f"Welcome back, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
    st.stop()  # Stop execution if not logged in

# --- MAIN APP (Authenticated) ---
current_user_id = st.session_state["user_id"]
current_username = st.session_state["username"]


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
    Smart Request Handler V2
    """
    db_path = get_db_path()
    final_asin = asin_input
    system_note = ""
    is_unknown = False

    try:
        with duckdb.connect(db_path, read_only=True) as conn:
            # 1. Lookup Product Logic
            row = conn.execute(
                "SELECT parent_asin FROM products WHERE asin = ? OR parent_asin = ? LIMIT 1", [asin_input, asin_input]
            ).fetchone()

            if row:
                mapped_parent = row[0]
                if mapped_parent and mapped_parent != asin_input:
                    final_asin = mapped_parent
                    system_note = f"[Auto-Map] Child {asin_input} -> Parent {final_asin}"
            else:
                is_unknown = True
                system_note = "[Unknown ASIN] Not in Product DB. Admin verify Parent."

            # 2. Check Existing Data (Reviews)
            rev_stats = conn.execute(
                "SELECT COUNT(*), MAX(review_date) FROM reviews WHERE parent_asin = ?", [final_asin]
            ).fetchone()
            has_data = rev_stats[0] > 0
            last_date = rev_stats[1]

            if has_data and not force_update:
                return (
                    False,
                    f"🛑 Đã có dữ liệu! Tìm thấy {rev_stats[0]} reviews (Mới nhất: {last_date}). Nếu cần cập nhật, hãy tick 'Force Update'.",
                )

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
        VALUES (?, ?, 'PENDING_APPROVAL', ?, ?)
    """
    try:
        with duckdb.connect(db_path, read_only=False) as conn:
            conn.execute(sql, [req_id, final_asin, current_user_id, full_note])

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
st.sidebar.title("🕵️ Product Intelligence")
st.sidebar.caption(f"Logged in as: **{current_username}**")
if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()

st.sidebar.markdown("---")

# Request Form
with st.sidebar.expander("➕ Request New ASIN"):
    with st.form("req_form"):
        new_asin = st.text_input("Enter ASIN:", placeholder="B0...")
        req_note = st.text_input("Note:", placeholder="Why prioritize this?")
        force_chk = st.checkbox("Force Update (If exists)")

        submitted = st.form_submit_button("Submit Request")
        if submitted:
            if not new_asin or not new_asin.startswith("B0"):
                st.error("Invalid ASIN (Must start with 'B0')")
            else:
                ok, msg = request_new_asin(new_asin.strip(), req_note, force_chk)
                if ok:
                    if "⚠️" in msg:
                        st.warning(msg)  # Yellow for Unknown/Warning
                    else:
                        st.success(msg)  # Green for Auto-Correct/Success
                else:
                    st.warning(msg)  # Yellow for Error/Stop

    # Show History
    st.caption("🕒 Recent Requests")
    try:
        hist_df = query_df(
            "SELECT asin, status FROM scrape_queue WHERE requested_by = ? ORDER BY created_at DESC LIMIT 5",
            [current_user_id],
        )
        if not hist_df.empty:
            st.dataframe(hist_df, use_container_width=True, hide_index=True)
    except:
        pass

st.sidebar.markdown("---")

# Load ASIN List
df_asins = query_df("""
    SELECT 
        asin as parent_asin, 
        COALESCE(real_total_ratings, 0) as review_count, 
        COALESCE(real_average_rating, 0.0) as avg_rating
    FROM products 
    ORDER BY review_count DESC, parent_asin ASC
"""
)

if df_asins.empty:
    st.warning("No data found. Please ingest some reviews first.")
else:
    selected_asin = st.sidebar.selectbox(
        "Select Product (ASIN)",
        df_asins["parent_asin"].tolist(),
        format_func=lambda x: f"{x} (⭐{df_asins[df_asins['parent_asin'] == x]['avg_rating'].values[0]})",
    )

    if selected_asin:
        # --- Handle ASIN Change Logic (With History Swap) ---
        if "current_asin" not in st.session_state:
            st.session_state["current_asin"] = selected_asin
        
        # Init Global History Vault
        if "chat_histories" not in st.session_state:
            st.session_state["chat_histories"] = {}

        # If ASIN changed, Swap History & Reset Detective
        if st.session_state["current_asin"] != selected_asin:
            old_asin = st.session_state["current_asin"]
            
            # 1. Save OLD history to Vault
            st.session_state["chat_histories"][old_asin] = st.session_state.messages
            
            # 2. Load NEW history from Vault (or empty if first time)
            st.session_state.messages = st.session_state["chat_histories"].get(selected_asin, [])
            
            # 3. Reset Agent (Crucial: Agent must be reborn with new ASIN context)
            st.session_state.detective = None 
            if "detective" in st.session_state:
                del st.session_state["detective"]
            
            # 4. Update Pointer & Rerun
            st.session_state["current_asin"] = selected_asin
            st.rerun()

        # --- Common Data Fetching ---
        dna_query = """
            SELECT 
                title, material, main_niche, gender, design_type, 
                target_audience, size_capacity, product_line, 
                num_pieces, pack, brand, image_url
            FROM products 
            WHERE asin = ? OR parent_asin = ? 
            LIMIT 1
        """
        dna = query_df(dna_query, [selected_asin, selected_asin])

        # Product Title Header
        product_display_title = selected_asin
        product_brand = "N/A"
        if not dna.empty:
            d = dna.iloc[0]
            product_display_title = d['title'] if d['title'] else selected_asin
            product_brand = d['brand'] if d['brand'] else "N/A"

        st.title(f"{product_brand} - {product_display_title[:50]}...")
        if len(product_display_title) > 50:
            st.caption(product_display_title)

        # --- TABS LAYOUT ---
        # Cleanup Scroll Button Logic (Run on every rerun to clear button if switching tabs)
        cleanup_js = """
        <script>
            var oldBtn = window.parent.document.getElementById('scrollBtn');
            if (oldBtn) { oldBtn.remove(); }
            var oldBtnV2 = window.parent.document.getElementById('scrollBtnV2');
            if (oldBtnV2) { oldBtnV2.remove(); }
        </script>
        """
        components.html(cleanup_js, height=0)

        tab_overview, tab_deep, tab_battle, tab_strategy = st.tabs([
            "🏠 Executive Summary", 
            "🔬 Customer X-Ray", 
            "⚔️ Market Showdown", 
            "🧠 Strategy Hub"
        ])

        # =================================================================================
        # TAB 1: EXECUTIVE SUMMARY
        # =================================================================================
        with tab_overview:
            # 1. KPIs
            # Fetch Metadata directly from Products table
            # DuckDB JSON extraction: CAST(json_extract(...) AS INT)
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
                # Fallback if json is null
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
                    if not dna.empty:
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

        # =================================================================================
        # TAB 2: CUSTOMER X-RAY (DEEP DIVE)
        # =================================================================================
        with tab_deep:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader("📊 Aspect Sentiment Analysis")
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
                        "Evidence Quote": st.column_config.TextColumn("Quote", width="large"),
                    },
                )

        # =================================================================================
        # TAB 3: MARKET SHOWDOWN
        # =================================================================================
        with tab_battle:
            st.subheader("⚔️ Head-to-Head Comparison")
            
            ai_asins_df = query_df(
                "SELECT DISTINCT parent_asin FROM review_tags WHERE parent_asin != ?", [selected_asin]
            )
            ai_asins = ai_asins_df["parent_asin"].tolist() if not ai_asins_df.empty else []

            if ai_asins:
                c_sel, c_blank = st.columns([1, 2])
                with c_sel:
                    challenger_asin = st.selectbox("Select Challenger:", ai_asins)
                
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
                            # We need to use session state or placeholder if we want controls below to affect table above
                            # But standard Streamlit flow: Input -> Render.
                            # So to have Input BELOW Render, we need `st.empty()` placeholder.
                            
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

        # =================================================================================
        # TAB 4: STRATEGY HUB (AI AGENT)
        # =================================================================================
        with tab_strategy:
            st.header("🧠 Strategy Hub")
            st.caption("Coordinate with your AI Detective to build winning strategies.")

            try:
                from scout_app.core.detective import DetectiveAgent
            except:
                from core.detective import DetectiveAgent

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

            st.markdown("---")
            
            # --- Evidence Locker (Raw Reviews) ---
            with st.expander("📂 Evidence Locker (Raw Reviews)"):
                st.caption("Direct access to customer feedback for verification.")
                show_bad = st.checkbox("Show Negative Only (<= 3 stars)", value=True)
                
                ev_sql = "SELECT review_date, rating_score, title, text FROM reviews WHERE parent_asin = ?"
                if show_bad:
                    ev_sql += " AND rating_score <= 3"
                ev_sql += " ORDER BY review_date DESC LIMIT 50"
                
                df_ev = query_df(ev_sql, [selected_asin])
                if not df_ev.empty:
                    # Rename Columns
                    df_ev.rename(columns={"review_date": "Date", "rating_score": "Stars", "title": "Title", "text": "Review Content"}, inplace=True)
                st.dataframe(df_ev, use_container_width=True)