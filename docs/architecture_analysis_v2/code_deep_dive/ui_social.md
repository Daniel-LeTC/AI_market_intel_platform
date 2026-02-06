# Code Deep Dive: Social Scout Module (`routers/social.py`, `SocialScraper`)

**Role:** The Social Intelligence Layer.
**Responsibility:** Fetching, processing, and monetizing Social Media data (TikTok, Meta).

---

## 1. `SocialRouter` (`scout_app/routers/social.py`)
**Role:** The API Gateway for Social Tasks.

### Atomic Logic: "The Pay-to-Play Pipeline"
1.  **Estimation (Pre-flight):** 
    - Endpoint `/estimate_cost` calls `SocialScraper.estimate_cost`.
    - Purpose: UI can show users "This will cost $0.50" *before* they click run.
2.  **Wallet Gatekeeping (Sync):**
    - Endpoint `/trigger` checks `WalletGuard.check_funds(user_id, cost)` *synchronously*.
    - If insufficient funds -> Returns `402 Payment Required` immediately. Prevents queue spamming.
3.  **Task Execution (Async):**
    - Pushes task to `BackgroundTasks`.
    - **Execution Flow:**
        1.  **Re-check Funds:** (Double check inside thread to prevent race conditions).
        2.  **Scrape:** Calls `SocialScraper`.
        3.  **Ingest:** Saves to `social_posts` table (writes to both Blue/Green DBs for safety).
        4.  **Charge:** Calls `WalletGuard.charge_user()` *after* successful data acquisition.
        5.  **Audit:** Logs detailed transaction to `scrape_audit`.

---

## 2. `SocialScraper` (`scout_app/core/social_scraper.py`)
**Role:** The Multi-Platform Fetcher.

### Atomic Logic
- **Cost Calculator:**
    - TikTok Feed: $0.30 / 1k items.
    - Facebook Hashtag: $2.50 / 1k items (Premium due to anti-bot).
- **Platform Normalization:**
    - Maps diverse JSON schemas (TikTok API vs Facebook Graph) into a unified DataFrame structure:
    - `[post_id, platform, author, text, likes, comments_count, shares, url, created_at]`.

### Dependency Graph
- **Called By:** `routers/social.py`.
- **Calls:** `ApifyClient` (ApiDojo & Official Actors).
- **Data Flow:** Returns `pd.DataFrame` -> Ingested by Router.

---

## 3. `Social Scout UI` (`scout_app/pages/05_Social_Scout.py`)
**Status:** 🚧 Under Construction.
- Currently a placeholder page redirecting users back to the main dashboard while the backend is being refactored.
