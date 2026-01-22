# 📋 Technical TODO: Pre-calculation & Refactoring

**Goal:** High Performance & Maintainable Codebase.

## ✅ Phase 1-4: Pre-calculation Architecture (Completed)
- [x] Schema `product_stats` created.
- [x] `StatsEngine` implemented.
- [x] Ingest Integration done.
- [x] Backfill completed (Note: Caused Lock issue, need fix for future).

## 🔄 Phase 5: UI Refactor & Optimization (Current Focus)
- [ ] **Fix Concurrency (Blue-Green Backfill):**
    - [ ] Update `scripts/backfill_stats_v1.py` to write to Standby DB and swap, avoiding UI locks.
- [ ] **Split Monolithic UI (`Market_Intelligence.py`):**
    - [ ] Create `scout_app/ui/common.py` (Shared helpers).
    - [ ] Create `scout_app/ui/tabs/overview.py` (Tab 1).
    - [ ] Create `scout_app/ui/tabs/xray.py` (Tab 2).
    - [ ] Create `scout_app/ui/tabs/showdown.py` (Tab 3).
    - [ ] Create `scout_app/ui/tabs/strategy.py` (Tab 4).
    - [ ] Refactor `Market_Intelligence.py` to be a lightweight orchestrator.

## 🔄 Phase 6: Clean Up
- [ ] Remove legacy SQL queries from `Market_Intelligence.py` once Refactor is stable.