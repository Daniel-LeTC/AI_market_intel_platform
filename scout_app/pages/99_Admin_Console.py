import streamlit as st
import requests
import os
import pandas as pd
import time
from pathlib import Path

# --- Configuration ---
st.set_page_config(page_title="Admin Console", page_icon="🛡️", layout="wide")

# CSS to fix long lines in code blocks (Word Wrap)
st.markdown("""
    <style>
    .stCode code {
        white-space: pre-wrap !important;
        word-break: break-all !important;
    }
    </style>
""", unsafe_allow_html=True)

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
LOG_FILE = BASE_DIR / "scout_app/logs/worker.log"
STAGING_DIR = BASE_DIR / "staging_data"
WORKER_URL = os.getenv("WORKER_URL", "http://worker:8000")

# Security
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    if st.session_state["password_input"] == ADMIN_PASSWORD:
        st.session_state["authenticated"] = True
    else:
        st.error("❌ Wrong Password")

if not st.session_state["authenticated"]:
    st.title("🛡️ Restricted Access")
    st.text_input("Enter Admin Password", type="password", key="password_input", on_change=check_password)
    st.stop()

# --- Helpers ---
def tail_log(lines=30):
    if not LOG_FILE.exists():
        return ["Waiting for logs..."]
    try:
        with open(LOG_FILE, "r") as f:
            return f.readlines()[-lines:]
    except Exception:
        return ["Error reading log file."]

def list_staging_files():
    if not STAGING_DIR.exists():
        return []
    return sorted(list(STAGING_DIR.glob("*.xlsx")) + list(STAGING_DIR.glob("*.jsonl")), key=os.path.getmtime, reverse=True)

# --- UI ---
st.title("🛡️ Gatekeeper Control Center")

# Tabs
tab_scrape, tab_staging, tab_ai, tab_logs = st.tabs(["🕷️ Scrape Room", "📦 Staging Area", "🧠 AI Operations", "📟 Terminal"])

# --- TAB 1: SCRAPE ROOM ---
with tab_scrape:
    st.header("Hot Plug Scraper")
    st.info("Files will be downloaded to Staging Area. They are NOT ingested automatically.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        asins_input = st.text_area("Enter ASINs (one per line or comma separated)", height=100)
    with col2:
        st.write("") # Spacer
        st.write("")
        scrape_btn = st.button("🚀 Launch Scraper", type="primary", use_container_width=True)

    if scrape_btn and asins_input:
        asins = [a.strip() for a in asins_input.replace("\n", ",").split(",") if a.strip()]
        if asins:
            try:
                res = requests.post(f"{WORKER_URL}/trigger/scrape", json={"asins": asins}, timeout=5)
                if res.status_code == 202:
                    st.success(f"✅ Scraper Dispatched for {len(asins)} ASINs! Check Terminal for progress.")
                else:
                    st.error(f"Failed: {res.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")
        else:
            st.warning("Please enter at least one ASIN.")

# --- TAB 2: STAGING AREA (Safe Ingest - API BASED) ---
with tab_staging:
    st.header("Staging Data Manager")
    st.markdown("Verify and Ingest files into the Main Database.")
    
    if st.button("🔄 Refresh List"):
        st.rerun()

    files = list_staging_files()
    if not files:
        st.info("No files in staging area.")
    else:
        for f in files:
            with st.expander(f"📄 {f.name} ({f.stat().st_size / 1024:.1f} KB)", expanded=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.caption(f"Path: `{f}`")
                    st.caption(f"Modified: {time.ctime(f.stat().st_mtime)}")
                with c2:
                    if st.button("📥 Ingest to DB", key=f"ingest_{f.name}"):
                        try:
                            payload = {"file_path": str(f.resolve())}
                            res = requests.post(f"{WORKER_URL}/trigger/ingest", json=payload, timeout=5)
                            if res.status_code == 202:
                                st.toast("✅ Ingest Request Sent!", icon="📥")
                                st.info("Worker is processing ingestion. Check Terminal for results.")
                            else:
                                st.error(f"Failed to trigger ingest: {res.text}")
                        except Exception as e:
                            st.error(f"Connection Error: {e}")
                with c3:
                    if st.button("🗑️ Delete", key=f"del_{f.name}", type="secondary"):
                        os.remove(f)
                        st.rerun()

# --- TAB 3: AI OPS ---
with tab_ai:
    st.header("AI Operations")
    
    with st.expander("💡 PRO TIP: Save 50% Cost with BATCH Mode", expanded=False):
        st.markdown("""
        **Live Mode** is expensive for large datasets (> 1000 reviews). 
        Use **Batch Mode** via the **Terminal Tab** to reduce costs significantly:
        
        1. Select `python manage.py batch-submit-miner` in the Dropdown Palette.
        2. Wait for completion (check via `batch-status`).
        3. Collect results via `batch-collect`.
        """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### ⛏️ Miner (Extract Aspects)")
        limit = st.number_input("Review Limit", 10, 1000, 50)
        if st.button("Start Miner"):
            try:
                requests.post(f"{WORKER_URL}/trigger/miner", params={"limit": limit}, timeout=2)
                st.toast("Miner Started!")
            except: st.error("Worker Offline")
    
    with c2:
        st.markdown("#### 🧹 Janitor (Normalize Tags)")
        st.markdown("Clean raw tags into standards.")
        if st.button("Start Janitor"):
            try:
                requests.post(f"{WORKER_URL}/trigger/janitor", timeout=2)
                st.toast("Janitor Started!")
            except: st.error("Worker Offline")

# --- TAB 4: TERMINAL (Safe Command Palette) ---
with tab_logs:
    st.header("🛠️ Quick Commands")
    st.caption("Execute on-demand commands directly within the worker container.")
    
    col_cmd, col_btn = st.columns([3, 1])
    with col_cmd:
        cmd_choice = st.selectbox(
            "Select Command:",
            [
                "ls -lh staging_data/",
                "du -sh scout_app/database/scout.duckdb",
                "python manage.py batch-status",
                "python manage.py batch-collect",
                "python manage.py batch-submit-miner --limit 5000",
                "python manage.py batch-submit-janitor",
                "tail -n 100 scout_app/logs/worker.log"
            ]
        )
    with col_btn:
        st.write("") # Spacer
        st.write("") # Spacer
        run_cmd = st.button("▶️ Run Command", type="primary", use_container_width=True)

    # --- RESULT AREA ---
    if run_cmd:
        st.markdown("#### 📤 Command Output")
        try:
            res = requests.post(f"{WORKER_URL}/admin/exec_cmd", json={"cmd": cmd_choice}, timeout=65)
            if res.status_code == 200:
                data = res.json()
                st.success(f"Executed: `{data['cmd']}` (Code: {data['returncode']})")
                if data['stdout']:
                    st.code(data['stdout'], language="bash")
                if data['stderr']:
                    st.error(data['stderr'])
            else:
                st.error(f"Error: {res.text}")
        except Exception as e:
            st.error(f"Connection Error: {e}")

    st.divider()
    st.header("📜 Worker Event History")
    st.caption("Persistent log of all background activities (Scraping, Ingesting, Mining).")
    if st.button("🔄 Refresh History"):
        st.rerun()
    
    logs = tail_log(50)
    log_text = "".join(logs)
    st.code(log_text, language="bash", line_numbers=True)