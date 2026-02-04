# TASK: Rebuild Products Table (Parent-Centric Model)
- Goal: Restore `products` table to exactly ~1,047 parents.
- Logic:
    1. **Products Table:** ONLY store entries where `asin == parent_asin`. 
    2. **Ingest Strategy:** When processing 10k variants, only save/update the metadata for the Parent ASIN.
    3. **Review Linkage:** Ensure EVERY review has a correct `parent_asin`. All reviews of children (variants) are aggregated under their single parent.
- Steps:
    1. Backup current `scout_a.duckdb`.
    2. TRUNCATE `products` table.
    3. Ingest Comforter Metadata (902 parents) from `Kid Comforter Set_Thoai RnD_19-12-2025.xlsx` (Taking one representative row per Parent Asin).
    4. Ingest Books/Tumblers Metadata (145 parents) from JSONL files.
    5. Integrity Check: Verify `products` row count is exactly ~1,047.
    6. Sync: Update `scout_b` to match.
