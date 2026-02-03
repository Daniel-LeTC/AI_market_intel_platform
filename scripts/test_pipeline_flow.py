import json
import duckdb
import pandas as pd
from pathlib import Path
from scout_app.core.ingest import DataIngester
from scout_app.core.stats_engine import StatsEngine
from scout_app.core.config import Settings

# --- TEST CONFIG ---
TEST_ASIN = "TEST999PIPELINE"
TEST_JSONL = Path("staging_data_local/test_pipeline.jsonl")
DB_PATH = Settings.get_active_db_path()


def setup_mock_data():
    """Create a mock JSONL file for metadata ingest."""
    # This matches the Apify structure seen in 39_asin.jsonl
    mock_item = {
        "asin": TEST_ASIN,
        "title": "Pipeline Test Product - DO NOT BUY",
        "manufacturer": "TEST BRAND",
        "imageUrlList": ["https://example.com/image.jpg"],
        "productRating": None,  # MOCK NAN/NULL RATING
        "countReview": 0,  # MOCK 0 REVIEWS
        "statusCode": 200,
        "statusMessage": "FOUND",
    }
    with open(TEST_JSONL, "w") as f:
        f.write(json.dumps(mock_item) + "\n")
    print(f"✅ Created mock JSONL: {TEST_JSONL}")


def run_test():
    print(f"🚀 Starting Pipeline Flow Test for ASIN: {TEST_ASIN}")

    # 1. SETUP
    setup_mock_data()
    ingester = DataIngester()
    engine = StatsEngine()

    try:
        # 2. INGEST METADATA
        print("📥 Step 1: Ingesting Metadata...")
        ingester.ingest_file(TEST_JSONL)

        # RE-OPEN CONNECTION TO GET NEW ACTIVE DB
        active_db = Settings.get_active_db_path()
        print(f"🔗 Re-opening connection to new Active DB: {active_db}")
        conn = duckdb.connect(str(active_db))

        # Verify metadata ingested
        res_p = conn.execute(
            "SELECT brand, title, real_average_rating FROM products WHERE asin = ?", [TEST_ASIN]
        ).fetchone()
        print(f"   Check products: {res_p}")

        if not res_p:
            # Maybe it went to product_parents but not products yet? (Rescued logic)
            res_pp = conn.execute(
                "SELECT brand, title FROM product_parents WHERE parent_asin = ?", [TEST_ASIN]
            ).fetchone()
            print(f"   Check product_parents: {res_pp}")
            # If it's missing in products, we can't test sync yet.
            # Ingester should have put it in products if metadata was found.
            # But Apify structure might be different.

        # 3. INGEST MOCK REVIEWS
        print("📥 Step 2: Injecting Mock Reviews...")
        mock_reviews = [
            ("R1_TEST", TEST_ASIN, 5.0, "Amazing quality and very soft material.", "2026-01-01"),
            ("R2_TEST", TEST_ASIN, 1.0, "Terrible packaging, arrived damaged.", "2026-01-02"),
        ]
        # Ensure we have a product record to avoid FK violation if products table was empty
        check_p = conn.execute("SELECT count(*) FROM products WHERE asin = ?", [TEST_ASIN]).fetchone()[0]
        if check_p == 0:
            print("   ⚠️ Product missing from 'products' table. Force creating to satisfy FK for testing.")
            conn.execute(
                "INSERT INTO products (asin, parent_asin, brand, title, category) SELECT parent_asin, parent_asin, brand, title, category FROM product_parents WHERE parent_asin = ?",
                [TEST_ASIN],
            )

        conn.executemany(
            """
            INSERT INTO reviews (review_id, parent_asin, rating_score, text, review_date, mining_status)
            VALUES (?, ?, ?, ?, ?, 'PENDING')
        """,
            mock_reviews,
        )

        # 4. INGEST MOCK TAGS (Simulating AI Miner)
        print("🧠 Step 3: Injecting Mock AI Tags...")
        mock_tags = [
            ("R1_TEST", TEST_ASIN, "Quality", "softness", "Positive", "Amazing quality"),
            ("R2_TEST", TEST_ASIN, "Service", "packaging", "Negative", "Terrible packaging"),
        ]
        conn.executemany(
            """
            INSERT INTO review_tags (review_id, parent_asin, category, aspect, sentiment, quote)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            mock_tags,
        )

        # 5. RUN STATS ENGINE (The critical part)
        print("📊 Step 4: Running Stats Engine & Sync...")
        engine.calculate_and_save(TEST_ASIN, conn=conn)

        # 6. VERIFICATION
        print("\n🔍 --- FINAL VERIFICATION ---")

        # Check Stats Table
        stats_res = conn.execute("SELECT metrics_json FROM product_stats WHERE asin = ?", [TEST_ASIN]).fetchone()
        if stats_res:
            print("✅ product_stats entry created.")
            stats_obj = json.loads(stats_res[0])
            print(f"   Calculated Rating: {stats_obj['kpis']['avg_rating']}")
        else:
            print("❌ product_stats entry MISSING!")

        # Check Sync back to products
        final_p = conn.execute(
            "SELECT real_average_rating, real_total_ratings FROM products WHERE asin = ?", [TEST_ASIN]
        ).fetchone()
        print(f"   Final Product Rating in DB: {final_p[0]}")
        print(f"   Final Product Reviews in DB: {final_p[1]}")

        if final_p[0] is not None and final_p[0] > 0:
            print("🏆 SUCCESS: Pipeline synced calculated stats back to products table!")
        else:
            print("❌ FAILURE: products table still shows NaN/0 ratings.")

    finally:
        # 7. CLEANUP
        print("\n🧹 Step 5: Cleaning up test data...")
        active_db = Settings.get_active_db_path()
        conn = duckdb.connect(str(active_db))
        conn.execute("DELETE FROM review_tags WHERE parent_asin = ?", [TEST_ASIN])
        conn.execute("DELETE FROM reviews WHERE parent_asin = ?", [TEST_ASIN])
        conn.execute("DELETE FROM product_stats WHERE asin = ?", [TEST_ASIN])
        conn.execute("DELETE FROM products WHERE asin = ? OR parent_asin = ?", [TEST_ASIN, TEST_ASIN])
        conn.execute("DELETE FROM product_parents WHERE parent_asin = ?", [TEST_ASIN])

        if TEST_JSONL.exists():
            TEST_JSONL.unlink()

        conn.close()
        print("✨ Cleanup complete.")


if __name__ == "__main__":
    run_test()
