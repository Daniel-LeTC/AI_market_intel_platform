# 📝 Tactical Plan (TODO)

## Phase 3: Production Deployment & Hardening (Current)
- [x] **Dockerize Application**
    - [x] Create `Dockerfile` (Unified).
    - [x] Create `docker-compose.prod.yml`.
    - [x] Optimize `.dockerignore`.
- [x] **GCP Deployment**
    - [x] Build & Push Scripts (`scripts/deploy_build.sh`).
    - [x] Remote Deploy Scripts (`scripts/deploy_remote.sh`).
    - [x] **Hot Patch Workflow** (`scripts/hot_patch_all.sh`) for fast iteration.
- [x] **Bug Fixing (Post-Deploy)**
    - [x] Fix `DeltaGenerator` error in `Market_Intelligence.py`.
    - [x] Fix `NameError: uuid` in `ui/common.py`.
    - [x] Fix Missing `/trigger/ingest` endpoint in `worker_api.py`.

## Phase 4: Social Scout AI (Next)
- [ ] **Trend Bridge Engine**
    - [ ] Keyword Matching Logic (Social vs Amazon).
    - [ ] Volume Correlation.
- [ ] **Sentiment X-Ray**
    - [ ] Social Sentiment Analysis.

## Backlog
- [ ] Admin Console: Progress Bars for Background Tasks.
- [ ] Load History from Disk (JSONL).
