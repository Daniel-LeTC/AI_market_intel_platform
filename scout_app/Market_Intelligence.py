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

# --- AUTHENTICATION GATEKEEPER ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Ensure keys exist
for key in ["user_id", "role", "username"]:
    if key not in st.session_state:
        st.session_state[key] = None

# --- AUTHENTICATION GATEKEEPER ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Ensure keys exist
for key in ["user_id", "role", "username"]:
    if key not in st.session_state:
        st.session_state[key] = None

# Create a placeholder for the login form
login_placeholder = st.empty()

# If NOT authenticated, render the login form inside the placeholder
if not st.session_state["authenticated"]:
    # Login Page Layout
    with login_placeholder.container():
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
                        # Do NOT rerun. Just clear the placeholder.
                        login_placeholder.empty()
                    else:
                        st.error("Invalid username or password.")
                        st.stop() # Stop here if failed
                else:
                    st.stop() # Stop here if waiting for input

# --- MAIN APP (Authenticated) ---
# If we reach here, it means st.session_state["authenticated"] is True
# (Either from previous session OR just set above)

# Double check to clear placeholder if it was set (e.g. strict refresh)
login_placeholder.empty()

current_user_id = st.session_state["user_id"]
current_username = st.session_state["username"]

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
                ok, msg = request_new_asin(new_asin.strip(), req_note, force_chk, user_id=current_user_id)
                if ok:
                    if "⚠️" in msg:
                        st.warning(msg)
                    else:
                        st.success(msg)
                else:
                    st.warning(msg)

    # Show History
    st.caption("🕒 Recent Requests")
    
    @st.cache_data(ttl=30)
    def get_recent_requests(uid):
        try:
            return query_df(
                "SELECT asin, status FROM scrape_queue WHERE requested_by = ? ORDER BY created_at DESC LIMIT 5",
                [uid],
            )
        except:
            return pd.DataFrame()

    hist_df = get_recent_requests(current_user_id)
    if not hist_df.empty:
        st.dataframe(hist_df, use_container_width=True, hide_index=True)

st.sidebar.markdown("---")

# Load ASIN List (Cached for Performance)
@st.cache_data
def get_asin_list():
    return query_df("""
        SELECT 
            asin as parent_asin, 
            COALESCE(real_total_ratings, 0) as review_count, 
            COALESCE(real_average_rating, 0.0) as avg_rating
        FROM products 
        ORDER BY review_count DESC, parent_asin ASC
    """)

df_asins = get_asin_list()

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
            # 3. Reset Agent
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

        # --- PRE-CALCULATED STATS (FETCH ONCE) ---
        precalc = get_precalc_stats(selected_asin)

        # --- TABS LAYOUT ---
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

        with tab_overview:
            render_overview_tab(selected_asin, product_brand, dna, precalc)
        
        with tab_deep:
            render_xray_tab(selected_asin, precalc)

        with tab_battle:
            render_showdown_tab(selected_asin)

        with tab_strategy:
            render_strategy_tab(selected_asin, current_user_id)
