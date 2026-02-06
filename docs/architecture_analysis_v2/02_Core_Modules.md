# System Architecture: Logic Clusters

This document provides a high-level summary of the system's logical groupings. For detailed line-by-line analysis, refer to the `code_deep_dive/` directory.

## 1. Acquisition Cluster
*Handling the intake of raw data from the external world.*
- **Scrapers:** `AmazonScraper` (Deep 5-star split), `SocialScraper` (Multi-platform).
- **Orchestration:** `worker_api.py` manages async dispatch; `scripts/worker_*.py` handle browser automation.
- **Wallet:** `WalletGuard` ensures budget compliance before any paid API call.
- **👉 Deep Dive:** `core_scraping_wallet.md`, `worker_orchestration.md`.

## 2. Ingestion & Storage Cluster
*Cleaning, structuring, and persisting data.*
- **Ingestion:** `DataIngester` implements the "Blue-Green" deployment strategy for zero downtime.
- **Normalization:** `MetadataParser` standardizes messy scraper JSON (Apify) into a strict Schema.
- **Schema:** 3-Database Architecture (`scout`, `social`, `system`).
- **👉 Deep Dive:** `core_ingest.md`, `core_migrations.md`, `05_Database_ERD_and_Usage.md`.

## 3. Intelligence Cluster (The Brain)
*Transforming raw text into structured insights using AI.*
- **Miner:** Extracts Aspect/Sentiment tags from reviews. Uses Regex-Repair for robust JSON parsing.
- **Janitor (`TagNormalizer`):** Standardizes synonyms (e.g., "soft", "softness" -> "Softness") using a RAG Shield.
- **Detective:** Interactive Agent with Tool-Use capabilities and strict "Persona" rules.
- **👉 Deep Dive:** `core_ai.md`.

## 4. Analytical Cluster
*Calculating metrics and rendering insights.*
- **StatsEngine:** The OLAP layer. Implements "Weighted Extrapolation" to fix sample bias.
- **UI Tabs:** `X-Ray` (Market Heatmap), `Showdown` (Proven Quality referee), `Overview` (DNA Mapping).
- **👉 Deep Dive:** `core_stats_engine.md`, `ui_analytical_tabs.md`.

## 5. Operations Cluster
*Keeping the lights on.*
- **Batch Processing:** `ai_batch.py` & `manage.py` handle cost-effective async AI jobs on Google Cloud.
- **Maintenance:** Deduplication, Vacuuming, and Syncing.
- **👉 Deep Dive:** `ops_and_utils.md`, `auxiliary_scripts.md`.
