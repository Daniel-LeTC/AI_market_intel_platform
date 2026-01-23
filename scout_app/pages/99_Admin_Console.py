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

# Tabs
tab_dash, tab_req, tab_scrape, tab_staging, tab_ai, tab_logs = st.tabs(
    ["🚀 Pipeline Dashboard", "📥 User Requests", "🕷️ Scrape Room", "📦 Staging Area", "🧠 AI Operations", "📟 Terminal"]
)

# --- TAB 0: PIPELINE DASHBOARD ---
with tab_dash:
    st.header("Pipeline Health Monitor")
    pipe = get_pipeline_stats()
    
    # 1. High Level Metrics
    m1, m2, m3 = st.columns(3)
    with m1:
        revs = pipe.get('reviews', {})
        st.metric("Pending Reviews", revs.get('PENDING', 0), help="New reviews waiting for AI")
        st.metric("Mining in Progress", revs.get('QUEUED', 0), delta_color="off")
    with m2:
        st.metric("Janitor Debt", f"{pipe.get('unmapped_count', 0)} aspects", help="Aspects waiting for standardization")
    with m3:
        st.metric("Stale Dashboards", len(pipe.get('recalc_list', [])), help="ASINs with new data but old stats")

    # 2. Action Lists
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🧹 Dirty Aspects (Sample)")
        if pipe.get('unmapped_count', 0) > 0:
            df_dirty = query_df("""
                SELECT aspect, COUNT(*) as mentions 
                FROM review_tags rt
                LEFT JOIN aspect_mapping am ON lower(trim(rt.aspect)) = lower(trim(am.raw_aspect))
                WHERE am.raw_aspect IS NULL AND length(rt.aspect) BETWEEN 2 AND 40
                GROUP BY 1 ORDER BY 2 DESC LIMIT 10
            """)
            st.dataframe(df_dirty, use_container_width=True, hide_index=True)
            st.info("💡 Go to 'AI Operations' to run Janitor.")
        else:
            st.success("All aspects are clean!")

    with c2:
        st.subheader("📊 Recalc Queue")
        recalc_list = pipe.get('recalc_list', [])
        if recalc_list:
            st.write(f"The following **{len(recalc_list)}** ASINs need a stats refresh:")
            st.code(", ".join(recalc_list[:20]) + ("..." if len(recalc_list) > 20 else ""), language="text")
            if st.button("🚀 Trigger Smart Recalc Now", type="primary"):
                try:
                    res = requests.post(f"{WORKER_URL}/trigger/recalc", timeout=5)
                    if res.status_code == 202:
                        st.toast("Smart Recalc Dispatched!")
                        time.sleep(1)
                        st.rerun()
                except:
                    st.error("Worker Offline")
        else:
            st.success("All dashboards are fresh!")

# --- TAB 0: USER REQUESTS ---
with tab_req:
    st.header("ASIN Request Queue")

    # Load data
    df_req = query_df(
        "SELECT request_id, asin, note, priority, status, created_at FROM scrape_queue WHERE status = 'PENDING_APPROVAL' ORDER BY created_at DESC"
    )

    if df_req.empty:
        st.success("🎉 All requests cleared!")
    else:
        # Add 'Select' column for checkbox UI
        df_req.insert(0, "Select", False)

        st.caption("Double-click cells to Edit ASIN/Note. Tick 'Select' to Approve in Batch.")

        # Editable Dataframe
        edited_df = st.data_editor(
            df_req,
            column_config={
                "Select": st.column_config.CheckboxColumn("Approve?", default=False),
                "request_id": st.column_config.TextColumn("ID", disabled=True),
                "asin": st.column_config.TextColumn("ASIN (Editable)", help="Change Child to Parent ASIN here"),
                "status": st.column_config.TextColumn("Status", disabled=True),
                "created_at": st.column_config.DatetimeColumn("Requested At", disabled=True, format="D MMM, HH:mm"),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="req_editor",
        )

        col_act1, col_act2 = st.columns([1, 4])
        with col_act1:
            if st.button("🚀 Approve Selected", type="primary"):
                # Filter selected rows
                selected_rows = edited_df[edited_df["Select"] == True]

                if selected_rows.empty:
                    st.warning("Please tick at least one row.")
                else:
                    approved_asins = []
                    for index, row in selected_rows.iterrows():
                        # Update DB
                        sql_update = """
                            UPDATE scrape_queue 
                            SET status = 'READY_TO_SCRAPE', asin = ?, note = ?
                            WHERE request_id = ?
                        """
                        execute_sql(sql_update, [row["asin"], row["note"], row["request_id"]])
                        approved_asins.append(row["asin"])

                    # Store in session state to trigger scrape in Tab 1 or here directly
                    st.session_state["approved_batch"] = approved_asins
                    st.success(f"✅ Approved {len(approved_asins)} items!")
                    st.rerun()

        with col_act2:
            if st.button("🗑️ Reject Selected", type="secondary"):
                selected_rows = edited_df[edited_df["Select"] == True]
                if not selected_rows.empty:
                    for _, row in selected_rows.iterrows():
                        execute_sql(
                            "UPDATE scrape_queue SET status = 'REJECTED' WHERE request_id = ?", [row["request_id"]]
                        )
                    st.success("Moved to Rejected.")
                    time.sleep(1)
                    st.rerun()

    # --- AUTO-LAUNCH SECTION (Post-Approval) ---
    if "approved_batch" in st.session_state and st.session_state["approved_batch"]:
        st.divider()
        st.info(f"🚀 **Ready to Launch:** {len(st.session_state['approved_batch'])} ASINs pending execution.")
        st.code(", ".join(st.session_state["approved_batch"]), language="text")

        c_launch, c_clear = st.columns([1, 4])
        with c_launch:
            if st.button("🔥 Launch Scraper Now", type="primary"):
                try:
                    payload = {"asins": st.session_state["approved_batch"]}
                    res = requests.post(f"{WORKER_URL}/trigger/scrape", json=payload, timeout=5)
                    if res.status_code == 202:
                        st.success(f"✅ Scraper Dispatched! Status: {res.json().get('status')}")
                        # Update status to PROCESSING
                        placeholders = ",".join(["?" ] * len(st.session_state["approved_batch"]))
                        execute_sql(
                            f"UPDATE scrape_queue SET status = 'PROCESSING' WHERE asin IN ({placeholders}) AND status = 'READY_TO_SCRAPE'",
                            st.session_state["approved_batch"],
                        )
                        del st.session_state["approved_batch"]
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Failed: {res.text}")
                except Exception as e:
                    st.error(f"Worker connection failed: {e}")
        with c_clear:
            if st.button("Cancel / Clear"):
                del st.session_state["approved_batch"]
                st.rerun()

# --- TAB 1: SCRAPE ROOM ---
with tab_scrape:
    st.header("Hot Plug Scraper")
    st.info("Files will be downloaded to Staging Area. They are NOT ingested automatically.")

    col1, col2 = st.columns([3, 1])
    with col1:
        asins_input = st.text_area("Enter ASINs (one per line or comma separated)", height=100)
    with col2:
        st.write("")  # Spacer
        st.write("")
        scrape_btn = st.button("🚀 Launch Scraper", type="primary", use_container_width=True)

    if scrape_btn:
        if asins_input.strip():
            asins = [a.strip() for a in asins_input.replace("\n", ",").split(",") if a.strip()]
            try:
                res = requests.post(f"{WORKER_URL}/trigger/scrape", json={"asins": asins}, timeout=5)
                if res.status_code == 202:
                    st.success(f"✅ Scraper Dispatched for {len(asins)} ASINs! Check Terminal for progress.")
                else:
                    st.error(f"Failed: {res.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")
        else:
            st.warning("⚠️ Please enter at least one ASIN before launching the scraper.")

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
        st.markdown(
            """
        **Live Mode** is expensive for large datasets (> 1000 reviews). 
        Use **Batch Mode** via the **Terminal Tab** to reduce costs significantly:
        
        1. Select `python manage.py batch-submit-miner` in the Dropdown Palette.
        2. Wait for completion (check via `batch-status`).
        3. Collect results via `batch-collect`.
        """,
            unsafe_allow_html=True,
        )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### ⛏️ Miner (Extract Aspects)")
        limit = st.number_input("Review Limit", 10, 1000, 50)
        if st.button("Start Miner"):
            try:
                requests.post(f"{WORKER_URL}/trigger/miner", params={"limit": limit}, timeout=2)
                st.toast("Miner Started!")
            except:
                st.error("Worker Offline")

    with c2:
        st.markdown("#### 🧹 Janitor (Normalize Tags)")
        st.markdown("Clean raw tags into standards.")
        if st.button("Start Janitor"):
            try:
                requests.post(f"{WORKER_URL}/trigger/janitor", timeout=2)
                st.toast("Janitor Started!")
            except:
                st.error("Worker Offline")

    st.divider()
    st.markdown("#### 📊 Stats Engine (Dashboard Cache)")
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        if st.button("🔥 Global Stats Recalc", help="Recalculate ALL products (Heavy CPU!)"):
            try:
                res = requests.post(f"{WORKER_URL}/trigger/recalc", timeout=5)
                if res.status_code == 202:
                    st.success("🚀 Global Recalc Dispatched!")
                else:
                    st.error("Failed")
            except:
                st.error("Worker Offline")
    with s_col2:
        target_asin = st.text_input("Target ASIN (Optional)", placeholder="B0...")
        if st.button("📊 Targeted Recalc"):
            if not target_asin:
                st.warning("Please enter an ASIN")
            else:
                try:
                    res = requests.post(f"{WORKER_URL}/trigger/recalc", params={"asin": target_asin}, timeout=5)
                    if res.status_code == 202:
                        st.toast(f"Recalc started for {target_asin}")
                    else:
                        st.error("Failed")
                except:
                    st.error("Worker Offline")

# --- TAB 4: TERMINAL (Safe Command Palette) ---
with tab_logs:
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
