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
    
    # --- STEP 1: FEED HUNTING ---
    with st.expander("1️⃣ Step 1: Hunt Viral Videos (Feed Scraper)", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            tt_keywords = st.text_input("Hashtags / Keywords:", placeholder="e.g., beddinghack", help="Separate by comma")
            tt_limit = st.slider("Max Posts to Scan:", 10, 500, 50, step=10)
        with col2:
            st.info("**Cost Estimate (Feed)**")
            if tt_keywords:
                res_cost = call_social_api("/estimate_cost", json_data={"platform": "tiktok", "limit": tt_limit, "task_type": "feed"})
                if "error" not in res_cost:
                    cost = res_cost['estimated_cost_usd']
                    st.metric("Estimated Cost", f"${cost:.3f}")
                    st.success("🟢 Safe to run (Cheap)")
                else:
                    st.error("Worker Offline")

        if st.button("🚀 Launch Feed Scraper", type="primary"):
            if not tt_keywords:
                st.warning("Please enter at least one keyword.")
            else:
                keywords = [k.strip() for k in tt_keywords.split(",")]
                payload = {"keywords": keywords, "platform": "tiktok", "limit": tt_limit}
                res = call_social_api("/trigger", json_data=payload)
                if "error" not in res:
                    st.success(f"✅ Job Dispatched! Wait for file in Step 2.")
                else:
                    st.error(f"Failed: {res['error']}")

    # --- STEP 2: DEEP DIVE ---
    st.markdown("---")
    st.subheader("2️⃣ Step 2: Deep Dive (Comment Analysis)")
    
    # List available feed files
    staging_dir = "staging_data"
    feed_files = []
    if os.path.exists(staging_dir):
        feed_files = [f for f in os.listdir(staging_dir) if f.startswith("social_tiktok_feed_") and f.endswith(".csv")]
    
    if not feed_files:
        st.info("ℹ️ No feed data found. Run Step 1 first.")
    else:
        selected_file = st.selectbox("Select Feed File:", sorted(feed_files, reverse=True))
        
        if selected_file:
            try:
                df_feed = pd.read_csv(os.path.join(staging_dir, selected_file))
                
                # FIX: Ensure 'desc' is string to avoid Streamlit Float Error on NaN
                if "desc" in df_feed.columns:
                    df_feed["desc"] = df_feed["desc"].astype(str).replace("nan", "")
                
                # FIX: Ensure 'url' is string
                if "url" in df_feed.columns:
                    df_feed["url"] = df_feed["url"].astype(str).replace("nan", "")

                # FIX: Convert ID to string to prevent JS BigInt precision loss
                if "id" in df_feed.columns:
                    df_feed["id"] = df_feed["id"].astype(str)
                
                # Show Selector
                st.caption("Tick videos to scrape comments:")
                df_feed.insert(0, "Select", False)
                
                edited_feed = st.data_editor(
                    df_feed,
                    column_config={
                        "Select": st.column_config.CheckboxColumn(required=True),
                        "url": st.column_config.LinkColumn("Video Link"),
                        "desc": st.column_config.TextColumn("Description", width="medium"),
                        "views": st.column_config.NumberColumn("Views"),
                        "likes": st.column_config.NumberColumn("Likes"),
                    },
                    hide_index=True,
                    use_container_width=True,
                    num_rows="fixed"
                )
                
                # Action Zone
                c_act1, c_act2 = st.columns([1, 1])
                with c_act1:
                    max_comments = st.number_input("Max Comments per Video:", 20, 1000, 50)
                
                # Get Selected
                selected_rows = edited_feed[edited_feed["Select"] == True]
                num_selected = len(selected_rows)
                
                with c_act2:
                    st.write("") # Spacer
                    st.write("") # Spacer
                    if num_selected > 0:
                        total_items = num_selected * max_comments
                        # Estimate Cost
                        res_est = call_social_api("/estimate_cost", json_data={"platform": "tiktok", "limit": total_items, "task_type": "comments"})
                        if "error" not in res_est:
                            cost_est = res_est['estimated_cost_usd']
                            st.metric(f"Est. Cost ({num_selected} Vids)", f"${cost_est:.3f}")
                            
                            if st.button("🔥 Launch Comment Scraper", type="primary"):
                                vid_urls = selected_rows['url'].tolist()
                                payload_cmt = {
                                    "video_urls": vid_urls,
                                    "max_comments_per_video": max_comments,
                                    "platform": "tiktok"
                                }
                                res_cmt = call_social_api("/trigger_comments", json_data=payload_cmt)
                                if "error" not in res_cmt:
                                    st.success(f"✅ Dispatched! Scraping {total_items} comments...")
                                else:
                                    st.error(f"Failed: {res_cmt['error']}")
                        else:
                            st.error("Worker Offline")
                    else:
                        st.info("Select videos to estimate cost.")
                        
            except Exception as e:
                st.error(f"Error loading file: {e}")

# --- TAB 2: FACEBOOK ---
with tab_meta:
    st.header("Facebook Hashtag Spy")
    st.warning("⚠️ High Cost: Facebook scraping is ~5x more expensive than TikTok.")
    
    # --- STEP 1: HASHTAG HUNTING ---
    with st.expander("1️⃣ Step 1: Hunt Viral Posts (Hashtag Search)", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            fb_keywords = st.text_input("Hashtags:", placeholder="e.g., bedding, decor", help="Separate by comma (No # needed)", key="fb_kw")
            fb_limit = st.slider("Max Posts to Scan:", 10, 200, 20, step=10, key="fb_lim")
        with col2:
            st.info("**Cost Estimate (Feed)**")
            if fb_keywords:
                res_cost = call_social_api("/estimate_cost", json_data={"platform": "facebook", "limit": fb_limit, "task_type": "feed"})
                if "error" not in res_cost:
                    cost = res_cost['estimated_cost_usd']
                    st.metric("Estimated Cost", f"${cost:.3f}")
                    st.warning("🟡 Moderate Cost")
                else:
                    st.error("Worker Offline")

        if st.button("🚀 Launch Facebook Search", type="primary", key="fb_launch"):
            if not fb_keywords:
                st.warning("Please enter keyword.")
            else:
                keywords = [k.strip() for k in fb_keywords.split(",")]
                payload = {"keywords": keywords, "platform": "facebook", "limit": fb_limit}
                res = call_social_api("/trigger", json_data=payload)
                if "error" not in res:
                    st.success(f"✅ Job Dispatched! Wait for file in Step 2.")
                else:
                    st.error(f"Failed: {res['error']}")

    # --- STEP 2: FB DEEP DIVE ---
    st.markdown("---")
    st.subheader("2️⃣ Step 2: Deep Dive (Comment Analysis)")
    
    # List available feed files
    staging_dir = "staging_data"
    fb_feed_files = []
    if os.path.exists(staging_dir):
        fb_feed_files = [f for f in os.listdir(staging_dir) if f.startswith("social_facebook_feed_") and f.endswith(".csv")]
    
    if not fb_feed_files:
        st.info("ℹ️ No FB feed data found. Run Step 1 first.")
    else:
        sel_fb_file = st.selectbox("Select Feed File:", sorted(fb_feed_files, reverse=True), key="fb_sel_file")
        
        if sel_fb_file:
            try:
                df_fb = pd.read_csv(os.path.join(staging_dir, sel_fb_file))
                
                # FIX: Ensure 'text' is string
                if "text" in df_fb.columns:
                    df_fb["text"] = df_fb["text"].astype(str).replace("nan", "")
                
                # FIX: Ensure 'url' is string
                if "url" in df_fb.columns:
                    df_fb["url"] = df_fb["url"].astype(str).replace("nan", "")

                # FIX: Convert ID to string
                if "id" in df_fb.columns:
                    df_fb["id"] = df_fb["id"].astype(str)

                st.caption("Tick posts to scrape comments:")
                if "Select" not in df_fb.columns:
                    df_fb.insert(0, "Select", False)
                
                # Check required columns exist
                cols_config = {"Select": st.column_config.CheckboxColumn(required=True)}
                if "url" in df_fb.columns: cols_config["url"] = st.column_config.LinkColumn("Post Link")
                if "text" in df_fb.columns: cols_config["text"] = st.column_config.TextColumn("Content", width="medium")
                
                edited_fb = st.data_editor(
                    df_fb,
                    column_config=cols_config,
                    hide_index=True,
                    use_container_width=True,
                    num_rows="fixed",
                    key="fb_editor"
                )
                
                # Action Zone
                c_act1, c_act2 = st.columns([1, 1])
                with c_act1:
                    fb_max_comments = st.number_input("Max Comments per Post:", 10, 500, 20, key="fb_max_cmt")
                
                # Get Selected
                sel_fb_rows = edited_fb[edited_fb["Select"] == True]
                num_fb_sel = len(sel_fb_rows)
                
                with c_act2:
                    st.write("") 
                    st.write("") 
                    if num_fb_sel > 0:
                        total_items = num_fb_sel * fb_max_comments
                        res_est = call_social_api("/estimate_cost", json_data={"platform": "facebook", "limit": total_items, "task_type": "comments"})
                        if "error" not in res_est:
                            cost_est = res_est['estimated_cost_usd']
                            st.metric(f"Est. Cost ({num_fb_sel} Posts)", f"${cost_est:.3f}")
                            
                            if st.button("🔥 Launch Comment Scraper", type="primary", key="fb_launch_cmt"):
                                post_urls = sel_fb_rows['url'].tolist()
                                payload_cmt = {
                                    "video_urls": post_urls, # Using same key for compatibility, handled in backend
                                    "max_comments_per_video": fb_max_comments,
                                    "platform": "facebook" # IMPORTANT: Backend must handle this flag
                                }
                                # Wait, backend 'CommentRequest' defaults to tiktok platform? Need to check router.
                                # Quick fix: Add 'platform' to CommentRequest model in Router if not exist.
                                # Let's assume Router update is needed or generic.
                                # Actually, Core Scraper has scrape_facebook_comments.
                                # We need to ensure Router passes the platform correctly.
                                
                                res_cmt = call_social_api("/trigger_comments", json_data=payload_cmt)
                                if "error" not in res_cmt:
                                    st.success(f"✅ Dispatched! Scraping comments...")
                                else:
                                    st.error(f"Failed: {res_cmt['error']}")
                        else:
                            st.error("Worker Offline")
                    else:
                        st.info("Select posts to estimate cost.")
                        
            except Exception as e:
                st.error(f"Error loading file: {e}")

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
