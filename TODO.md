# 📝 Tactical Plan (TODO)

## Phase 1: Pre-calculation Architecture 🚀 [DONE]
- [x] Create `product_stats` table in DuckDB.
- [x] Implement `StatsEngine` (Sentiment, KPIs, Trends).
- [x] Integrate into `DataIngester` pipeline.
- [x] Run backfill script.

## Phase 2: UI Modularization & Performance 🛠️ [DONE]
- [x] Split monolithic UI into `scout_app/ui/tabs/`.
- [x] **PERFORMANCE VICTORY:** Implement `@st.fragment` for isolated re-runs.
- [x] Cache heavy DB queries (`get_precalc_stats`).
- [x] Fix Showdown Logic (Competitor selection bug).
- [x] Fix Strategy Hub UX (Disable input while thinking).

## Phase 3: Social Scout AI (Next) 🛰️ [TODO]
- [ ] Implement Trend Bridge (Keyword matching).
- [ ] Sentiment X-Ray (Visual drill-down).
- [ ] UI Integration in `05_Social_Scout.py`.
