# 📋 Technical TODO: Pre-calculation & Refactoring

**Goal:** High Performance & Maintainable Codebase.

## ✅ Phase 1-4: Pre-calculation Architecture (Completed)
- [x] Schema `product_stats` created.
- [x] `StatsEngine` implemented.
- [x] Ingest Integration done.
- [x] Backfill completed.

## ✅ Phase 5: UI Refactor & Optimization (Completed)
- [x] **Fix Concurrency:** Updated `scripts/backfill_stats_v1.py` to use Blue-Green deployment.
- [x] **Split Monolithic UI:**
    - [x] Created `scout_app/ui/common.py`.
    - [x] Created `scout_app/ui/tabs/overview.py`.
    - [x] Created `scout_app/ui/tabs/xray.py`.
    - [x] Created `scout_app/ui/tabs/showdown.py`.
    - [x] Created `scout_app/ui/tabs/strategy.py`.
    - [x] Refactored `Market_Intelligence.py`.

## ✅ Phase 6: Clean Up (Completed)
- [x] Removed legacy SQL queries from `Market_Intelligence.py` (via refactor).
