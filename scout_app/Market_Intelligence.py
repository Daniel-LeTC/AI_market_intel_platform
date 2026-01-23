import sys
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# Add root and current dir to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR.parent))

from core.auth import AuthManager
from scout_app.ui.common import query_df, request_new_asin, get_precalc_stats
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
        selection = st.session_state["jump_table_market"].get("selection", {}).get("rows")
        if selection:
            # We need the ASIN list to find what was clicked
            # Since we are in main(), we can fetch the list now
            df_temp = query_df("SELECT parent_asin FROM products WHERE asin = parent_asin ORDER BY parent_asin ASC")
            if not df_temp.empty:
                idx = selection[0]
                # In Mass Mode, the list might be different, but for now we trust 
                # the index if we use the same sorting. 
                # BETTER: The Jump Interceptor should store the ASIN directly if possible.
                # However, for simplicity, let's just use the index against the master list for now.
                asin_list = df_temp["parent_asin"].tolist()
                if idx < len(asin_list):
                    st.session_state["main_asin_selector"] = asin_list[idx]
            
            # Clear selection to prevent infinite loop
            st.session_state["jump_table_market"] = {"selection": {"rows": [], "columns": []}}

    # --- AUTHENTICATION GATEKEEPER ---
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
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
                        st.session_state.update({
                            "authenticated": True, "user_id": user["user_id"],
                            "username": user["username"], "role": user["role"]
                        })
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
                new_asin = st.text_input("Enter ASIN:", placeholder="B0...")
                req_note = st.text_input("Note:")
                force_chk = st.checkbox("Force Update")
                if st.form_submit_button("Submit"):
                    ok, msg = request_new_asin(new_asin.strip(), req_note, force_chk, user_id=current_user_id)
                    st.success(msg) if ok else st.warning(msg)

        st.markdown("---")
        # Load ASIN List (True Parents Only)
        df_asins = query_df("""
            SELECT 
                parent_asin, 
                real_average_rating as avg_rating 
            FROM products 
            WHERE asin = parent_asin
            ORDER BY parent_asin ASC
        """)
        
        if df_asins.empty:
            st.error("No data in DB.")
            return

        selected_asin = st.sidebar.selectbox(
            "Select Product (ASIN)",
            df_asins["parent_asin"].tolist(),
            format_func=lambda x: f"{x} (⭐{df_asins[df_asins['parent_asin'] == x]['avg_rating'].values[0]})",
            key="main_asin_selector"
        )

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
            if "detective" in st.session_state: del st.session_state["detective"]
            st.rerun()

        # Fetch DNA (Full Family)
        dna = query_df("SELECT * FROM products WHERE parent_asin = ?", [selected_asin])
        
        # Determine Display Title & Brand from the Parent row specifically
        parent_row = dna[dna['asin'] == selected_asin]
        if not parent_row.empty:
            title = parent_row.iloc[0]['title'] or selected_asin
            brand = parent_row.iloc[0]['brand'] or "N/A"
        else:
            # Fallback to first available if parent row is weirdly missing
            title = dna.iloc[0]['title'] if not dna.empty else selected_asin
            brand = dna.iloc[0]['brand'] if not dna.empty else "N/A"

        st.title(f"{brand} - {title[:60]}...")

        tab_overview, tab_deep, tab_battle, tab_strategy = st.tabs([
            "🏠 Executive Summary", "🔬 Customer X-Ray", "⚔️ Market Showdown", "🧠 Strategy Hub"
        ])

        with tab_overview: render_overview_tab(selected_asin, brand, dna)
        with tab_deep: render_xray_tab(selected_asin)
        with tab_battle: render_showdown_tab(selected_asin)
        with tab_strategy: render_strategy_tab(selected_asin, current_user_id)

if __name__ == "__main__":
    main()