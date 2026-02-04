import os
import sys
import time
from pathlib import Path

import duckdb
import pandas as pd
import requests
import streamlit as st

# Add root to sys.path to find core
sys.path.append(str(Path(__file__).resolve().parent.parent))
from core.config import Settings

# --- Configuration ---
st.set_page_config(page_title="Admin Console", page_icon="🛡️", layout="wide")

# --- ADMIN GATEKEEPER ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.warning("⚠️ Access Restricted. Please Login first.")
    st.stop()

if st.session_state.get("role") != "ADMIN":
    st.error("⛔ ACCESS DENIED: Administrators Only.")
    st.stop()

# --- CSS & Path ---
st.markdown(
    """
    <style>
    .stCode code {
        white-space: pre-wrap !important;
        word-break: break-all !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

BASE_DIR = Path(__file__).parent.parent.parent
LOG_FILE = BASE_DIR / "scout_app/logs/worker.log"
STAGING_DIR = BASE_DIR / "staging_data"
WORKER_URL = os.getenv("WORKER_URL", "http://worker:8000")


# --- DB Helpers (Direct for Admin) ---
def get_db_path():
    return str(Settings.get_active_db_path())


def get_pipeline_stats():
    """Fetch high-level metrics for the entire pipeline."""
    db_p = get_db_path()
    stats = {}
    try:
        with duckdb.connect(db_p, read_only=True) as conn:
            # 1. Review Queue
            rev_q = conn.execute("SELECT mining_status, COUNT(*) FROM reviews GROUP BY 1").fetchall()
            stats['reviews'] = {str(s[0]): s[1] for s in rev_q}
            
            # 2. Janitor Debt
            stats['unmapped_count'] = conn.execute("""
                SELECT COUNT(DISTINCT rt.aspect)
                FROM review_tags rt
                LEFT JOIN aspect_mapping am ON lower(trim(rt.aspect)) = lower(trim(am.raw_aspect))
                WHERE am.raw_aspect IS NULL
                AND length(rt.aspect) BETWEEN 2 AND 40
            """).fetchone()[0]
            
            # 3. Recalc Queue
            recalc_df = conn.execute("""
                SELECT DISTINCT r.parent_asin 
                FROM reviews r
                LEFT JOIN product_stats ps ON r.parent_asin = ps.asin
                WHERE r.mining_status = 'COMPLETED'
                AND (ps.last_updated IS NULL OR r.ingested_at > ps.last_updated)
            """).df()
            stats['recalc_list'] = recalc_df['parent_asin'].tolist()
            
    except Exception as e:
        st.error(f"Stats Error: {e}")
    return stats


def query_df(sql, params=None):
    try:
        with duckdb.connect(get_db_path(), read_only=True) as conn:
            return conn.execute(sql, params).df()
    except:
        return pd.DataFrame()


def execute_sql(sql, params=None):
    try:
        with duckdb.connect(get_db_path(), read_only=False) as conn:
            conn.execute(sql, params)
        return True
    except Exception as e:
        st.error(f"SQL Error: {e}")
        return False


# --- Helpers ---
def tail_log(lines=30):
    if not LOG_FILE.exists():
        return ["Waiting for logs..."]
    try:
        with open(LOG_FILE) as f:
            return f.readlines()[-lines:]
    except Exception:
        return ["Error reading log file."]


def list_staging_files():
    if not STAGING_DIR.exists():
        return []
    return sorted(
        list(STAGING_DIR.glob("*.xlsx")) + list(STAGING_DIR.glob("*.jsonl")),
        key=os.path.getmtime,
        reverse=True,
    )


# --- UI ---
st.title("🛡️ Gatekeeper Control Center")
active_db = os.path.basename(get_db_path())
st.caption(f"Welcome, **{st.session_state['username']}** | Connected to: `{active_db}`")

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("⚙️ Admin Tools")
    if st.button("🔄 Refresh Dashboard Data"):
        st.session_state["last_db_update"] = time.time()
        st.cache_data.clear() # Nuclear option to be sure
        st.success("✅ Cache Cleared! Dashboard will reload.")
    
    st.divider()
    if st.button("🚪 Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

# Tabs
tab_scrape, tab_staging, tab_ingest, tab_ai, tab_stats, tab_orch, tab_logs = st.tabs(
    ["🕷️ Scrape Room", "📦 Staging Area", "📥 Ingest Lab", "🧠 AI Operations", "📊 Stats Engine", "🚀 Orchestrator", "📟 Terminal"]
)

# --- TAB 1: SCRAPE ROOM (includes User Requests) ---
with tab_scrape:
    st.header("1. ASIN Request Queue")
    # Load data
    df_req = query_df(
        "SELECT request_id, asin, note, priority, status, created_at FROM scrape_queue WHERE status = 'PENDING_APPROVAL' ORDER BY created_at DESC"
    )

    if df_req.empty:
        st.success("🎉 All requests cleared!")
    else:
        # Add 'Select' column for checkbox UI
        df_req.insert(0, "Select", False)
        st.caption("Approve requests here to move them to the Scrape Engine.")
        edited_df = st.data_editor(
            df_req,
            column_config={
                "Select": st.column_config.CheckboxColumn("Approve?", default=False),
                "asin": st.column_config.TextColumn("ASIN"),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="req_editor",
        )
        
        if st.button("🚀 Approve Selected", type="primary"):
            selected = edited_df[edited_df["Select"] == True]
            for _, row in selected.iterrows():
                execute_sql("UPDATE scrape_queue SET status = 'READY_TO_SCRAPE' WHERE request_id = ?", [row["request_id"]])
            st.success(f"Approved {len(selected)} requests.")
            st.rerun()
            
        if st.button("❌ Reject Selected", type="secondary"):
            selected = edited_df[edited_df["Select"] == True]
            for _, row in selected.iterrows():
                execute_sql("UPDATE scrape_queue SET status = 'REJECTED' WHERE request_id = ?", [row["request_id"]])
            st.warning(f"Rejected {len(selected)} requests.")
            st.rerun()

    st.divider()
    st.header("2. Scrape Engine")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔍 Parent Finder")
        st.caption("Playwright worker to find parentAsin from DP pages.")
        
        # NEW: Manual Category Input
        st.warning("⚠️ **Policy:** Use a SINGLE Category per batch (e.g., 'comforter').")
        target_cat = st.text_input("Target Category (Manual Override)", placeholder="comforter, tumbler, etc.", key="target_cat")
        
        # Auto-Load Helper
        if st.button("📋 Load Approved ASINs"):
            approved_df = query_df("SELECT asin FROM scrape_queue WHERE status = 'READY_TO_SCRAPE' LIMIT 50")
            if not approved_df.empty:
                st.session_state["pf_input"] = "\n".join(approved_df["asin"].tolist())
                st.success(f"Loaded {len(approved_df)} ASINs from queue.")
                st.rerun()
            else:
                st.info("No ASINs marked as 'READY_TO_SCRAPE'.")

        pf_asins = st.text_area("ASINs for Parent Finding", height=100, key="pf_input", value=st.session_state.get("pf_input", ""))
        if st.button("Launch Parent Finder", type="primary" if target_cat else "secondary"):
            if not target_cat:
                st.error("⛔ Please enter a **Target Category** before launching.")
            elif pf_asins.strip():
                asins = [a.strip() for a in pf_asins.replace("\n", ",").split(",") if a.strip()]
                requests.post(f"{WORKER_URL}/trigger/find_parents", json={"asins": asins, "category": target_cat})
                # Sync status in queue
                for asin in asins:
                    execute_sql("UPDATE scrape_queue SET status = 'IN_PROGRESS' WHERE asin = ? AND status = 'READY_TO_SCRAPE'", [asin])
                st.success(f"Parent Finder dispatched for {len(asins)} items in category '{target_cat}'!")
            
    with c2:
        st.subheader("🎭 Apify Detail Scraper")
        st.caption("Axesso API to fetch full product details.")
        
        if st.button("📋 Load Missing Details"):
            missing_df = query_df("SELECT parent_asin FROM product_parents WHERE brand IS NULL LIMIT 20")
            if not missing_df.empty:
                st.session_state["ap_input"] = "\n".join(missing_df["parent_asin"].tolist())
                st.success(f"Loaded {len(missing_df)} parents with missing metadata.")
                st.rerun()
            else:
                st.info("All parents in DB have metadata.")

        ap_asins = st.text_area("ASINs for Details", height=100, key="ap_input", value=st.session_state.get("ap_input", ""))
        if st.button("Launch Apify Worker"):
            if ap_asins.strip():
                asins = [a.strip() for a in ap_asins.replace("\n", ",").split(",") if a.strip()]
                cat = st.session_state.get("target_cat", "comforter")
                requests.post(f"{WORKER_URL}/trigger/product_details", json={"asins": asins, "category": cat})
                st.success(f"Apify Worker dispatched for {len(asins)} items in category '{cat}'!")

    st.divider()
    st.subheader("🕵️ Direct Review Scraper")
    
    if st.button("📋 Load Unscraped Parents"):
        unscraped_df = query_df("""
            SELECT parent_asin FROM product_parents 
            WHERE parent_asin NOT IN (SELECT DISTINCT parent_asin FROM reviews)
            LIMIT 10
        """)
        if not unscraped_df.empty:
            st.session_state["rev_input"] = "\n".join(unscraped_df["parent_asin"].tolist())
            st.success(f"Loaded {len(unscraped_df)} parents needing reviews.")
            st.rerun()
        else:
            st.info("No parents found without reviews.")

    asins_input = st.text_area("Enter ASINs for Reviews (Legacy JSON flow)", height=100, key="rev_input", value=st.session_state.get("rev_input", ""))
    if st.button("Launch Review Scraper"):
        if asins_input.strip():
            asins = [a.strip() for a in asins_input.replace("\n", ",").split(",") if a.strip()]
            requests.post(f"{WORKER_URL}/trigger/scrape", json={"asins": asins})
            st.success("Scraper started!")

# --- TAB 2: STAGING AREA ---
with tab_staging:
    st.header("Data Staging Area")
    st.info("Files here are ready for validation before Ingest.")
    files = list_staging_files()
    if not files:
        st.info("Staging is empty.")
    else:
        for f in files:
            with st.expander(f"📄 {f.name}"):
                st.write(f"Path: {f}")
                if st.button(f"Delete {f.name}"):
                    os.remove(f)
                    st.rerun()

# --- TAB 3: INGEST LAB ---
with tab_ingest:
    st.header("Database Ingestion Lab")
    files = list_staging_files()
    if files:
        selected_file = st.selectbox("Select file to ingest:", [f.resolve() for f in files], format_func=lambda x: os.path.basename(x))
        if st.button("📥 RUN INGESTION", type="primary"):
            try:
                res = requests.post(f"{WORKER_URL}/trigger/ingest", json={"file_path": str(selected_file)})
                if res.status_code == 202:
                    st.success("Ingestion dispatched!")
                else:
                    st.error(res.text)
            except:
                st.error("Worker offline")
    else:
        st.warning("No files in staging to ingest.")

# --- TAB 4: AI OPERATIONS ---
with tab_ai:
    st.header("AI Operations (Miner & Janitor)")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("⛏️ Aspect Miner")
        limit = st.number_input("Review Limit", 10, 5000, 50)
        if st.button("Start Miner"):
            requests.post(f"{WORKER_URL}/trigger/miner", params={"limit": limit})
            st.success("Miner started")
    with c2:
        st.subheader("🧹 Tag Janitor")
        if st.button("Start Janitor"):
            requests.post(f"{WORKER_URL}/trigger/janitor")
            st.success("Janitor started")

# --- TAB 5: STATS ENGINE ---
with tab_stats:
    st.header("Stats Engine & Dashboard Cache")
    target_asin = st.text_input("Target ASIN (Optional)", placeholder="B0...")
    if st.button("🔄 Recalculate Stats"):
        params = {"asin": target_asin} if target_asin else {}
        requests.post(f"{WORKER_URL}/trigger/recalc", params=params)
        st.success("Stats recalc started")

# --- TAB 6: ORCHESTRATOR ---
with tab_orch:
    st.header("Workflow Orchestrator")
    st.markdown("""
    ### 🔄 Active Pipeline Dependencies
    The flowchart below shows the data journey:
    1. **Scrape** -> Creates JSON in Staging.
    2. **Ingest** -> Moves Staging to DB & Updates `product_parents`.
    3. **AI Miner** -> Extracts aspects from raw reviews.
    4. **AI Janitor** -> Standardizes aspects.
    5. **Stats Engine** -> Pre-calculates metrics for UI.
    """)
    st.info("This section will eventually show real-time Gantt charts or dependency graphs.")

# --- TAB 7: TERMINAL & LOGS ---
with tab_logs:
    st.header("Logs & Terminal")
    st.header("🛠️ Quick Commands")
    st.caption("Execute on-demand commands directly within the worker container.")

    col_tpl, col_cmd, col_btn = st.columns([1, 2, 1])
    with col_tpl:
        template = st.selectbox(
            "Templates:",
            [
                "Custom...",
                "ls -lh staging_data/",
                f"du -sh scout_app/database/{active_db}",
                "python manage.py batch-status",
                "python manage.py batch-collect",
                "python manage.py batch-submit-miner --limit 1000",
                "python manage.py batch-submit-janitor",
                "tail -n 100 scout_app/logs/worker.log",
                "python manage.py reset"
            ],
        )
    
    with col_cmd:
        # Default to template, but allow editing
        final_cmd = st.text_input("Command to execute:", value="" if template == "Custom..." else template)

    with col_btn:
        st.write("")  # Spacer
        st.write("")  # Spacer
        run_cmd = st.button("▶️ Run Command", type="primary", use_container_width=True)

    # --- NEW: DB DEDUP, VACUUM & RESET INTEGRATION ---
    st.markdown("---")
    st.markdown("#### 🧹 Database Maintenance")
    d_col1, d_col2, d_col3, d_col4 = st.columns(4)
    with d_col1:
        if st.button("🔍 Check Duplicates", use_container_width=True):
            try:
                res = requests.get(f"{WORKER_URL}/admin/dedup/stats", timeout=5)
                if res.status_code == 200:
                    s = res.json()
                    st.info(f"Active: `{s['active_db']}` | Duplicates: **{s['duplicates']}**")
                else:
                    st.error(res.text)
            except:
                st.error("Worker Offline")
    with d_col2:
        if st.button("🔥 Run Smart Dedup", use_container_width=True):
            try:
                res = requests.post(f"{WORKER_URL}/admin/dedup/run", timeout=5)
                if res.status_code == 202:
                    st.success("🚀 Dedup Task Dispatched!")
                else:
                    st.error(res.text)
            except:
                st.error("Worker Offline")
    with d_col3:
        if st.button("💨 DB Compaction", help="Vacuum active DB", use_container_width=True):
            try:
                v_cmd = f"python -c 'import duckdb; conn=duckdb.connect(\"scout_app/database/{active_db}\"); conn.execute(\"CHECKPOINT; VACUUM;\"); conn.close()'"
                res = requests.post(f"{WORKER_URL}/admin/exec_cmd", json={"cmd": v_cmd}, timeout=60)
                if res.status_code == 200:
                    st.toast("✅ DB Vacuumed!")
                else:
                    st.error("Failed to vacuum.")
            except:
                st.error("Worker Offline")
    with d_col4:
        if st.button("🔄 Reset Stuck Jobs", help="Reset QUEUED to PENDING", use_container_width=True):
            try:
                res = requests.post(f"{WORKER_URL}/admin/exec_cmd", json={"cmd": "python manage.py reset"}, timeout=10)
                if res.status_code == 200:
                    st.toast("✅ Stuck jobs reset to PENDING!")
                else:
                    st.error("Failed to reset.")
            except:
                st.error("Worker Offline")

    # --- RESULT AREA ---
    if run_cmd:
        if not final_cmd:
            st.error("Please enter a command.")
        else:
            st.markdown("#### 📤 Command Output")
            try:
                res = requests.post(f"{WORKER_URL}/admin/exec_cmd", json={"cmd": final_cmd}, timeout=65)
                if res.status_code == 200:
                    data = res.json()
                    st.success(f"Executed: `{data['cmd']}` (Code: {data['returncode']})")
                    if data["stdout"]:
                        st.code(data["stdout"], language="bash")
                    if data["stderr"]:
                        st.error(data["stderr"])
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
