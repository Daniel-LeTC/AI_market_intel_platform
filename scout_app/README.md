# 🕵️ Market Intelligence Dashboard - UI Guide

Welcome to the frontend of the **Bright Scraper Tool**. This dashboard is designed for R&D, Content, and Growth teams to extract actionable insights from competitors.

---

## 🎨 Dashboard Features

### 1. Executive Summary (Tab 1)
- **Product DNA:** Real-time metadata (Brand, Material, Variation Counts) synced from DB.
- **KPI Cards:** High-level satisfaction metrics and review volume.

### 2. Customer X-Ray (Tab 2)
- **Impact Mode:** See which product aspects (Softness, Value, etc.) are driving satisfaction or pain.
- **🔥 Mass Analysis:** A Market Sentiment Heatmap for the Top 50 competitors. 
- **Quick Jump:** Click any ASIN in the detail table to switch context instantly.

### 3. Market Showdown (Tab 3) ⚔️
- **Battle Matrix:** Direct side-by-side comparison with a "Market Average" benchmark.
- **1% Sensitivity:** Highlighting even minor satisfaction gaps that matter at Amazon's scale.

### 4. Strategy Hub (Tab 4) 🕵️‍♂️
- **Detective Agent V4.4:** Chat with an AI analyst powered by **Gemini 3 Flash**.
- **Evidence Search:** Ask the agent to find specific quotes or summarize competitor flaws.

---

## 🛡️ Admin Console (Page 99)
For power users and data managers:
- **Hot Scrape:** Input ASINs to trigger Apify scraping immediately.
- **Staging Manager:** Review downloaded files before committing them to the database.
- **AI Controls:** Manually trigger the "Janitor" to clean up or unify product aspects.
- **💨 DB Vacuum:** Reclaim space and optimize performance with a single click.

---

## ⚙️ Technical Notes
- **Active DB:** The app automatically reads from the active Blue-Green database (`scout_a` or `scout_b`).
- **Real-time Sync:** All AI extractions and metadata updates reflect instantly on the UI without restarts.
- **Access Control:** Role-based access (ADMIN vs USER) ensures data safety.
