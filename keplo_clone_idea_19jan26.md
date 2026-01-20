# Keplo Clone Idea (RnD Scout Upgrade Plan)
*Date: 19 Jan 2026*
*Source: Competitor Analysis (Keplo Scraper)*

## 🎯 Core Philosophy: "Conversion Club"
Turn raw data into **Actionable Briefs** & **Visual Assets**.

---

## 🛠️ Feature Mapping (Keplo vs. RnD Scout)

| Keplo Feature (The "Hype" Name) | RnD Scout Implementation (The "Real" Tool) | Status | Action Item |
| :--- | :--- | :--- | :--- |
| **Review Analysis** | **📊 Sentiment Radar** | ✅ Done | Rename current charts section. |
| **Raw Reviews** | **📝 Evidence Locker** | ✅ Done | Rename 'Latest Reviews' table. |
| **Priority Actions** | **🚨 Action Center** | ⚠️ Partial | Group 'Pain Points' into a dedicated 'Fix This Now' box. |
| **Deep Research** | **🕵️ Deep Detective** | ✅ Done | Enhance with "Buyer Persona" & "Purchase Barrier" prompts. |
| **Content Plan** | **✍️ Listing Architect** | ⏳ Planned | New Prompt: "Generate SEO Title/Bullets based on Pain Points". |
| **Demographics** | **👥 Persona Profiler** | ⏳ Planned | New Prompt: "Who is buying this? (Age/Gender/Use Case)". |
| **Rufus Analysis** | **🤖 Rufus Simulator** | ⏳ Planned | Use Gemini to simulate Rufus response based ONLY on scraped reviews. Goal: Predict what Amazon's AI will tell customers. |

---

## 🤖 The "Rufus Simulation" Logic (Bủ bủ Lmao Mode)
**Context:** Rufus is Amazon's shopping assistant. It "recommends" products based on review sentiment.
**Strategy:**
1.  **Input:** Customer Question (e.g., "Is this good for hot sleepers?").
2.  **Context Injection:** Provide Gemini with `Product DNA` + `Latest 50 Reviews` + `Key Pain Points`.
3.  **Prompt:** "Act as a shopping assistant. Based *strictly* on the provided reviews (do not hallucinate), answer if this product fits the user's needs. Highlight risks if reviews are negative."
4.  **Value:** R&D can see if their current "Review Health" is strong enough to win Rufus's recommendation.

---

## 🛠️ Feature Mapping (Keplo vs. RnD Scout)

### Step 1: Submit ASIN (The Gatekeeper)
*   **Current:** `Request New Competitor` (Sidebar).
*   **Upgrade:** Auto-detect Marketplace (US/UK/DE). Bulk Input support (Comma separated).

### Step 2: AI Analysis (The Engine)
*   **Current:** Miner + Janitor.
*   **Upgrade:** Real-time progress bar (already have Batch Status, need better UI visualization).

### Step 3: Get Insights (The Dashboard)
**Refactor `Market_Intelligence.py` Layout:**
1.  **Header:** Product DNA (Material, Brand, Target).
2.  **Section 1: The Scorecard (Priority Actions).**
    *   "3 things to fix immediately."
    *   "3 things customers love (Keep it)."
3.  **Section 2: The Battlefield (Competitor Comparison).**
    *   "Why they buy THEM instead of US?"
4.  **Section 3: The Deep Dive (Detective).**
    *   Prompt Hints: `Buyer Persona`, `Rufus Simulation`, `SEO Keywords`.

---

## 💡 Prompt Hints Strategy (The "Mớm" Feature)
Add clickable buttons in Chat Interface:
*   `🧠 Psychological Triggers`: "Why do people emotionally connect with this?"
*   `🚧 Purchase Barriers`: "What stops people from buying?"
*   `🤖 Rufus Check`: "Simulate an Amazon Rufus chat about this product."
*   `👥 Customer Avatar`: "Describe the typical user in detail."
*   `🔥 Roast My Product`: "Act as a brutal Gordon Ramsay. Roast this product based on its worst reviews. No mercy, just the harsh truth."

---

## 🔌 Platform Features
*   **Blue-Green DB:** Ensures 100% Uptime during analysis.
*   **Social Scout:** The "Secret Weapon" Keplo doesn't seem to highlight enough. (Hashtag Reverse Engineering).
*   **Instagram Scout:** The "Visual Goldmine". Scrape Hashtags & Reels. High noise ("Trash mixed with Gold") but invaluable for Visual Inspiration & Lifestyle Context.

---

## 💎 Advanced R&D Modules (RnD Scout Exclusives)

### 🏛️ Module 1: The Trend Bridge (Social-to-Amazon Sync)
**Concept:** Connect Viral Social Trends to Amazon Sourcing/Marketing opportunities.
1.  **AI Extraction:** Process `social_posts` captions to extract generic product keywords (e.g., "Egg Peeler").
2.  **Market Matching:** Cross-reference keywords with `products` table (Amazon ASINs).
3.  **Opportunity Score:** Identify products with "High Viral Views" on Social but "Low/Mediocre Ratings" on Amazon.
4.  **Value:** Early detection of "Winning Products" before they saturate the market. (The "Hunter" Mode).
*   **Challenges:** Matching logic requires Semantic Search (Vector DB) to map "teen code" on TikTok to complex Amazon Titles. Requires broad Amazon DB coverage.

### 🧬 Module 1.5: Social Sentiment X-Ray (Viral Context)
**Concept:** Determine *WHY* a post is viral (Positive vs. Negative Drama).
1.  **Input:** 50-100 Comments per Viral Post.
2.  **AI Analysis:**
    *   **Sentiment Map:** Positive/Negative/Neutral.
    *   **Viral Context:** Tag "🔥 Viral: BAD QUALITY" or "✨ Viral: CHEAP PRICE".
    *   **Word Cloud:** Visual representation of community buzz.
3.  **Value:** Prevents sourcing "Negative Viral" products (e.g., products famous for breaking easily).

### 🏰 Module 3: The Watchtower (Automated Health Monitor)
**Concept:** 24/7 Monitoring of Critical Assets (Proactive Alerts).
1.  **Pinning System:** Users MUST manually "📌 Pin" an ASIN to the Watchlist.
    *   **Quota:** Max 5 Pins per User (Prevent spam/budget drain).
2.  **Cron Logic:** Runs every **3 Days**.
    *   **Action:** Scrape only the latest **10 Reviews** (Low cost).
    *   **Diff Check:** Compare Review IDs. If no new data -> Sleep.
3.  **Health Check:**
    *   **Alert Condition:** If >30% of new reviews are Negative OR Rating drops >0.1.
    *   **Notification:** In-App Alert (or Telegram). "🚨 ASIN B0... just received 3 consecutive 1-star reviews!"
4.  **Storage:** Watchlist config stored in `system.duckdb` (User-linked).

### ✍️ Module 2: The Listing Architect (Pain-Point Driven Copywriting)
**Concept:** Generate conversion-optimized listings that proactively solve competitor weaknesses.
1.  **Insight Injection:** Pull `Top 5 Pain Points` (Negative Review Tags) from specific competitors in DB.
2.  **USP Alignment:** User inputs their own product's Unique Selling Points (e.g., "304 Stainless Steel").
3.  **AI Generation:** Create 5 Bullet Points using "Psychological Counter-Framing" (e.g., if competitor's product rusts, highlight our durability as the solution).
4.  **Value:** Directly translates R&D data into "Money-making" Content. (The "Architect" Mode).

---

## 🔐 System Security & Wallet Guard (The Gatekeeper V2)
**Goal:** Protect Company Intent (Secrecy) & Control API Costs (Budgeting).
*   **Architecture:** 
    *   `system.duckdb`: Critical data (Users, Auth, Current Budget). Lightweight & Fast.
    *   `logs.duckdb`: High-volume data (Chat History, Scrape Logs, Audit Trails). Optimized for Write-Heavy workload.
*   **User Management:**
    *   **Auth:** Anonymous **User ID + Password** login. User IDs are numeric/coded (e.g., `user_1001`).
    *   **Mapping:** Only Admin (the owner) holds the mapping of "User ID -> Real Person" externally.
    *   **Roles:** `Admin` (Approve requests, Top-up quota) vs `User` (Standard access).
    *   **Isolation:** Users only see their own scraping requests (prevent internal leaks).
        *   *Tech:* Link `scrape_queue.requested_by` to the anonymous `user_id`.
*   **Budget Control (Wallet Guard):**
    *   **Quota:** Each user gets a monthly limit (e.g., $20).
    *   **Pre-flight Check:** System blocks scraping if `Current Spend + Est Cost > Budget`.
    *   **Audit Logs:** Track who scraped what and when. "Who burned $50 on TikTok spam?" (Stored in `logs.duckdb`).
## 🗄️ Database Schema Implementation (Technical Ref)

### 1. `system.duckdb` (Security & Auth)
```sql
-- Anonymous Users
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR PRIMARY KEY, -- e.g., 'u1001'
    username VARCHAR UNIQUE,     -- e.g., '1001'
    password_hash VARCHAR,       -- bcrypt hash
    role VARCHAR DEFAULT 'USER', -- 'ADMIN' or 'USER'
    monthly_budget DOUBLE DEFAULT 20.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wallet & Quota Tracking
CREATE TABLE IF NOT EXISTS user_wallets (
    user_id VARCHAR PRIMARY KEY,
    current_spend DOUBLE DEFAULT 0.0,
    last_topup_date TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Watchtower Pin List
CREATE TABLE IF NOT EXISTS watchlist (
    pin_id VARCHAR PRIMARY KEY,
    user_id VARCHAR,
    asin VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### 2. `logs.duckdb` (Audit & History)
```sql
-- Scrape Audit (Money Tracking)
CREATE TABLE IF NOT EXISTS scrape_audit_logs (
    log_id VARCHAR PRIMARY KEY,
    user_id VARCHAR,
    platform VARCHAR,
    task_type VARCHAR,
    target VARCHAR,
    item_count INTEGER,
    cost_usd DOUBLE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat Intelligence Archive
CREATE TABLE IF NOT EXISTS chat_history (
    chat_id VARCHAR PRIMARY KEY,
    user_id VARCHAR,
    asin_context VARCHAR,
    user_query VARCHAR,
    ai_response VARCHAR,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```





