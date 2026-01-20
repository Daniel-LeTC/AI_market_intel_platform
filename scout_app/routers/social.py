from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging
import os

from scout_app.core.social_scraper import SocialScraper

# --- Config ---
router = APIRouter(prefix="/social", tags=["Social Intelligence"])
logger = logging.getLogger("SocialWorker")

# --- Models ---
class SocialRequest(BaseModel):
    keywords: List[str]
    platform: str # 'tiktok' or 'meta_ads'
    limit: int = 20
    sort_type: str = "RELEVANCE"
    country: str = "US"

class CostCheckRequest(BaseModel):
    platform: str
    limit: int
    task_type: str = "feed" # 'feed' or 'comments'

class CommentRequest(BaseModel):
    video_urls: List[str]
    max_comments_per_video: int = 50
    platform: str = "tiktok"

from scout_app.core.config import Settings
import duckdb

# --- DB Helper ---
def get_social_db():
    # Simple strategy: Sync with Main DB active state or default to A
    # For now, just write to BOTH to be safe/simple (since we don't have a separate pointer yet)
    # Or better: Just write to A and B. It's low volume.
    return str(Settings.DB_SOCIAL_A)

def ingest_to_db(df, table_name):
    if df.empty: return
    try:
        # Write to both A and B for redundancy since we don't switch them often
        dbs = [Settings.DB_SOCIAL_A, Settings.DB_SOCIAL_B]
        for db in dbs:
            with duckdb.connect(str(db)) as conn:
                # Use "INSERT INTO ... BY NAME" for flexible column mapping
                conn.register('temp_df', df)
                conn.execute(f"INSERT INTO {table_name} BY NAME SELECT * FROM temp_df")
        logger.info(f"✅ Data ingested into Social DBs ({table_name})")
    except Exception as e:
        logger.error(f"❌ DB Ingest Failed: {e}")

# --- Logic Wrappers ---
def run_social_task(req: SocialRequest):
    platform_name = "TikTok" if req.platform == "tiktok" else "Meta Ads"
    logger.info(f"⚡ [{platform_name}] Starting Feed Scrape for {req.keywords} (Limit: {req.limit})...")
    try:
        scraper = SocialScraper() 
        if req.platform == "tiktok":
            df = scraper.scrape_tiktok_feed(req.keywords, limit=req.limit, sort_type=req.sort_type)
        elif req.platform == "facebook": # Corrected from meta_ads for Hashtag
             df = scraper.scrape_facebook_hashtag(req.keywords, limit=req.limit)
        elif req.platform == "instagram":
             df = scraper.scrape_instagram_hashtag(req.keywords, limit=req.limit)
        else: # Meta Ads or Fallback
             df = scraper.scrape_meta_ads(req.keywords, limit=req.limit, country=req.country)

        if not df.empty:
            # Save CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"social_{req.platform}_feed_{timestamp}.csv"
            os.makedirs("staging_data", exist_ok=True)
            df.to_csv(f"staging_data/{filename}", index=False)
            
            # Ingest DB
            ingest_to_db(df, "social_posts")
            
    except Exception as e:
        logger.error(f"❌ [{platform_name}] Failed: {e}")

def run_comment_task(req: CommentRequest):
    platform_name = "TikTok" if req.platform == "tiktok" else "Facebook"
    logger.info(f"⚡ [{platform_name}] Scraping Comments for {len(req.video_urls)} posts...")
    
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
            
            # Ingest DB
            ingest_to_db(df, "social_comments")
            
    except Exception as e:
        logger.error(f"❌ [{platform_name} Comments] Failed: {e}")

# --- Endpoints ---

@router.post("/estimate_cost") 
def estimate_cost(req: CostCheckRequest):
    """
    Calculate cost BEFORE running.
    """
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
    """
    Launch Feed Scraping Job.
    """
    if not req.keywords:
        raise HTTPException(status_code=400, detail="Keywords required.")
    background_tasks.add_task(run_social_task, req)
    return {"status": "accepted", "job": f"social_{req.platform}_feed", "target": req.keywords}

@router.post("/trigger_comments", status_code=202)
def trigger_comment_scrape(req: CommentRequest, background_tasks: BackgroundTasks):
    """
    Launch Comment Scraping Job.
    """
    if not req.video_urls:
        raise HTTPException(status_code=400, detail="Video URLs required.")
    background_tasks.add_task(run_comment_task, req)
    return {"status": "accepted", "job": "tiktok_comments", "target_count": len(req.video_urls)}
