import sys
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import time

# Add root and current dir to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR.parent))

from core.auth import AuthManager
from scout_app.ui.common import (
    query_df,
    request_new_asin,
    get_precalc_stats,
    get_active_asin_list,
    get_all_product_metadata,
)
from scout_app.ui.tabs.overview import render_overview_tab
from scout_app.ui.tabs.xray import render_xray_tab
from scout_app.ui.tabs.showdown import render_showdown_tab
from scout_app.ui.tabs.strategy import render_strategy_tab

# --- Config ---
st.set_page_config(page_title="Product Intelligence", page_icon="🕵️", layout="wide")


def main():
    # --- JUMP INTERCEPTOR (Bypass Streamlit State Conflict) ---
    # This must run BEFORE sidebar instantiation
    if "jump_table_market" in st.session_state:
        pass

    # --- AUTHENTICATION GATEKEEPER ---
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        # ... (login form remains same)
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
                        st.session_state.update(
                            {
                                "authenticated": True,
                                "user_id": user["user_id"],
                                "username": user["username"],
                                "role": user["role"],
                            }
                        )
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
        return

    current_user_id = st.session_state["user_id"]
    current_username = st.session_state["username"]

    # --- SIDEBAR ---
    with st.sidebar:
        st.caption(f"Logged in as: **{current_username}**")
        if st.sidebar.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

        st.markdown("---")
        with st.sidebar.expander("➕ Request New ASIN"):
            with st.form("req_form"):
                new_asin_input = st.text_input("Enter ASIN:", placeholder="B0...")
                req_note = st.text_input("Note:")
                force_chk = st.checkbox("Force Update")
                if st.form_submit_button("Submit"):
                    new_asin_clean = new_asin_input.strip()
                    ok, msg = request_new_asin(new_asin_clean, req_note, force_chk, user_id=current_user_id)
                    if ok:
                        st.success(msg)
                    else:
                        # SMART SWITCH: If data exists, navigate user to it
                        if "Đã có dữ liệu" in msg:
                            df_check = query_df(
                                "SELECT parent_asin FROM products WHERE asin = ? OR parent_asin = ? LIMIT 1",
                                [new_asin_clean, new_asin_clean],
                            )
                            if not df_check.empty:
                                parent_asin = df_check.iloc[0]["parent_asin"]
                                # 1. Invalidate Cache
                                st.session_state["last_db_update"] = time.time()
                                # 2. Set State for Redirection
                                st.session_state["main_asin_selector"] = parent_asin
                                st.session_state["current_asin"] = parent_asin
                                st.success(f"🎯 Đã tìm thấy! Đang chuyển tới ASIN Cha: {parent_asin}")
                                time.sleep(2)
                                st.rerun()
                        st.warning(msg)

        # --- Sidebar Status Table ---
        st.caption("🔍 Request Status")
        df_status = query_df(
            """
            SELECT asin, status, created_at 
            FROM scrape_queue 
            WHERE requested_by = ? 
            ORDER BY created_at DESC 
            LIMIT 5
        """,
            [current_user_id],
        )

        if not df_status.empty:
            # Color coding or simple display
            st.dataframe(
                df_status,
                column_config={
                    "asin": st.column_config.TextColumn("ASIN"),
                    "status": st.column_config.TextColumn("Status"),
                    "created_at": st.column_config.DatetimeColumn("Date", format="DD/MM HH:mm"),
                },
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No active requests.")

        st.markdown("---")
        # --- SMART SIDEBAR 2.0 ---
        cache_key = st.session_state.get("last_db_update", 0)
        df_meta = get_all_product_metadata(cache_key=cache_key)

        if df_meta.empty:
            st.error("No product data found in DB.")
            return

        st.subheader("🎯 Product Explorer")

        # 1. Category Filter
        all_cats = sorted([c for c in df_meta["category"].dropna().unique() if c])
        sel_cat = st.sidebar.selectbox("Category:", ["All"] + all_cats)

        # 2. Niche Filter (Filtered by Category)
        df_filtered = df_meta.copy()
        if sel_cat != "All":
            df_filtered = df_filtered[df_filtered["category"] == sel_cat]

        all_niches = sorted([n for n in df_filtered["niche"].dropna().unique() if n])
        sel_niche = st.sidebar.selectbox("Niche:", ["All"] + all_niches)

        if sel_niche != "All":
            df_filtered = df_filtered[df_filtered["niche"] == sel_niche]

        # 3. Search Box
        search_term = st.sidebar.text_input("🔍 Search Brand/Title/ASIN:", placeholder="e.g. B0...")
        if search_term:
            search_term = search_term.lower()
            df_filtered = df_filtered[
                df_filtered["parent_asin"].str.lower().str.contains(search_term, na=False)
                | df_filtered["variation_pool"].str.lower().str.contains(search_term, na=False)
                | df_filtered["title"].str.lower().str.contains(search_term, na=False)
                | df_filtered["brand"].str.lower().str.contains(search_term, na=False)
            ]

        # 4. Result Selection (Interactive Table)
        if df_filtered.empty:
            st.sidebar.warning("No matches found.")
            selected_asin = st.session_state.get("main_asin_selector")
        else:
            st.sidebar.markdown(f"**Matches ({len(df_filtered)}):**")

            # Prepare display DF
            display_df = df_filtered[["brand", "parent_asin", "title"]].copy()
            display_df.columns = ["Brand", "ASIN", "Product Name"]

            # Find index of currently selected ASIN to highlight
            current_asin = st.session_state.get("main_asin_selector")
            pre_selected_rows = []
            if current_asin in display_df["ASIN"].values:
                idx = display_df[display_df["ASIN"] == current_asin].index[0]
                # In streamlit dataframe, indices might be different if we filtered,
                # but we'll use the position in the current display_df
                pos = list(display_df["ASIN"]).index(current_asin)
                pre_selected_rows = [pos]

            event = st.sidebar.dataframe(
                display_df,
                on_select="rerun",
                selection_mode="single-row",
                hide_index=True,
                use_container_width=True,
                key="sidebar_selection_table",
            )

            # Logic to update selected_asin from table click
            if event and event.get("selection", {}).get("rows"):
                row_idx = event["selection"]["rows"][0]
                selected_asin = display_df.iloc[row_idx]["ASIN"]
                # Update the main selector key to stay in sync
                st.session_state["main_asin_selector"] = selected_asin
            else:
                selected_asin = st.session_state.get("main_asin_selector")

            # Fallback: if current selection is not in list but we need one
            if not selected_asin and not display_df.empty:
                selected_asin = display_df.iloc[0]["ASIN"]

    if selected_asin:
        # ASIN Change History Swap
        if "current_asin" not in st.session_state:
            st.session_state["current_asin"] = selected_asin

        if "chat_histories" not in st.session_state:
            st.session_state["chat_histories"] = {}

        if st.session_state["current_asin"] != selected_asin:
            st.session_state["chat_histories"][st.session_state["current_asin"]] = st.session_state.get("messages", [])
            st.session_state.messages = st.session_state["chat_histories"].get(selected_asin, [])
            st.session_state["current_asin"] = selected_asin
            # Detective reset logic handled inside Strategy tab or here
            if "detective" in st.session_state:
                del st.session_state["detective"]
            st.rerun()

        # Fetch DNA (Full Family)
        dna = query_df("SELECT * FROM products WHERE parent_asin = ?", [selected_asin])

        # Determine Display Title & Brand from the Parent row specifically
        parent_row = dna[dna["asin"] == selected_asin]
        if not parent_row.empty:
            title = parent_row.iloc[0]["title"] or selected_asin
            brand = parent_row.iloc[0]["brand"] or "N/A"
        else:
            # Fallback to first available if parent row is weirdly missing
            title = dna.iloc[0]["title"] if not dna.empty else selected_asin
            brand = dna.iloc[0]["brand"] if not dna.empty else "N/A"

        st.title(f"{brand} - {title[:60]}...")

        tab_overview, tab_deep, tab_battle, tab_strategy = st.tabs(
            ["🏠 Executive Summary", "🔬 Customer X-Ray", "⚔️ Market Showdown", "🧠 Strategy Hub"]
        )

        with tab_overview:
            render_overview_tab(selected_asin, brand, dna)
        with tab_deep:
            render_xray_tab(selected_asin)
        with tab_battle:
            render_showdown_tab(selected_asin)
        with tab_strategy:
            render_strategy_tab(selected_asin, current_user_id)


if __name__ == "__main__":
    main()
