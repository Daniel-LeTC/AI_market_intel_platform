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
    ACTOR_TIKTOK_FEED = "apidojo/tiktok-scraper" 
    ACTOR_TIKTOK_COMMENTS = "apidojo/tiktok-comments-scraper" # Cheaper & Better
    
    # Facebook Actors (Apify Official/Reliable)
    ACTOR_FB_HASHTAG = "apify/facebook-hashtag-scraper"
    ACTOR_FB_COMMENTS = "apify/facebook-comments-scraper"
    
    ACTOR_META_ADS = "curious_coder/facebook-ads-library-scraper"

    # Cost Config (USD per 1000 items)
    # Feed: Cheap ($0.30 / 1k)
    COST_TIKTOK_FEED_PER_1K = 0.30  
    COST_TIKTOK_COMMENTS_PER_1K = 0.30 # Matching ApiDojo pricing in research
    
    # Facebook is expensive due to anti-bot
    COST_FB_HASHTAG_PER_1K = 2.50
    COST_FB_COMMENTS_PER_1K = 1.50
    
    COST_META_ADS_PER_1K = 1.00

    def __init__(self, api_key: str = None, mock_mode: bool = False):
        self.api_key = api_key or DEFAULT_APIFY_TOKEN
        self.mock_mode = mock_mode
        if not mock_mode and not self.api_key:
            logger.warning("⚠️ No Apify Token provided. Forcing MOCK_MODE.")
            self.mock_mode = True
        else:
            self.client = ApifyClient(self.api_key) if not mock_mode else None

    def estimate_cost(self, platform: str, limit: int, task_type: str = "feed") -> float:
        """
        Returns estimated cost in USD.
        platform: 'tiktok', 'facebook', 'meta_ads'
        task_type: 'feed', 'comments'
        """
        if platform == "tiktok":
            rate = self.COST_TIKTOK_COMMENTS_PER_1K if task_type == "comments" else self.COST_TIKTOK_FEED_PER_1K
        elif platform == "facebook":
            rate = self.COST_FB_COMMENTS_PER_1K if task_type == "comments" else self.COST_FB_HASHTAG_PER_1K
        else:
            rate = self.COST_META_ADS_PER_1K
            
        return (limit / 1000.0) * rate

    def scrape_facebook_hashtag(self, keywords: List[str], limit: int = 20) -> pd.DataFrame:
        """
        TIER 1 (FB): Hashtag Search.
        """
        logger.info(f"⚡ [Facebook] Searching Hashtags: {keywords} (Limit: {limit})...")
        
        if self.mock_mode:
            return self._mock_fb_data(keywords[0], limit)

        try:
            # apify/facebook-hashtag-scraper schema FIXED
            run_input = {
                "keywordList": keywords, # Correct key based on Dry Run
                "resultsLimit": limit,
            }
            
            run = self.client.actor(self.ACTOR_FB_HASHTAG).call(run_input=run_input)
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            data = []
            for item in dataset_items:
                # Robust Mapping for Facebook (Schema varies by post type/actor version)
                
                # Text/Content
                text_content = (
                    item.get("postText") or 
                    item.get("content") or 
                    item.get("text")
                )
                
                # Fallback for Video/Reels without caption
                if not text_content and item.get("__typename") == "Video":
                    text_content = "[Video/Reel Media]"
                
                # Author
                author_name = item.get("author", {}).get("name") or item.get("user", {}).get("name") or item.get("video_owner", {}).get("name")
                
                # Metrics
                likes = item.get("like_count") or item.get("reactionsCount") or item.get("likes", 0) or item.get("play_count", 0) # Use play_count for reels/video as proxy if likes missing
                comments = item.get("comment_count") or item.get("commentsCount") or item.get("comments", 0)
                shares = item.get("share_count") or item.get("shares", 0)
                
                # URL
                post_url = item.get("permalink") or item.get("permalink_url") or item.get("url") or item.get("postUrl")
                
                data.append({
                    "platform": "facebook",
                    "post_id": str(item.get("postId") or item.get("id")),
                    "keyword": keywords[0],
                    "author": author_name,
                    "text": text_content,
                    "likes": likes,
                    "comments_count": comments,
                    "shares": shares,
                    "views": 0, # Not available in standard FB hashtag scrape usually
                    "url": post_url, 
                    "created_at": item.get("date") or item.get("time") or item.get("timestamp")
                })
            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"❌ [Facebook Hashtag] Failed: {e}")
            return pd.DataFrame()

    def scrape_instagram_hashtag(self, keywords: List[str], limit: int = 20) -> pd.DataFrame:
        """
        TIER 1 (IG): Hashtag Search.
        """
        logger.info(f"⚡ [Instagram] Searching Hashtags: {keywords} (Limit: {limit})...")
        
        if self.mock_mode:
            # Re-use mock fb logic for now or simple mock
            return self._mock_fb_data(keywords[0], limit)

        try:
            # apify/instagram-hashtag-scraper schema
            run_input = {
                "hashtags": keywords,
                "resultsLimit": limit,
                "resultsType": "posts"
            }
            
            run = self.client.actor("apify/instagram-hashtag-scraper").call(run_input=run_input)
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            data = []
            for item in dataset_items:
                data.append({
                    "platform": "instagram",
                    "id": item.get("id"),
                    "keyword": keywords[0],
                    "author": item.get("ownerUsername"),
                    "text": item.get("caption"),
                    "likes": item.get("likesCount", 0),
                    "comments_count": item.get("commentsCount", 0),
                    "url": item.get("url"),
                    "display_url": item.get("displayUrl"),
                    "date": item.get("timestamp")
                })
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"❌ [Instagram Hashtag] Failed: {e}")
            return pd.DataFrame()

    def scrape_facebook_comments(self, post_urls: List[str], max_comments: int = 20) -> pd.DataFrame:

        """
        TIER 2 (FB): Comment Deep Dive.
        """
        logger.info(f"⚡ [Facebook] Scraping Comments for {len(post_urls)} posts...")
        
        if self.mock_mode:
            return self._mock_fb_comments(len(post_urls), max_comments)

        try:
            # apify/facebook-comments-scraper schema
            run_input = {
                "startUrls": [{"url": u} for u in post_urls],
                "resultsLimit": max_comments * len(post_urls), 
                "includeNestedComments": False 
            }
            
            run = self.client.actor(self.ACTOR_FB_COMMENTS).call(run_input=run_input)
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            data = []
            for item in items:
                data.append({
                    "comment_id": str(item.get("id") or uuid.uuid4()),
                    "post_url": item.get("postUrl"), 
                    "platform": "facebook",
                    "author": item.get("profileName"),
                    "text": item.get("text"),
                    "likes": item.get("likesCount", 0),
                    "reply_count": 0, # Not available in simple scrape
                    "created_at": item.get("date"),
                    "sentiment": None
                })
            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"❌ [Facebook Comments] Failed: {e}")
            return pd.DataFrame()

    # --- MOCK DATA UPDATES ---
    def _mock_fb_data(self, keyword, limit):
        import random
        data = []
        for i in range(limit):
            data.append({
                "platform": "facebook",
                "post_id": f"fb_{random.randint(1000,9999)}",
                "keyword": keyword,
                "author": f"User {i}",
                "text": f"Loving this #{keyword} product! Highly recommend.",
                "likes": random.randint(10, 500),
                "comments_count": random.randint(0, 50),
                "shares": random.randint(0, 20),
                "views": 0,
                "url": "https://facebook.com/post/123",
                "created_at": "2025-01-15"
            })
        return pd.DataFrame(data)

    def _mock_fb_comments(self, num_posts, limit):
        data = []
        for _ in range(num_posts * limit):
            data.append({
                "comment_id": str(uuid.uuid4()),
                "post_url": "https://facebook.com/post/123",
                "platform": "facebook",
                "text": "How much is it?",
                "author": "Customer A",
                "likes": 2,
                "reply_count": 0,
                "created_at": "2025-01-16",
                "sentiment": None
            })
        return pd.DataFrame(data)

    def scrape_tiktok_comments(self, video_urls: List[str], max_comments_per_video: int = 20) -> pd.DataFrame:
        """
        TIER 2: Deep Dive (Voice of Customer).
        Scrapes comments from specific TikTok videos.
        """
        logger.info(f"⚡ [TikTok] Scraping Comments for {len(video_urls)} videos (Max {max_comments_per_video}/vid)...")
        
        if self.mock_mode:
            return self._mock_tiktok_comments(len(video_urls), max_comments_per_video)
            
        try:
            # Using apidojo/tiktok-comments-scraper (Correct one)
            # Schema: videoUrls (list), maxCommentsPerVideo (int)
            run_input = {
                "videoUrls": video_urls,
                "maxCommentsPerVideo": max_comments_per_video
            }
            
            run = self.client.actor(self.ACTOR_TIKTOK_COMMENTS).call(run_input=run_input)
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            data = []
            for item in items:
                data.append({
                    "comment_id": str(item.get("id") or uuid.uuid4()),
                    "post_url": item.get("videoWebUrl"), # Use videoWebUrl as linking key (not perfect but OK)
                    "platform": "tiktok",
                    "author": item.get("uniqueId"),
                    "text": item.get("text"),
                    "likes": item.get("diggCount"),
                    "reply_count": item.get("replyCount"),
                    "created_at": datetime.fromtimestamp(item.get("createTime", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                    "sentiment": None
                })
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"❌ [TikTok Comments] Failed: {e}")
            return pd.DataFrame()

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
            # Schema for apidojo/tiktok-scraper
            run_input = {
                "keywords": keywords,
                "maxItems": limit,
                "sortType": sort_type.upper(), # FIXED: Must be UPPERCASE
                "proxyConfiguration": {"useApifyProxy": True}
            }
            
            # Execute
            run = self.client.actor(self.ACTOR_TIKTOK_FEED).call(run_input=run_input)
            
            # Fetch
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            logger.info(f"✅ [TikTok] Retrieved {len(dataset_items)} items.")
            
            # Transform
            data = []
            for item in dataset_items:
                # Mapping generic fields (Adjust based on actual Apidojo output)
                # Dry Run Findings: 
                # title -> desc
                # webVideoUrl -> MISSING. Construct: https://www.tiktok.com/@{user}/video/{id}
                # channel -> author info
                
                author_name = item.get("channel", {}).get("name") or "unknown"
                video_id = item.get("id")
                
                data.append({
                    "platform": "tiktok",
                    "post_id": video_id,
                    "keyword": keywords[0],
                    "author": author_name,
                    "text": item.get("title"), # Dry run confirmed 'title' holds the caption
                    "views": item.get("views", 0),
                    "likes": item.get("likes", 0),
                    "shares": item.get("shares", 0),
                    "comments_count": item.get("comments", 0),
                    "created_at": item.get("uploadedAtFormatted", "") or item.get("uploadedAt"),
                    "url": f"https://www.tiktok.com/@{author_name}/video/{video_id}", # Constructed URL
                    # "music": item.get("song", {}).get("title"), # Removed from DB Schema to simplify
                    # "duration": 0 
                })
            
            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"❌ [TikTok] Failed: {e}")
            return pd.DataFrame()

    def _mock_tiktok_comments(self, num_vids, limit_per_vid):
        data = []
        for _ in range(num_vids * limit_per_vid):
            data.append({
                "comment_id": str(uuid.uuid4()),
                "post_url": "http://tiktok.com/mock_vid",
                "platform": "tiktok",
                "text": "This hack is amazing! Where to buy?",
                "author": "user_123",
                "likes": 50,
                "reply_count": 2,
                "created_at": "2025-01-19",
                "sentiment": None
            })
        return pd.DataFrame(data)


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
                "post_id": f"tt_{random.randint(100000,999999)}",
                "keyword": keyword,
                "author": f"creator_{random.randint(1,50)}",
                "text": f"Check out this #{keyword} trend! #viral",
                "views": views,
                "likes": int(views * 0.1),
                "shares": int(views * 0.01),
                "comments_count": random.randint(0, 50),
                "created_at": datetime.now().strftime("%Y-%m-%d"),
                "url": "https://tiktok.com",
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
