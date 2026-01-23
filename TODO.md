# 📝 Tactical Plan (TODO)

## Phase 3: Infrastructure Refactoring & Cleanup 🛠️ [COMPLETE]

### 1. Core Fortification
- [x] **Universal Ingest:** Handles Child ASINs, JSONL flattening, and Smart Upsert. (Done)
- [x] **Money-Safe Miner:** Pre-locking and Deduplication verified. (Done)
- [x] **Precise Janitor:** RAG Shield and Auto-trigger verified. (Done)
- [x] **Blue-Green Sync:** `manage.py` and Admin Console synchronized. (Done)

### 2. Admin Console & Housekeeping
- [x] **Archive Legacy Files:** Cleaned up `scripts/` and `upload_batch_*`. (Done)
- [x] **DB Maintenance UI:** Added Vacuum/Compaction button to Admin Console. (Done)
- [ ] **Background Progress UI:** Add status indicators for long-running jobs.

## Phase 4: Production Deployment (GCP) 🚀 [COMPLETE]

### 1. Docker & Infrastructure
- [x] **Dockerize Application:** Created `Dockerfile` and `docker-compose.prod.yml`.
- [x] **Optimization:** Reduced image size (~500MB) via `.dockerignore`.
- [x] **Deployment Scripts:** 
    - `deploy_build.sh` (Build & Push).
    - `deploy_remote.sh` (Remote Update).
    - `hot_patch_all.sh` (Fast Fix Code Injection).

### 2. Post-Deploy Stabilization
- [x] **Critical Bug Fixes:**
    - UI: Fixed `DeltaGenerator` magic error.
    - Common: Fixed `uuid` import error.
    - Worker: Added `/trigger/ingest` endpoint.

## Phase 5: Social Scout AI & UI Polish 🛰️ [NEXT]

### 1. Immediate UX Polish (Priority High)
- [ ] **Heatmap Revival (Strategy Tab):**
    - [ ] Restore missing Market Opportunity Heatmap.
    - [ ] Redesign for non-academic users (Simplified Visuals).
    - [ ] Explicit Calculation Logic (Tooltip/Legend).
- [ ] **Showdown Tab Refinement:**
    - [ ] Fix Legend Text (Sync 5% vs 1% threshold).
    - [ ] Add Color Coding (Green/Red background) for Winner/Loser columns.
    - [ ] Clarify "Market" column (Niche Average explanation).

### 2. Trend Bridge Engine (Social Scout)
- [ ] **Keyword Matching:** Map Amazon Aspects <-> Social Hashtags/Keywords.
- [ ] **Volume Correlation:** Overlay Social Volume on Amazon Sales Rank/Review Velocity.

### 3. Sentiment X-Ray
- [ ] **Social Sentiment:** Adapt `stats_engine` for TikTok/Meta comments.
- [ ] **Cross-Platform Dashboard:** Unified view of Amazon vs. Social sentiment.

## Backlog
- [ ] **Final DB Purge:** Delete `scout_fresh.duckdb` and Lab clones before Monday.
- [ ] **Load History from Disk:** Read from JSONL logs instead of DB for Chat history.
