from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging
import os
import duckdb
import pandas as pd

from scout_app.core.social_scraper import SocialScraper
from scout_app.core.config import Settings
from scout_app.core.wallet import WalletGuard
from scout_app.core.logger import log_event

# --- Config ---
router = APIRouter(prefix="/social", tags=["Social Intelligence"])
logger = logging.getLogger("SocialWorker")

# --- Models ---
class SocialRequest(BaseModel):
    keywords: List[str]
    platform: str # 'tiktok', 'facebook', 'instagram', 'meta_ads'
    limit: int = 20
    sort_type: str = "RELEVANCE"
    country: str = "US"
    user_id: str = "api_user" # Default for now

class CommentRequest(BaseModel):
    video_urls: List[str]
    max_comments_per_video: int = 50
    platform: str = "tiktok"
    user_id: str = "api_user"

class CostCheckRequest(BaseModel):
    platform: str
    limit: int
    task_type: str = "feed" # 'feed' or 'comments'

# --- DB Helper ---
def ingest_to_db(df, table_name):
    if df.empty: return
    try:
        # Write to both A and B for redundancy
        dbs = [Settings.DB_SOCIAL_A, Settings.DB_SOCIAL_B]
        for db in dbs:
            with duckdb.connect(str(db)) as conn:
                conn.register('temp_df', df)
                conn.execute(f"INSERT INTO {table_name} BY NAME SELECT * FROM temp_df")
        logger.info(f"✅ Data ingested into Social DBs ({table_name})")
    except Exception as e:
        logger.error(f"❌ DB Ingest Failed: {e}")

# --- Logic Wrappers ---
def run_social_task(req: SocialRequest, estimated_cost: float):
    wallet = WalletGuard()
    platform_name = req.platform.upper()
    
    # Double check funds before execution (in case of race conditions or long queue)
    if not wallet.check_funds(req.user_id, estimated_cost):
        logger.warning(f"🚫 [{req.user_id}] Insufficient funds for {platform_name} task.")
        return

    logger.info(f"⚡ [{platform_name}] Starting Feed Scrape for {req.keywords} (Est Cost: ${estimated_cost})...")
    
    try:
        scraper = SocialScraper() 
        df = pd.DataFrame()

        if req.platform == "tiktok":
            df = scraper.scrape_tiktok_feed(req.keywords, limit=req.limit, sort_type=req.sort_type)
        elif req.platform == "facebook": 
             df = scraper.scrape_facebook_hashtag(req.keywords, limit=req.limit)
        elif req.platform == "instagram":
             df = scraper.scrape_instagram_hashtag(req.keywords, limit=req.limit)
        else: 
             df = scraper.scrape_meta_ads(req.keywords, limit=req.limit, country=req.country)

        if not df.empty:
            # Save Buffer CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"social_{req.platform}_feed_{timestamp}.csv"
            os.makedirs("staging_data", exist_ok=True)
            df.to_csv(f"staging_data/{filename}", index=False)
            
            # Ingest DB
            ingest_to_db(df, "social_posts")
            
            # CHARGE USER & LOG AUDIT
            wallet.charge_user(req.user_id, estimated_cost, {
                "type": "social_feed",
                "platform": req.platform,
                "keywords": req.keywords,
                "items": len(df)
            })
            
            # Detailed Audit Log
            log_event("scrape_audit", {
                "user_id": req.user_id,
                "platform": req.platform,
                "task": "feed",
                "target": str(req.keywords),
                "items_count": len(df),
                "cost_usd": estimated_cost,
                "status": "SUCCESS"
            })
            
    except Exception as e:
        logger.error(f"❌ [{platform_name}] Failed: {e}")
        log_event("scrape_audit", {
            "user_id": req.user_id,
            "platform": req.platform,
            "task": "feed",
            "error": str(e),
            "status": "FAILED"
        })

def run_comment_task(req: CommentRequest, estimated_cost: float):
    wallet = WalletGuard()
    platform_name = req.platform.upper()

    if not wallet.check_funds(req.user_id, estimated_cost):
        logger.warning(f"🚫 [{req.user_id}] Insufficient funds for Comments task.")
        return
    
    logger.info(f"⚡ [{platform_name}] Scraping Comments for {len(req.video_urls)} posts (Est Cost: ${estimated_cost})...")
    
    try:
        scraper = SocialScraper()
        df = pd.DataFrame()
        
        if req.platform == "tiktok":
            df = scraper.scrape_tiktok_comments(req.video_urls, max_comments_per_video=req.max_comments_per_video)
        elif req.platform == "facebook":
            df = scraper.scrape_facebook_comments(req.video_urls, max_comments=req.max_comments_per_video)
        
        if not df.empty:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"social_{req.platform}_comments_{timestamp}.csv"
            os.makedirs("staging_data", exist_ok=True)
            df.to_csv(f"staging_data/{filename}", index=False)
            
            ingest_to_db(df, "social_comments")
            
            # CHARGE USER
            wallet.charge_user(req.user_id, estimated_cost, {
                "type": "social_comments",
                "platform": req.platform,
                "video_count": len(req.video_urls)
            })

            log_event("scrape_audit", {
                "user_id": req.user_id,
                "platform": req.platform,
                "task": "comments",
                "items_count": len(df),
                "cost_usd": estimated_cost,
                "status": "SUCCESS"
            })
            
    except Exception as e:
        logger.error(f"❌ [{platform_name} Comments] Failed: {e}")
        log_event("scrape_audit", {
            "user_id": req.user_id,
            "platform": req.platform,
            "task": "comments",
            "error": str(e),
            "status": "FAILED"
        })

# --- Endpoints ---

@router.post("/estimate_cost") 
def estimate_cost_endpoint(req: CostCheckRequest):
    scraper = SocialScraper()
    cost = scraper.estimate_cost(req.platform, req.limit, req.task_type)
    return {
        "platform": req.platform,
        "items": req.limit,
        "task_type": req.task_type,
        "estimated_cost_usd": cost,
        "is_safe": cost < 5.0 
    }

@router.post("/trigger", status_code=202)
def trigger_social_scrape(req: SocialRequest, background_tasks: BackgroundTasks):
    if not req.keywords:
        raise HTTPException(status_code=400, detail="Keywords required.")
    
    # 1. Estimate Cost
    scraper = SocialScraper()
    est_cost = scraper.estimate_cost(req.platform, req.limit, "feed")
    
    # 2. Check Wallet
    wallet = WalletGuard()
    if not wallet.check_funds(req.user_id, est_cost):
        raise HTTPException(status_code=402, detail=f"Insufficient funds. Estimated cost: ${est_cost}")

    # 3. Queue Task
    background_tasks.add_task(run_social_task, req, est_cost)
    
    return {
        "status": "accepted", 
        "job": f"social_{req.platform}_feed", 
        "estimated_cost": est_cost,
        "wallet_check": "passed"
    }

@router.post("/trigger_comments", status_code=202)
def trigger_comment_scrape(req: CommentRequest, background_tasks: BackgroundTasks):
    if not req.video_urls:
        raise HTTPException(status_code=400, detail="Video URLs required.")
    
    # 1. Estimate Cost
    scraper = SocialScraper()
    est_cost = scraper.estimate_cost(req.platform, len(req.video_urls) * req.max_comments_per_video, "comments")

    # 2. Check Wallet
    wallet = WalletGuard()
    if not wallet.check_funds(req.user_id, est_cost):
        raise HTTPException(status_code=402, detail=f"Insufficient funds. Estimated cost: ${est_cost}")

    # 3. Queue Task
    background_tasks.add_task(run_comment_task, req, est_cost)
    
    return {
        "status": "accepted", 
        "job": "tiktok_comments", 
        "estimated_cost": est_cost,
        "wallet_check": "passed"
    }