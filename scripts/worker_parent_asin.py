import asyncio
import re
import duckdb
import sys
import os
import argparse
import random
import time
from playwright.async_api import async_playwright
from pathlib import Path

# Add root to sys.path to find core
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scout_app.core.config import Settings
from scout_app.core.logger import log_event


async def find_parent_asin(asin: str):
    """
    Scrape Amazon DP page to find the parentAsin using Regex.
    """
    url = f"https://www.amazon.com/dp/{asin}"
    print(f"🕵️ Searching for parent of {asin} at {url}...")

    async with async_playwright() as p:
        # Launch browser (headless for stability)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="load", timeout=30000)
            content = await page.content()

            # Simple Regex to find parentAsin
            match = re.search(r'"parentAsin"\s*:\s*"(B[A-Z0-9]{9})"', content)
            if match:
                parent = match.group(1)
                print(f"✅ Found Parent ASIN: {parent}")
                return parent
            else:
                print(f"❌ Could not find parentAsin in page source for {asin}")
                # Fallback: maybe it's its own parent?
                return None
        except Exception as e:
            print(f"⚠️ Error scraping {asin}: {e}")
            return None
        finally:
            await browser.close()


async def main(asins: list, category: str = None):
    db_path = str(Settings.get_active_db_path())
    conn = duckdb.connect(db_path)

    try:
        for asin in asins:
            parent = await find_parent_asin(asin)
            if parent:
                # Update DB - Product Parents
                if category:
                    conn.execute(
                        """
                        INSERT INTO product_parents (parent_asin, category, last_updated)
                        VALUES (?, ?, now())
                        ON CONFLICT (parent_asin) DO UPDATE SET 
                            category = CASE 
                                WHEN product_parents.category IS NULL OR product_parents.category IN ('Unknown', 'comforter') 
                                THEN excluded.category 
                                ELSE product_parents.category 
                            END,
                            last_updated = now()
                    """,
                        [parent, category],
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO product_parents (parent_asin, last_updated)
                        VALUES (?, now())
                        ON CONFLICT (parent_asin) DO UPDATE SET last_updated = now()
                    """,
                        [parent],
                    )

                # NEW: Ensure Parent exists in products table as well (Placeholder)
                conn.execute(
                    """
                    INSERT INTO products (asin, parent_asin, category, verification_status, last_updated)
                    VALUES (?, ?, ?, 'PARENT_PLACEHOLDER', now())
                    ON CONFLICT (asin) DO NOTHING
                    """,
                    [parent, parent, category],
                )

                # Update Queue Status to COMPLETED
                conn.execute(
                    """
                    UPDATE scrape_queue 
                    SET status = 'COMPLETED', 
                        note = COALESCE(note, '') || ' [Found Parent: ' || ? || ']'
                    WHERE asin = ? AND status = 'IN_PROGRESS'
                """,
                    [parent, asin],
                )

                # Also log for user visibility
                log_event("ParentFinder", {"asin": asin, "parent": parent, "category": category, "status": "mapped"})
            else:
                log_event("ParentFinder", {"asin": asin, "status": "not_found"})

                # Update Queue Status to FAILED
                conn.execute(
                    """
                    UPDATE scrape_queue 
                    SET status = 'FAILED', 
                        note = COALESCE(note, '') || ' [Parent Not Found]'
                    WHERE asin = ? AND status = 'IN_PROGRESS'
                """,
                    [asin],
                )

            # Anti-Bot: HEAVY random sleep with jitter for safety
            base_sleep = random.uniform(15, 30) if len(asins) > 1 else 0
            if base_sleep > 0:
                print(f"😴 Taking a long nap for {base_sleep:.2f}s to avoid Amazon Bot detection...")
                await asyncio.sleep(base_sleep)
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find parent ASINs and optionally set category.")
    parser.add_argument("asins", nargs="+", help="One or more ASINs to process")
    parser.add_argument("--category", help="Category to assign to the found parent ASINs")

    args = parser.parse_args()

    if args.asins:
        asyncio.run(main(args.asins, args.category))
    else:
        parser.print_help()
