# 🚀 Bright Scraper Tool - Market Intelligence Platform

> **The All-in-One Amazon Market Intelligence & Social Trends Engine.**
> Leveraging **Gemini 2.5/3.0** for deep sentiment analysis, **DuckDB** for high-performance analytics, and **Streamlit** for an interactive, data-driven dashboard.

---

## 📖 Overview

The **Bright Scraper Tool** (internal codename: *Keplo Clone*) is a sophisticated market research platform designed to give sellers a competitive edge. It automates the collection, analysis, and visualization of product data from Amazon and social media trends from TikTok/Meta.

By combining deep scraping capabilities with advanced LLM agents, the system transforms raw review data into actionable strategy reports, "Detective" insights, and direct competitor showdowns.

---

## ✨ Key Features

### 1. 📊 Market Intelligence Dashboard
The core interface (`Market_Intelligence.py`) offers a 4-tab strategic view:
- **🏠 Executive Summary**: High-level KPIs, sales estimates, and rating distributions.
- **🔬 Customer X-Ray**: Deep dive into "Who," "What," and "Why" using AI analysis of thousands of reviews.
- **⚔️ Market Showdown**: Head-to-head comparison of product DNA, specs, and consumer sentiment.
- **🧠 Strategy Hub**: AI Chat interface with context-aware history to brainstorm marketing angles.

### 2. 🕵️ Detective Agent V2
An autonomous AI agent residing in the backend:
- **Loop Prevention**: Smart logic to avoid recursive tool calling.
- **Fact-Checking**: Cross-references claims against actual review data.
- **Context Awareness**: Remembers the current product context across chat sessions.

### 3. 📱 Social Scout
A dedicated module for off-Amazon intelligence:
- **Trend Bridge**: Maps Amazon keywords to social media hashtags.
- **WalletGuard**: Real-time budget tracking for Apify scraper costs.
- **Multi-Platform**: Supports TikTok and Meta (Facebook/Instagram) ad library scraping.

### 4. ⚙️ Robust Infrastructure
- **Blue-Green Deployment**: Zero-downtime updates using dual DuckDB databases (`scout_a` / `scout_b`).
- **Worker API**: Async FastAPI backend handling heavy lifting (scraping, mining, ingesting).
- **Admin Console**: Full control over scraping queues, job status, and database maintenance.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | Streamlit | Responsive, interactive dashboard UI. |
| **Database** | DuckDB | Embeddable OLAP database for fast analytical queries. |
| **AI/LLM** | Google Gemini | **3.0 Flash** (UI Agent) & **2.5 Flash Lite** (High-volume Mining). |
| **Scraping** | Apify | Scalable cloud scraping for Amazon & Social Media. |
| **Backend** | FastAPI | `worker_api.py` manages background tasks and queues. |
| **Container** | Docker | Full containerization for easy deployment. |

---

## 📂 Repository Structure

```graphql
bright_scraper_tool/
├── scout_app/                  # MAIN APPLICATION CODE
│   ├── Market_Intelligence.py  # 🚀 Entry Point (Streamlit Dashboard)
│   ├── core/                   # 🧠 Backend Logic Modules
│   │   ├── detective.py        # AI Agent & Tool definitions
│   │   ├── miner.py            # Review Mining & Sentiment Extraction
│   │   ├── ingest.py           # Data Ingestion & Upsert Logic
│   │   ├── auth.py             # User Authentication System
│   │   └── social_scraper.py   # TikTok/Meta Scraping Logic
│   ├── ui/                     # 🎨 UI Components & Widgets
│   │   ├── common.py           # Shared UI utilities
│   │   └── tabs/               # Tab implementations (Overview, X-Ray, etc.)
│   ├── pages/                  # 📄 Additional Streamlit Pages
│   │   ├── 05_Social_Scout.py  # Social Media Tracker
│   │   └── 99_Admin_Console.py # System Admin & Maintenance
│   └── database/               # Database connection helpers
├── scripts/                    # 🔧 Maintenance & Utility Scripts
│   ├── hot_patch_ui.sh         # Quick UI update script
│   └── worker_product_details.py # Standalone worker scripts
├── worker_api.py               # 🌐 FastAPI Worker Entry Point
├── manage.py                   # 📟 CLI Management Tool
├── docker-compose.yml          # Container configuration
└── requirements.txt            # Python dependencies
```

---

## 🚀 Installation & Setup

### 1. Prerequisites
- **Docker** & **Docker Compose**
- **Python 3.10+** (if running locally)
- API Keys for **Apify** and **Google Gemini**

### 2. Environment Configuration
Create a `.env` file in the root directory:
```bash
APIFY_TOKEN=your_apify_token
GEMINI_API_KEY=your_gemini_key          # For Smart Detective Agent
GEMINI_MINER_KEY=your_gemini_miner_key  # For Batch Mining (High Throughput)
ADMIN_PASSWORD=secure_password
```

### 3. Running with Docker (Recommended)
Launch the entire stack (UI + Worker):
```bash
docker compose up -d
```
- **Dashboard**: [http://localhost:8501](http://localhost:8501)
- **Worker API**: [http://localhost:8000](http://localhost:8000)

### 4. Running Locally (Development)
```bash
# Install dependencies
uv sync

# Run the Streamlit UI
uv run streamlit run scout_app/Market_Intelligence.py

# (Optional) Run the Worker API separately
uv run uvicorn worker_api:app --reload
```

---

## 📖 Walkthrough / Usage Guide

### 1️⃣ Login & Access
- Open the dashboard at `localhost:8501`.
- Login with your credentials. **Role-based access** ensures tailored views for Admins vs. Viewers.

### 2️⃣ Requesting a New Product
1. Go to the **Sidebar** > **Request New ASIN**.
2. Enter the Amazon ASIN (e.g., `B08XYZ123`).
3. (Optional) Check **Force Update** to re-scrape fresh data.
4. Click **Submit**. The `Worker` will pick up the job, scrape data via Apify, run the AI Miner, and ingest it into the active DB.

### 3️⃣ Analyzing Data
Once data is ready, select the product from the sidebar dropdown.
- **Executive Summary**: Check the "Rating Bias" chart to see if reviews are manipulated.
- **Customer X-Ray**: Read the "Purchase Drivers" to understand why people buy.
- **Strategy Hub**: Chat with the **Detective Agent**.
    - *Example Query:* "Compare the negative feedback of this product vs. the main competitor."

### 4️⃣ Admin Maintenance
- Use the **Admin Console** (Page 99) to monitor the **Scrape Queue**.
- Run `python manage.py reset` if jobs get stuck.
- Check `detective_audit.log` for detailed AI agent traces.
