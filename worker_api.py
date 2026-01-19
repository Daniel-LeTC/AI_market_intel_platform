from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
import os
import sys
import subprocess
from typing import List

# Ensure root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import core logic
from scout_app.core.miner import AIMiner
from scout_app.core.normalizer import TagNormalizer
from scout_app.core.scraper import AmazonScraper
from scout_app.core.ingest import DataIngester

# NEW: Import Routers
from scout_app.routers import social

# --- Logging Setup ---
LOG_FILE = "scout_app/logs/worker.log"
logger = logging.getLogger("Gatekeeper")
logger.setLevel(logging.INFO)

fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

app = FastAPI(title="RnD Scout Gatekeeper", version="1.6 (Social Module)")

# Include Routers
app.include_router(social.router)

# --- Models ---
class ScrapeRequest(BaseModel):
    asins: List[str]

class IngestRequest(BaseModel):
    file_path: str

class CommandRequest(BaseModel):
    cmd: str

# --- Logic Wrappers ---
def run_miner_task(limit: int):
    logger.info(f"🚀 [Miner] Starting Job (Limit: {limit})...")
    try:
        miner = AIMiner()
        miner.run_live(limit=limit) 
        logger.info(f"✅ [Miner] Job Complete.")
    except Exception as e:
        logger.error(f"❌ [Miner] Failed: {e}")

def run_janitor_task():
    logger.info(f"🧹 [Janitor] Starting Job...")
    try:
        janitor = TagNormalizer()
        janitor.run_live() 
        logger.info(f"✅ [Janitor] Job Complete.")
    except Exception as e:
        logger.error(f"❌ [Janitor] Failed: {e}")

def run_scraper_task(asins: List[str]):
    logger.info(f"🕷️ [Scraper] Starting for {len(asins)} ASINs: {asins}...")
    try:
        scraper = AmazonScraper()
        file_path = scraper.run_deep_scrape(asins)
        if file_path:
            logger.info(f"✅ [Scraper] Data saved to: {file_path}")
            logger.info(f"👉 [Action Required] Go to Admin Console -> Staging Files to verify & ingest.")
        else:
            logger.warning("⚠️ [Scraper] No data returned from Apify.")
    except Exception as e:
        logger.error(f"❌ [Scraper] Failed: {e}")

def run_ingest_task(file_path: str):
    logger.info(f"📥 [Ingest] Starting ingestion for: {file_path}")
    try:
        from pathlib import Path
        path_obj = Path(file_path)
        if "staging_data" not in str(path_obj.resolve()):
            logger.error(f"❌ [Ingest] Security Block: Cannot ingest files outside staging_data.")
            return
        ingester = DataIngester()
        result = ingester.ingest_file(path_obj)
        if "error" in result:
            logger.error(f"❌ [Ingest] Failed: {result['error']}")
        else:
            logger.info(f"✅ [Ingest] Success! Rows: {result.get('inserted_rows')}. ASINs: {result.get('asins_found')}")
    except Exception as e:
        logger.error(f"❌ [Ingest] Critical Error: {e}")

# --- Endpoints ---

@app.get("/")
def health_check():
    return {"status": "online", "role": "Gatekeeper Full"}

@app.post("/trigger/miner", status_code=202)
def trigger_miner(background_tasks: BackgroundTasks, limit: int = 100):
    background_tasks.add_task(run_miner_task, limit)
    return {"status": "accepted", "job": "miner"}

@app.post("/trigger/janitor", status_code=202)
def trigger_janitor(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_janitor_task)
    return {"status": "accepted", "job": "janitor"}

@app.post("/trigger/scrape", status_code=202)
def trigger_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks):
    asins = [a.strip() for a in req.asins if a.strip()]
    if not asins:
        raise HTTPException(status_code=400, detail="No ASINs provided")
    background_tasks.add_task(run_scraper_task, asins)
    return {"status": "accepted", "job": "scrape", "target": asins}

@app.post("/trigger/ingest", status_code=202)
def trigger_ingest(req: IngestRequest, background_tasks: BackgroundTasks):
    if not os.path.exists(req.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    background_tasks.add_task(run_ingest_task, req.file_path)
    return {"status": "accepted", "job": "ingest", "file": req.file_path}

@app.post("/admin/run_migration_v2")
def trigger_migration_v2():
    try:
        from scout_app.core.migration_v2 import migrate_v2_social_wallet
        migrate_v2_social_wallet()
        return {"status": "success", "message": "Migration V2 completed."}
    except Exception as e:
        logger.error(f"Migration Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/exec_cmd")
def exec_cmd(req: CommandRequest):
    """
    Execute SAFE shell commands via Dropdown Palette.
    Whitelist prevents RCE abuse.
    """
    cmd = req.cmd.strip()
    
    # Whitelist Check
    allowed_prefixes = [
        "ls ", "du ", "tail ", 
        "python manage.py batch-status", 
        "python manage.py batch-collect",
        "python manage.py batch-submit-miner",
        "python manage.py batch-submit-janitor"
    ]
    
    is_safe = any(cmd.startswith(p) for p in allowed_prefixes)
    if not is_safe:
        raise HTTPException(status_code=403, detail="Command not allowed. Please use the Dropdown Palette.")

    try:
        # Run command and capture output (Timeout 60s for batch submit)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return {
            "cmd": cmd,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/dedup/stats")
def get_dedup_stats():
    try:
        import duckdb
        from scout_app.core.config import Settings
        db_path = str(Settings.get_active_db_path())
        
        query = """
        WITH enriched_tags AS (
            SELECT 
                rt.*,
                CASE WHEN am.standard_aspect IS NOT NULL THEN 1 ELSE 0 END as is_cleaned
            FROM review_tags rt
            LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
        ),
        ranked_tags AS (
            SELECT 
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY review_id, quote, sentiment 
                    ORDER BY is_cleaned DESC, created_at DESC
                ) as rank
            FROM enriched_tags
        )
        SELECT 
            CASE WHEN rank = 1 THEN 'KEEP' ELSE 'DELETE' END as action,
            COUNT(*) as count
        FROM ranked_tags
        GROUP BY 1
        """
        with duckdb.connect(db_path, read_only=True) as conn:
            df = conn.execute(query).df()
            stats = df.set_index('action')['count'].to_dict()
            return {
                "active_db": os.path.basename(db_path),
                "total_rows": int(df['count'].sum()),
                "duplicates": int(stats.get('DELETE', 0)),
                "clean_rows": int(stats.get('KEEP', 0))
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/dedup/run")
def run_dedup(background_tasks: BackgroundTasks):
    def dedup_job():
        logger.info("🧹 [Dedup] Starting Smart Cleanup...")
        try:
            import duckdb
            import shutil
            from scout_app.core.config import Settings
            
            active_path = Settings.get_active_db_path()
            standby_path = Settings.get_standby_db_path()
            
            # 1. Sync
            shutil.copy(active_path, standby_path)
            
            # 2. Clean Standby
            with duckdb.connect(str(standby_path)) as conn:
                conn.execute("""
                    DELETE FROM review_tags 
                    WHERE tag_id IN (
                        SELECT tag_id FROM (
                            SELECT 
                                rt.tag_id,
                                ROW_NUMBER() OVER (
                                    PARTITION BY rt.review_id, rt.quote, rt.sentiment 
                                    ORDER BY (CASE WHEN am.standard_aspect IS NOT NULL THEN 1 ELSE 0 END) DESC, rt.created_at DESC
                                ) as rank
                            FROM review_tags rt
                            LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
                        ) WHERE rank > 1
                    )
                """)
            
            # 3. Swap
            Settings.swap_db()
            logger.info(f"✅ [Dedup] Cleanup complete. Swapped to {os.path.basename(standby_path)}")
            
        except Exception as e:
            logger.error(f"❌ [Dedup] Failed: {e}")

    background_tasks.add_task(dedup_job)
    return {"status": "accepted", "message": "Dedup job started in background."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)