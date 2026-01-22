# 📝 Tactical Plan (TODO)

## Phase 1 & 2 & 3 (Part 1): Done 🚀
- [x] Architecture, Performance, Tab 1 & Tab 2 (X-Ray).
- [x] Fixed `variation_count` bug.
- [x] Implemented "Estimated Customer Impact" logic.

## Phase 3: Refinement (Current) 🧐 [IN PROGRESS]

### Tab 3: Market Showdown [IN PROGRESS]
- [x] **Smart Matchmaking:** Implemented (Niche + Rating Count Match).
- [x] **UI Fix:** Pagination & Selection reset bug fixed.
- [ ] **Data Audit:** Wait for `recalc_all_stats.py` to finish, then sync `scout_a` to `scout_b`.
- [ ] **Weighted Comparison:** Upgrade Sentiment Comparison Chart to use "Estimated Impact" logic (Weighted % instead of Raw %).

### Tab 4: Strategy Hub [DONE]
- [x] **Refactor Prompt:** Tách prompt ra file `prompts.py`.
- [x] **Tune Persona:** Implemented "Anti-Múa" rules (Concise, Data-first, Actionable).
- [x] **Tool Upgrade:** Updated `get_product_dna` to use pre-calculated `product_stats`.

## Phase 4: Social Scout AI 🛰️ [PENDING]
- [ ] Implement Trend Bridge (Keyword matching).
- [ ] Sentiment X-Ray (Visual drill-down).