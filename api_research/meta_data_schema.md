# Meta Data Schema & ETL Mapping
*Reference for Apify Scraper Output -> DB Mapping*

## 1. Facebook Ads (`apify/facebook-ads-scraper`)
*Primary Goal: Identify Winning Creatives & Angles.*

### Key JSON Fields (Verified CamelCase)
```json
{
  "adArchiveID": "123456789",          // Primary Key
  "startDate": "2025-12-01",           // CRITICAL: Calculate Duration
  "endDate": null,                     // If null & isActive=true -> Running
  "isActive": true,
  "publisherPlatforms": ["facebook", "instagram"],
  "adCreativeBody": "Stop sleeping hot! Try our cooling comforter...", // The Hook (Content)
  "adCreativeLinkTitle": "Shop Now - 50% OFF", // The Offer
  "adCreativeLinkUrl": "https://competitor.com/product-page", // Landing Page
  "adCreativeImageUrl": "https://scontent...", // Visual Asset (Download this)
  "adCreativeVideoUrl": "https://video...",    // Video Asset (Download this)
  "snapshotUrl": "https://www.facebook.com/ads/library/..." // Backup Link
}
```

### ETL Logic
1.  **Filter:** Only keep `isActive` = `true` OR (`endDate` - `startDate` > 30 days).
2.  **Download:** Fetch `adCreativeImageUrl` / `adCreativeVideoUrl` to Cloud Storage immediately.
3.  **Derived Metrics:** `duration_days` = `today` - `startDate`.

---

## 2. Instagram (`apify/instagram-scraper`)
*Primary Goal: Viral Trends (Reels) & Real Usage (Tagged UGC).*

### Key JSON Fields (Verified Mixed)
```json
{
  "id": "987654321",                   // Primary Key
  "shortCode": "CS7wn...",             // URL Slug
  "type": "Video",                     // Image, Video, Sidecar
  "displayUrl": "https://instagram...", // Thumbnail/Image
  "videoUrl": "https://instagram...",   // Video Source
  "caption": "Loving my new room setup! #cozy #dorm", // SEO/Hashtags
  "timestamp": "2026-01-14T10:00:00.000Z",
  "likesCount": 1500,
  "commentsCount": 45,
  "videoViewCount": 250000,            // Viral Metric
  "ownerUsername": "competitor_official",
  "taggedUsers": [                     // UGC Validation
    {"username": "happy_customer_123"}
  ]
}
```

### ETL Logic
1.  **Filter (Official):** Keep only `videoViewCount` > 50,000 (Viral) or `timestamp` < 7 days (New).
2.  **Filter (Tagged):** Keep ALL tagged posts (High value UGC).
3.  **Action:** Extract Hashtags from `caption`.

---

## 3. Cost Optimization Rules
*   **Facebook:** Input list of `pageIds`. Limit `resultsLimit: 30`.
*   **Instagram:** Input list of `usernames`.
    *   Set `resultsType: "posts"` (Limit 20).
    *   Set `resultsType: "tagged"` (Limit 20).
    *   **DISABLE** `search`, `comments`, `stories` (Waste of money).