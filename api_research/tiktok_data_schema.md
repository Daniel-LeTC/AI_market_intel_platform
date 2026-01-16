# TikTok Data Schema & ETL Mapping
*Reference for ApiDojo (Apify) Scraper Output -> DB Mapping*

## 1. Core Philosophy: "Trend & Viral Hunter"
TikTok is about speed and sound. We need to catch the "Audio Trend" and the "Visual Hook".

## 2. Target Actor: `apify/tiktok-scraper` (or ApiDojo equivalent)

### Key JSON Fields (Verified Snake_Case)
```json
{
  "post_id": "7324567890123456789",    // Primary Key
  "create_time": 1705344000,           // Unix Timestamp
  "description": "Check out this amazing dance challenge! #dancechallenge", // Caption
  "author": {
    "unique_id": "bedding_queen",
    "nickname": "Sarah Home",
    "avatar_thumb": "https://..."
  },
  "music": {
    "id": "7000000000000000000",
    "title": "Upbeat Pop Song",        // Audio Trend
    "play_url": "https://..."
  },
  "digg_count": 15000,                 // Likes (Validation)
  "share_count": 1200,                 // Virality Indicator
  "comment_count": 350,
  "play_count": 500000,                // Views (Reach)
  "video_url": "https://v16.tiktokcdn...", // Video URL (Download this!)
  "video_duration": 30
}
```

### ETL Logic

#### A. Trend Hunting (Hashtag Mode)
*   **Input:** Hashtags (e.g., `#comforter`, `#bedroommakeover`).
*   **Filter:** `play_count` > 100,000 (Only study viral videos).
*   **Action:**
    1.  Download `video_url` (Check watermark status).
    2.  Extract `music.title` -> Count frequency to find trending audio.
    3.  Extract Hashtags from `description`.

#### B. Competitor Monitor (User Mode)
*   **Input:** Competitor Usernames.
*   **Filter:** Latest 10 videos (sort by `create_time`).
*   **Action:**
    1.  Monitor `share_count` / `play_count` ratio (Viral Score).
    2.  If Viral Score > 1% (e.g. 10k shares / 1M views) -> "Winning Content".

---

## 3. Cost Optimization
*   **Volume:** Limit per run.
    *   Hashtag: Top 50 videos.
    *   User: Last 10 videos.
*   **Comments:** **SKIP**. Only extract `comment_count` for filtering.