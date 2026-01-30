# TASK: Fix Product Stats Schema and Recalc Logic
- Target: `scout_app/database/`, `scout_app/core/stats_engine.py`
- Logic:
    1. Recreate `product_stats` table with `asin` as PRIMARY KEY to support `ON CONFLICT` upserts.
    2. Ensure `StatsEngine` handles NULLs in `real_total_ratings` and `rating_breakdown` more gracefully.
    3. Verify why `calculate_sentiment_weighted` returns empty for new ASINs.
- Constraint: Use Blue-Green migration strategy if applying to production.
