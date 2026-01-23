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

## Phase 4: Social Scout AI & Polish 🛰️ [NEXT]

### 1. Trend Bridge
- [ ] Implement Keyword Matching between Amazon Sentiment and Social Trends.
- [ ] "Sentiment X-Ray" for TikTok/Meta comments.

### 2. Deployment Prep
- [ ] **Final DB Purge:** Delete `scout_fresh.duckdb` and Lab clones before Monday.
- [ ] GCP VM Deployment config audit.