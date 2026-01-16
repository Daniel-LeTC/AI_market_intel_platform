# Meta (Facebook/Instagram) Scraper: The "Laser Beam" Strategy
*Goal: High Density Data for R&D. Minimize cost ($). No Vanity Metrics.*

## 1. The Core Philosophy: "Ignore the Noise"
Facebook/Instagram APIs are expensive ($2-$5/1k posts). We cannot scrape everything like TikTok ($0.30).
**Rule:** Only scrape what validates the product or the marketing angle.

---

## 2. Facebook Strategy: "Follow The Money" (Ad Library)
*Context:* Organic posts on Brand Pages are dead/irrelevant. Do not scrape Page Feeds unless necessary.
*Target:* **Facebook Ad Library API** (Apify: `apify/facebook-ads-scraper` or similar).

### What to extract (The "Meat"):
| Field | Why it's Dense Data | Actionable Insight |
| :--- | :--- | :--- |
| **`startDate`** | **The Truth Teller.** If `startDate` > 30 days ago & `isActive`=True => **PROFITABLE**. | Copy this angle/creative immediately. |
| **`body` (Caption)** | Marketing Hook. Shows exactly what Pain Point they are selling. | Extract Keywords & USP (Unique Selling Point). |
| **`images`/`videos`** | Visual Strategy. | Download for "Creative Swipe File". Analyze: Lifestyle vs Studio? |
| **`publisherPlatforms`** | Where are they scaling? (FB vs IG vs Audience Network). | Platform Fit. |

### The "Laser Beam" Workflow:
1.  Input: Domain or Page Name of Competitor.
2.  Filter: `active_ads_only` = True.
3.  Sort: Longest running first.
4.  **Limit:** Top 20 Active Ads per Competitor. (No need for 1000s).
5.  **Estimated Cost:** Very Low (Ads Lib scrapers are usually fast & efficient).

---

## 3. Instagram Strategy: "Visual Reality" (Reels & UGC)
*Context:* Instagram is about Aesthetic & Real Usage.
*Target:* **Instagram Scraper** (Apify: `apify/instagram-scraper` or `jaroslav-kuchar/instagram-scraper`).

### Mode A: The "Product Photographer" (Official Feed)
*Scope:* Latest 15 Posts + Top 5 Most Liked of all time.
*   **`displayUrl` (Image):** Analyze color palette, props, lighting.
*   **`caption` (Hashtags):** Extract SEO Keywords (#comforter #dormdecor).
*   **`videoViewCount` (Reels):** If > 100k views => Viral Content. Download video for editing reference.

### Mode B: The "Reality Check" (Tagged Posts)
*Scope:* Latest 20 Tagged Posts.
*   **Why:** These are photos users took themselves.
*   **Insight:** Does the product look cheap in bad lighting? How do real messy rooms look with it?
*   **Action:** If `caption` contains negative keywords ("disappointed", "returned"), alert R&D.

---

## 4. Cost Control "Circuit Breakers"

1.  **No Comment Scraping (Default):**
    *   Comments on Meta are 80% spam/tagging friends. Expensive waste.
    *   **Exception:** Only scrape comments if `commentsCount > 50` AND `caption` contains specific keywords (e.g., "giveaway" - ignore, "launch" - scrape).

2.  **No Follower Scraping:**
    *   Useless metric. 1M followers means nothing if engagement is 0.

3.  **Frequency:**
    *   TikTok: Daily (Fast trend).
    *   Meta Ads: Weekly (Campaigns change slowly).
    *   Meta Feed: Weekly.

## 5. Implementation Roadmap (Draft)

1.  **Ad Library Tool:** Build a wrapper to fetch Active Ads JSON.
2.  **Visual Downloader:** Script to download Images/Videos from JSON URLs (store in cloud storage, not DB blobs).
3.  **Vision AI Layer (Optional Phase 2):** Use Gemini 3 Flash to look at the Ad Image and describe: "What is the key visual element?" (e.g., "Girl sleeping smiling", "Dog on bed").

---

## Summary
Instead of scraping **1,000 posts** ($3.00), we scrape **20 Ads + 20 Tagged Posts** per competitor.
**Total Volume:** ~50 records.
**Total Value:** Extremely High (Proven winners + Real feedback).
**Cost:** Negligible per competitor.
