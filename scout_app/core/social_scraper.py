import os
import logging
import pandas as pd
from datetime import datetime
from apify_client import ApifyClient
from typing import List, Dict, Optional, Union

# --- Config ---
DEFAULT_APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")

logger = logging.getLogger("SocialScraper")

class SocialScraper:
    """
    Unified Interface for Social Media Scraping via Apify.
    Supports: TikTok (ApiDojo), Meta (Ads Lib).
    Implements 'Multi-Tier Funnel' strategy for cost control.
    """
    
    # Actors ID Mapping
    ACTOR_TIKTOK_DOJO = "clockworks/tiktok-scraper" # Using robust one or ApiDojo equivalent
    # Note: ApiDojo is often under different ID, assuming standard public one for now or user provided.
    # Using the one from research: 5K30i8aFccKNF5ICs (The Scout) is good for posts.
    ACTOR_TIKTOK_SCOUT = "5K30i8aFccKNF5ICs" 
    
    ACTOR_META_ADS = "curious_coder/facebook-ads-library-scraper"

    # Cost Config (Safety Buffer Included)
    COST_TIKTOK_PER_1K = 0.50  # Est safety
    COST_META_PER_1K = 1.00    # Est safety

    def __init__(self, api_key: str = None, mock_mode: bool = False):
        self.api_key = api_key or DEFAULT_APIFY_TOKEN
        self.mock_mode = mock_mode
        if not mock_mode and not self.api_key:
            logger.warning("⚠️ No Apify Token provided. Forcing MOCK_MODE.")
            self.mock_mode = True
        else:
            self.client = ApifyClient(self.api_key) if not mock_mode else None

    def estimate_cost(self, platform: str, limit: int) -> float:
        """Returns estimated cost in USD."""
        rate = self.COST_TIKTOK_PER_1K if platform == "tiktok" else self.COST_META_PER_1K
        return (limit / 1000.0) * rate

    def scrape_tiktok_feed(self, 
                           keywords: List[str], 
                           limit: int = 50, 
                           sort_type: str = "RELEVANCE", # RELEVANCE, LIKE, DATE
                           publish_date: str = "ALL_TIME" # ALL_TIME, THIS_MONTH, etc.
                           ) -> pd.DataFrame:
        """
        TIER 1: Wide Scan (Trend Hunting).
        Scrapes TikTok posts by Keywords/Hashtags.
        """
        logger.info(f"⚡ [TikTok] Scanning Feed: {keywords} (Limit: {limit}, Sort: {sort_type})...")
        
        if self.mock_mode:
            return self._mock_tiktok_data(keywords[0], limit)

        try:
            # Schema for apidojo/tiktok-scraper (or equivalent)
            run_input = {
                "keywords": keywords,
                "maxItems": limit,
                "sortType": 0 if sort_type == "RELEVANCE" else 1, # Simplified mapping
                "proxyConfiguration": {"useApifyProxy": True}
            }
            
            # Execute
            run = self.client.actor(self.ACTOR_TIKTOK_SCOUT).call(run_input=run_input)
            
            # Fetch
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            logger.info(f"✅ [TikTok] Retrieved {len(dataset_items)} items.")
            
            # Transform
            data = []
            for item in dataset_items:
                # Mapping generic fields
                data.append({
                    "platform": "tiktok",
                    "id": item.get("id"),
                    "keyword": keywords[0],
                    "author": item.get("author", {}).get("uniqueId"),
                    "desc": item.get("text") or item.get("desc"),
                    "views": item.get("playCount", 0) or item.get("stats", {}).get("playCount", 0),
                    "likes": item.get("diggCount", 0) or item.get("stats", {}).get("diggCount", 0),
                    "shares": item.get("shareCount", 0) or item.get("stats", {}).get("shareCount", 0),
                    "created_at": datetime.fromtimestamp(item.get("createTime", 0)).strftime("%Y-%m-%d"),
                    "url": item.get("webVideoUrl") or item.get("video", {}).get("playAddr"),
                    "music": item.get("music", {}).get("title"),
                    "duration": item.get("video", {}).get("duration", 0)
                })
            
            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"❌ [TikTok] Failed: {e}")
            return pd.DataFrame()

    def scrape_meta_ads(self, 
                        keywords: List[str], 
                        limit: int = 20, 
                        country: str = "US",
                        active_status: str = "all" # active, all
                        ) -> pd.DataFrame:
        """
        TIER 2: Deep Dive (Competitor Ads).
        Scrapes Facebook Ads Library.
        """
        logger.info(f"⚡ [Meta] Spying Ads: {keywords} (Limit: {limit})...")

        if self.mock_mode:
            return self._mock_meta_data(keywords[0], limit)

        try:
            run_input = {
                "startUrls": [{"url": f"https://www.facebook.com/ads/library/?active_status={active_status}&ad_type=all&country={country}&q={k}&search_type=keyword_unordered&media_type=all"} for k in keywords],
                "maxItems": limit,
                "proxy": {"useApifyProxy": True}
            }

            run = self.client.actor("curious_coder/facebook-ads-library-scraper").call(run_input=run_input)
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            data = []
            for item in dataset_items:
                data.append({
                    "platform": "meta_ads",
                    "id": item.get("id"),
                    "keyword": keywords[0],
                    "page_name": item.get("pageName"),
                    "ad_body": item.get("adBody"),
                    "cta_type": item.get("ctaType"),
                    "media_type": item.get("mediaType"),
                    "start_date": item.get("startDate"),
                    "end_date": item.get("endDate"),
                    "platforms": ", ".join(item.get("publisherPlatforms", [])),
                    "url": item.get("adSnapshotUrl")
                })
            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"❌ [Meta] Failed: {e}")
            return pd.DataFrame()

    # --- MOCK DATA ---
    def _mock_tiktok_data(self, keyword, limit):
        import random
        data = []
        for i in range(limit):
            views = random.randint(10000, 5000000)
            data.append({
                "platform": "tiktok",
                "id": f"tt_{random.randint(100000,999999)}",
                "keyword": keyword,
                "author": f"creator_{random.randint(1,50)}",
                "desc": f"Check out this #{keyword} trend! #viral",
                "views": views,
                "likes": int(views * 0.1),
                "shares": int(views * 0.01),
                "created_at": datetime.now().strftime("%Y-%m-%d"),
                "url": "https://tiktok.com",
                "music": "Trending Sound",
                "duration": random.randint(15, 60)
            })
        return pd.DataFrame(data)

    def _mock_meta_data(self, keyword, limit):
        import random
        data = []
        for i in range(limit):
            data.append({
                "platform": "meta_ads",
                "id": f"ad_{random.randint(1000000,9999999)}",
                "keyword": keyword,
                "page_name": f"{keyword.capitalize()} Brand",
                "ad_body": f"Best {keyword} deals! Shop now.",
                "cta_type": "SHOP_NOW",
                "media_type": "Video",
                "start_date": "2025-01-01",
                "end_date": "2025-02-01",
                "platforms": "Facebook, Instagram",
                "url": "https://facebook.com/ads/library"
            })
        return pd.DataFrame(data)
