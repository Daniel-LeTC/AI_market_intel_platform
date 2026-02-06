# Code Deep Dive: Scraping & Wallet (`scraper.py`, `social_scraper.py`, `wallet.py`)

**Role:** The Acquisition Layer.
**Responsibility:** Fetching external data (Amazon, Social Media) and managing the financial cost of these operations.

---

## 1. `AmazonScraper` (`scout_app/core/scraper.py`)
**Role:** The E-commerce Fetcher. Wraps Apify's Amazon Scraper.

### Atomic Logic: "The 5-Star Split Strategy"
- **Problem:** Amazon UI limits review visibility (usually ~100 per page, max 10 pages). Scraping "All Reviews" often gets capped.
- **Solution:** Instead of one big scrape, the scraper splits the job into 5 parallel sub-tasks:
    - Scrape 5-star only.
    - Scrape 4-star only.
    - ...
    - Scrape 1-star only.
- **Result:** Maximize yield per ASIN.
- **Output:** Downloads a raw XLSX file to `staging_data/`.

---

## 2. `SocialScraper` (`scout_app/core/social_scraper.py`)
**Role:** The Social Media Fetcher. Wraps multiple Apify Actors (TikTok, Meta).

### Key Logic & Atomic Functions
- **Multi-Platform Support:** Unified interface for TikTok (ApiDojo) and Facebook/Instagram (Official Apify Actors).
- **Cost Estimation (`estimate_cost`)**:
    - Returns estimated USD cost based on platform and limit.
    - Used by UI to warn users before execution.
- **Mock Mode:** If `APIFY_TOKEN` is missing, returns fake data (critical for local dev/testing without credit card).
- **Data Normalization:** Maps platform-specific fields (e.g., `like_count`, `reactionsCount`, `likes`) into a unified schema (`likes`, `comments_count`, `shares`).

---

## 3. `WalletGuard` (`scout_app/core/wallet.py`)
**Role:** The Financial Controller. Prevents budget overruns.

### Atomic Logic
- **Database:** Connects to `system.duckdb` (Separate from Application Data DB).
- **`check_funds(user_id, cost)`**: Read-only check.
- **`charge_user(user_id, cost, details)`**:
    - **Atomic Update:** `UPDATE user_wallets SET current_spend = current_spend + ?`
    - **Audit Log:** Writes JSONL log via `log_event`.

### Dependency Graph
- **Called By:** `miner.py` (before AI calls), `social_scraper.py` (logic embedded in UI triggers).
- **Side Effects:** Writes to `system.duckdb`, `logs/`.
