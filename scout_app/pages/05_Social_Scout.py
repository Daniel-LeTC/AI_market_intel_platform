import streamlit as st
import requests
import os
import pandas as pd
from datetime import datetime

# --- Config ---
st.set_page_config(page_title="Social Scout", page_icon="📱", layout="wide")
WORKER_URL = os.getenv("WORKER_URL", "http://worker:8000")

# --- UI Header ---
st.title("📱 Social Scout Intelligence")
st.markdown("""
    *Reverse Engineer Trends & Spy on Competitor Ads.* 
    **TikTok (Budget Friendly)** | **Meta (Deep Dive Only)**
""")

# --- Helper: API Calls ---
def call_social_api(endpoint, method="POST", json_data=None):
    try:
        url = f"{WORKER_URL}/social{endpoint}"
        if method == "POST":
            resp = requests.post(url, json=json_data, timeout=10)
        else:
            resp = requests.get(url, timeout=10)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# --- TABS ---
tab_tt, tab_meta, tab_vault = st.tabs(["🕺 TikTok Trend Hunter", "💙 Meta Ad Spy", "📂 Social Vault"])

# --- TAB 1: TIKTOK ---
with tab_tt:
    st.header("TikTok Viral Scout")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        tt_keywords = st.text_input("Hashtags / Keywords:", placeholder="e.g., beddinghack, bedroomdecor", help="Separate by comma")
        tt_limit = st.slider("Max Posts to Scan:", 10, 500, 50, step=10)
    
    with col2:
        st.info("**Cost Estimate (TikTok)**")
        if tt_keywords:
            res_cost = call_social_api("/estimate_cost", json_data={"platform": "tiktok", "limit": tt_limit})
            if "error" not in res_cost:
                cost = res_cost['estimated_cost_usd']
                st.metric("Estimated Cost", f"${cost:.3f}")
                st.success("🟢 Safe to run (Budget friendly)")
            else:
                st.error("Worker Offline")
        else:
            st.write("Enter keywords to see cost.")

    if st.button("🚀 Launch TikTok Scout", type="primary"):
        if not tt_keywords:
            st.warning("Please enter at least one keyword.")
        else:
            keywords = [k.strip() for k in tt_keywords.split(",")]
            payload = {
                "keywords": keywords,
                "platform": "tiktok",
                "limit": tt_limit
            }
            res = call_social_api("/trigger", json_data=payload)
            if "error" not in res:
                st.success(f"✅ Job Dispatched! Results will appear in Social Vault soon.")
            else:
                st.error(f"Failed: {res['error']}")

# --- TAB 2: META ---
with tab_meta:
    st.header("Meta Ads Library Spy")
    st.warning("⚠️ Meta Scraping is expensive. Use sparingly for verified competitors.")
    
    m_col1, m_col2 = st.columns([2, 1])
    
    with m_col1:
        meta_keywords = st.text_input("Brand Name / Product Keyword:", placeholder="e.g., Bedsure, Comforter Set")
        meta_limit = st.number_input("Max Ads to Scan:", 5, 100, 20)
        meta_country = st.selectbox("Target Country:", ["US", "VN", "GB", "CA", "DE"])
    
    with m_col2:
        st.info("**Cost Estimate (Meta)**")
        if meta_keywords:
            res_cost = call_social_api("/estimate_cost", json_data={"platform": "meta_ads", "limit": meta_limit})
            if "error" not in res_cost:
                cost = res_cost['estimated_cost_usd']
                st.metric("Estimated Cost", f"${cost:.3f}")
                if cost > 2.0:
                    st.error("🔴 High Friction Cost! Confirm before running.")
                else:
                    st.warning("🟡 Moderate Cost")
            else:
                st.error("Worker Offline")
        else:
            st.write("Enter keywords to see cost.")

    if st.button("🔥 Launch Meta Spy", type="secondary"):
        if not meta_keywords:
            st.warning("Please enter keyword.")
        else:
            payload = {
                "keywords": [meta_keywords.strip()],
                "platform": "meta_ads",
                "limit": meta_limit,
                "country": meta_country
            }
            res = call_social_api("/trigger", json_data=payload)
            if "error" not in res:
                st.success(f"✅ Ad Spy Dispatched! Checking {meta_keywords} in {meta_country}...")
            else:
                st.error(f"Failed: {res['error']}")

# --- TAB 3: VAULT ---
with tab_vault:
    st.header("Social Data Vault (Staging)")
    st.caption("Files generated from social scouts. Review and Ingest to analyze.")
    
    staging_dir = "staging_data"
    if os.path.exists(staging_dir):
        files = [f for f in os.listdir(staging_dir) if f.startswith("social_") and f.endswith(".csv")]
        if not files:
            st.info("No social data files found yet.")
        else:
            for f in sorted(files, reverse=True):
                with st.expander(f"📄 {f}", expanded=False):
                    f_path = os.path.join(staging_dir, f)
                    try:
                        df = pd.read_csv(f_path)
                        st.dataframe(df.head(10), use_container_width=True)
                        c1, c2 = st.columns(2)
                        with c1:
                            st.download_button("📥 Download CSV", data=open(f_path, "rb"), file_name=f)
                        with c2:
                            if st.button("🗑️ Delete File", key=f):
                                os.remove(f_path)
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error reading file: {e}")
    else:
        st.error("Staging directory missing.")

# --- SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ Wallet Guard Status")
st.sidebar.write("Budget Cap: **$20.00 / Month**")
st.sidebar.progress(0.15, text="Spend: $3.15 (Mocked)")
st.sidebar.markdown("---")
st.sidebar.caption("Powered by Apify Flash APIs")
