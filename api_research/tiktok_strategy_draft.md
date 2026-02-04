# TikTok Scraping Strategy: "Scout, Sniper & Rhythm"

## 1. Core Philosophy
- **Objective:** Monitor competitors, reverse-engineer their success, and discover market gaps.
- **Mantra:** "Metadata over Media" + "Context over Content".

## 2. The "Scout" Phase (Daily Monitoring)
- **Target:** List of known Competitor Profiles.
- **Scope:** Fetch Metadata of latest 30 videos.
- **Cost:** ~$0.1 per run (Cheap).
- **Metric:** `Relative Spike` = `Current Views` / `Channel Median Views`.
- **Viral Definition:** Any video where `Relative Spike >= 3.0` (3x normal performance).

## 3. The "Rhythm" Analysis (New Feature)
Don't just look at individual videos. Look at the **Time Delta** between uploads.

### Case A: The "Burst" (Spam/Campaign Mode)
- **Logic:** `Avg Time Gap < 24 hours`.
- **Behavior:** They are flooding the feed (e.g., 5 videos/day or a Series).
- **Scraper Action:**
    - DO NOT trigger alerts for every single video.
    - **Group** them into a "Batch".
    - Report: "Competitor posted a batch of 5 videos. Total Views: 500k. Best Performer: Video #3".
    - *Insight:* Detecting a new campaign launch.

### Case B: The "Machine" (Consistent)
- **Logic:** `Avg Time Gap = 1 - 3 days`.
- **Behavior:** Standard professional scheduling.
- **Scraper Action:** Standard monitoring. Alert on individual Viral spikes.

### Case C: The "Sniper" (Quality over Quantity)
- **Logic:** `Avg Time Gap > 7 days` (Rare uploads).
- **Behavior:** They only post high-production value content.
- **Scraper Action:**
    - **Immediate Alert** on ANY new upload (Viral or not).
    - *Insight:* If they move, it's usually something big (New Product or Big Promo).

---

## 4. The "Sniper" Phase (Deep Scan - Manager Approved)
Only triggered for **Viral Videos** or **Sniper Alerts**.

### The "Thread Miner" Strategy (Comment Logic)
We don't just scrape 1000 random comments. We mine the **Debates**.

1.  **Filter:** Sort by "Most Relevant" (Top).
2.  **The "Head & Shoulders" Rule:**
    - Scrape **Top 10 Root Comments** (The "Head").
    - Scrape **Top 3 Replies** for each Root (The "Shoulders").
    - *Total:* ~40 comments per viral video.
3.  **Cost Efficiency:**
    - Instead of 1000 junk comments ($1.00), we get 40 high-value comments ($0.04).
    - **ROI:** Extremely High.

### What to look for in Threads?
- **Debates:** "Why is X better than Y?" (Competitive Intel).
- **Complaints:** Replies often contain user validation of a defect ("Mine broke too!").
- **Pricing:** "Too expensive" vs "Worth it".

---

## 5. The "Dense Data" Framework
... (Kept from previous version)

## 6. The Missing Pieces (Advanced)
... (Kept from previous version)

## 7. Cost Estimation (Revised)
**Scenario:** Monitor 1 Competitor (Monthly).
- **Scout:** 30 runs x 30 videos = 900 items (~$3.00).
- **Sniper:** Detect 5 Viral Videos.
- **Thread Mine:** 5 videos x 50 comments = 250 comments (~$0.25).
- **Total Monthly Bill:** **~$3.50 per Competitor.**
- **Verdict:** Safe & Sustainable.

## 8. The "Delta Tracker" (Handling Dynamic Data)
*Challenge:* Views and Comments change over time. A single snapshot is misleading.
*Solution:* Re-scan old videos to calculate Velocity (Growth Rate).

### Implementation Requirement (Configurable Logic)
**Do NOT hardcode logic.** The "Boss" decides the rules. We build the switches.

**Configuration Variables (Must be in `config.yaml`):**
1.  `fresh_video_age_limit`: (Default: 3 days) -> Scan daily (High Frequency).
2.  `stale_video_age_limit`: (Default: 7 days) -> Scan every 3 days (Medium Frequency).
3.  `stop_tracking_age`: (Default: 30 days) -> Stop updating (Archive Mode).

*Note:* This increases daily request volume slightly (Old + New videos), but provides the vital "Growth Curve" chart.
