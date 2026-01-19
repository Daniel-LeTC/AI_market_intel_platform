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

# --- Logic Wrappers ---
def run_social_task(req: SocialRequest):
    platform_name = "TikTok" if req.platform == "tiktok" else "Meta Ads"
    logger.info(f"⚡ [{platform_name}] Starting Scrape for {req.keywords} (Limit: {req.limit})...")
    try:
        scraper = SocialScraper() # Token auto loaded from env
        if req.platform == "tiktok":
            df = scraper.scrape_tiktok_feed(req.keywords, limit=req.limit, sort_type=req.sort_type)
        elif req.platform == "meta_ads":
            df = scraper.scrape_meta_ads(req.keywords, limit=req.limit, country=req.country)
        else:
            logger.error(f"❌ Unknown Platform: {req.platform}")
            return

        if not df.empty:
            # Save to staging
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"social_{req.platform}_{timestamp}.csv"
            
            # Ensure staging dir exists
            staging_dir = "staging_data"
            os.makedirs(staging_dir, exist_ok=True)
            
            save_path = f"{staging_dir}/{filename}"
            df.to_csv(save_path, index=False)
            logger.info(f"✅ [{platform_name}] Data saved to: {save_path} ({len(df)} rows)")
        else:
            logger.warning(f"⚠️ [{platform_name}] No data found.")
            
    except Exception as e:
        logger.error(f"❌ [{platform_name}] Failed: {e}")

# --- Endpoints ---

@router.post("/estimate_cost") # Will be mounted as /social/estimate_cost
def estimate_cost(req: CostCheckRequest):
    """
    Calculate cost BEFORE running.
    """
    scraper = SocialScraper()
    cost = scraper.estimate_cost(req.platform, req.limit)
    return {
        "platform": req.platform,
        "items": req.limit,
        "estimated_cost_usd": cost,
        "is_safe": cost < 5.0 # Warning threshold
    }

@router.post("/trigger", status_code=202) # /social/trigger
def trigger_social_scrape(req: SocialRequest, background_tasks: BackgroundTasks):
    """
    Launch Social Scraping Job.
    """
    if not req.keywords:
        raise HTTPException(status_code=400, detail="Keywords required.")
    
    background_tasks.add_task(run_social_task, req)
    return {"status": "accepted", "job": f"social_{req.platform}", "target": req.keywords}
