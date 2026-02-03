import argparse
import sys
import shutil
import polars as pl
import duckdb
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to python path
sys.path.append(str(Path(__file__).parent))

from scout_app.core.config import Settings
from scout_app.core.scraper import AmazonScraper
from scout_app.core.ingest import DataIngester
from scout_app.core.miner import AIMiner
from scout_app.core.normalizer import TagNormalizer
from scout_app.core.ai_batch import AIBatchHandler

# Status CSV File (Legacy Dashboard)
STATUS_CSV = Path("asin_marked_status.csv")

def update_tracking_csv(asins: list):
    """Update legacy CSV using Polars."""
    if not STATUS_CSV.exists() or not asins:
        return

    try:
        df = pl.read_csv(STATUS_CSV, ignore_errors=True)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        status_expr = pl.col("Status")
        time_expr = pl.col("Last Scraped At")
        
        for asin in asins:
            mask = (pl.col("Parent Asin").cast(pl.Utf8).str.strip_chars() == str(asin).strip())
            status_expr = pl.when(mask).then(pl.lit("Scraped")).otherwise(status_expr)
            time_expr = pl.when(mask).then(pl.lit(now_str)).otherwise(time_expr)

        df = df.with_columns([
            status_expr.alias("Status"),
            time_expr.alias("Last Scraped At")
        ])
        df.write_csv(STATUS_CSV)
        print(f"📝 [Gatekeeper] Updated CSV tracking for {len(asins)} ASINs.")
    except Exception as e:
        print(f"⚠️ CSV Update Error: {e}")

def run_live_flow(asins: list, skip_ai: bool = False):
    """Scrape -> Ingest -> Live AI Processing."""
    # 1. Scrape
    scraper = AmazonScraper()
    raw_file = scraper.run_deep_scrape(asins)
    if not raw_file: return

    # 2. Ingest
    ingester = DataIngester()
    stats = ingester.ingest_file(raw_file)
    if stats.get("error"): return

    # 3. Update CSV
    update_tracking_csv(stats.get("asins_found", []))

    # 4. Live AI
    if not skip_ai:
        print("🧠 [Gatekeeper] Running Live AI Analysis...")
        miner = AIMiner()
        miner.run_live(limit=100)
        
        janitor = TagNormalizer()
        janitor.run_live()

    # 5. Cleanup
    archive_path = Settings.ARCHIVE_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{raw_file.name}"
    shutil.move(raw_file, archive_path)
    print(f"📦 [Gatekeeper] Flow completed. Data archived.")

def run_batch_submit_miner(limit: int = 10000):
    """Submit unmined reviews to Google Batch with limit."""
    miner = AIMiner()
    miner_file = miner.prepare_batch_file(limit=limit)
    if miner_file:
        miner_handler = AIBatchHandler(api_key=Settings.GEMINI_MINER_KEY)
        job_id = miner_handler.submit_batch_job(miner_file, "Miner", model=miner.MODEL_NAME)
        print(f"✅ Submitted Miner Job: {job_id}")

def run_batch_submit_janitor():
    """Submit unmapped aspects to Google Batch."""
    janitor = TagNormalizer()
    janitor_file = janitor.run_batch_prepare(limit=5000)
    if janitor_file:
        janitor_handler = AIBatchHandler(api_key=Settings.GEMINI_JANITOR_KEY)
        job_id = janitor_handler.submit_batch_job(janitor_file, "Janitor", model=janitor.MODEL_NAME)
        print(f"✅ Submitted Janitor Job: {job_id}")

def run_batch_status():
    """List current status of all jobs for both keys."""
    keys_to_check = [
        ("Miner", Settings.GEMINI_MINER_KEY),
        ("Janitor", Settings.GEMINI_JANITOR_KEY)
    ]
    print("\n📋 [Gatekeeper] Current Batch Jobs Status:")
    print(f"{'Type':<10} | {'Name':<30} | {'Status':<15} | {'Created At'}")
    print("-" * 85)
    
    for prefix, key in keys_to_check:
        if not key: continue
        try:
            handler = AIBatchHandler(api_key=key)
            jobs = handler.client.batches.list()
            for job in jobs:
                status = str(job.state)
                created = str(job.create_time)
                print(f"{prefix:<10} | {job.display_name[:30]:<30} | {status:<15} | {created[:19]}")
        except Exception as e:
            print(f"⚠️ Error listing {prefix} jobs: {e}")

def run_batch_cancel(job_id: str):
    """Cancel and delete a batch job."""
    # Try finding and deleting the job with both keys
    keys_to_check = [Settings.GEMINI_MINER_KEY, Settings.GEMINI_JANITOR_KEY]
    
    for key in keys_to_check:
        if not key: continue
        try:
            handler = AIBatchHandler(api_key=key)
            # Check if job exists first
            try:
                job = handler.client.batches.get(name=job_id)
                print(f"🛑 Found Job {job.display_name} ({job.state}). Deleting...")
                handler.client.batches.delete(name=job_id)
                print(f"✅ Job {job_id} deleted successfully.")
                return
            except Exception:
                continue # Not found with this key, try next
        except Exception as e:
            print(f"⚠️ Error with key: {e}")
    
    print(f"❌ Job {job_id} not found or could not be deleted.")

def run_batch_collect():
    """Collect results from SUCCEEDED jobs for both Miner and Janitor."""
    # 1. Miner Collection
    if Settings.GEMINI_MINER_KEY:
        handler = AIBatchHandler(api_key=Settings.GEMINI_MINER_KEY)
        miner = AIMiner()
        jobs = handler.client.batches.list()
        for job in jobs:
            if (job.state == "SUCCEEDED" or "SUCCEEDED" in str(job.state)) and "Miner" in job.display_name:
                print(f"📥 [Gatekeeper] Collecting Miner Job: {job.display_name}")
                content = handler.get_job_results(job.name)
                if content:
                    miner.ingest_batch_results(content)
                    # Safe to delete Miner job if we want, but let's be cautious
                    # handler.client.batches.delete(name=job.name)

    # 2. Janitor Collection
    if Settings.GEMINI_JANITOR_KEY:
        handler = AIBatchHandler(api_key=Settings.GEMINI_JANITOR_KEY)
        janitor = TagNormalizer()
        jobs = handler.client.batches.list()
        for job in jobs:
            # ONLY collect if display_name contains 'Janitor'
            if (job.state == "SUCCEEDED" or "SUCCEEDED" in str(job.state)) and "Janitor" in job.display_name:
                print(f"📥 [Gatekeeper] Collecting Janitor Job: {job.display_name}")
                content = handler.get_job_results(job.name)
                if content:
                    # Save debug file ALWAYS for Janitor to be safe
                    timestamp = datetime.now().strftime("%H%M%S")
                    debug_path = Settings.INGEST_STAGING_DIR / f"debug_janitor_{timestamp}.jsonl"
                    with open(debug_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"   💾 Saved raw result to {debug_path}")
                    
                    janitor.ingest_batch_results(content)
                    # handler.client.batches.delete(name=job.name)

def main():
    parser = argparse.ArgumentParser(description="Scout App Gatekeeper CLI")
    subparsers = parser.add_subparsers(dest="command")

    # commands
    subparsers.add_parser("run", help="Live Scrape & Ingest").add_argument("asins", nargs="+")
    subparsers.add_parser("pending", help="Scrape Pending ASINs from CSV").add_argument("--limit", type=int, default=5)
    
    # Batch commands split
    miner_p = subparsers.add_parser("batch-submit-miner", help="Submit pending reviews to Miner")
    miner_p.add_argument("--limit", type=int, default=10000)
    
    subparsers.add_parser("batch-submit-janitor", help="Submit dirty aspects to Janitor")
    
    subparsers.add_parser("batch-collect", help="Collect results from Google Batch")
    subparsers.add_parser("batch-status", help="Check status of all Google Batch jobs")
    
    cancel_p = subparsers.add_parser("batch-cancel", help="Cancel a batch job")
    cancel_p.add_argument("job_id", help="Job Name (e.g. batches/xyz...)")

    subparsers.add_parser("reset", help="Reset stuck QUEUED items to PENDING")

    args = parser.parse_args()
    Settings.ensure_dirs()
    
    if args.command == "run":
        run_live_flow(args.asins)
    elif args.command == "pending":
        if STATUS_CSV.exists():
            df = pl.read_csv(STATUS_CSV, ignore_errors=True)
            pending = df.filter(pl.col("Status") == "Pending").head(args.limit)
            if pending.height > 0:
                run_live_flow(pending["Parent Asin"].to_list())
            else:
                print("✨ No pending ASINs.")
    elif args.command == "batch-submit-miner": run_batch_submit_miner(limit=args.limit)
    elif args.command == "batch-submit-janitor": run_batch_submit_janitor()
    elif args.command == "batch-collect": run_batch_collect()
    elif args.command == "batch-status": run_batch_status()
    elif args.command == "batch-cancel": run_batch_cancel(args.job_id)
    elif args.command == "reset":
        db_path = str(Settings.get_active_db_path())
        conn = duckdb.connect(db_path)
        conn.execute("UPDATE reviews SET mining_status = 'PENDING' WHERE mining_status = 'QUEUED'")
        print(f"✅ Reset all QUEUED reviews to PENDING on {db_path}.")
        conn.close()
    else: parser.print_help()

if __name__ == "__main__":
    main()
