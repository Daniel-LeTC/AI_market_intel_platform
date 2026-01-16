import datetime
from pathlib import Path
from typing import List, Optional
from apify_client import ApifyClient
from .config import Settings

class AmazonScraper:
    def __init__(self):
        # Zero Trust: Validate Config again just in case
        if not Settings.APIFY_TOKEN:
            raise ValueError("APIFY_TOKEN is missing in Settings")
        
        self.client = ApifyClient(Settings.APIFY_TOKEN)
        self.actor_id = Settings.APIFY_ACTOR_ID
        self.stars = ["one_star", "two_star", "three_star", "four_star", "five_star"]

    def run_deep_scrape(self, asins: List[str]) -> Optional[Path]:
        """
        Trigger Apify task for a list of ASINs using 5-star split strategy.
        Downloads the result to staging_data/.
        
        Returns:
            Path: Absolute path to the downloaded file.
            None: If failed or empty.
        """
        if not asins:
            print("⚠️ Scraper: No ASINs provided.")
            return None

        # 1. Build Payload (Deep Scrape Strategy)
        run_input_items = []
        for asin in asins:
            asin = asin.strip()
            if not asin: continue
            
            for star in self.stars:
                run_input_items.append({
                    "asin": asin,
                    "domainCode": "com",
                    "sortBy": "recent",
                    "filterByStar": star,
                    "maxPages": 10  # Max amazon allows usually
                })

        print(f"🚀 [Scraper] Dispatching {len(run_input_items)} tasks (Parallel 5-Star Split) for {len(asins)} ASINs...")

        try:
            # 2. Execute on Apify (Blocking call - waits for finish)
            # Memory Limit: Default actor memory is usually fine.
            run = self.client.actor(self.actor_id).call(run_input={"input": run_input_items})
            
            run_id = run.get("id")
            status = run.get("status")
            print(f"⏳ [Scraper] Run ID: {run_id} | Status: {status}")

            if status != "SUCCEEDED":
                print(f"❌ [Scraper] Run failed with status: {status}")
                return None

            # 3. Check Dataset
            dataset_id = run["defaultDatasetId"]
            dataset_info = self.client.dataset(dataset_id).get()
            item_count = dataset_info.get("itemCount", 0)

            if item_count == 0:
                print("⚠️ [Scraper] Apify returned 0 items. Nothing to download.")
                return None

            print(f"📥 [Scraper] Downloading {item_count} items...")

            # 4. Download Raw Bytes (XLSX format preferred for now based on legacy)
            # We download as ONE big file. The Ingester will handle splitting/deduplication.
            dataset_bytes = self.client.dataset(dataset_id).get_items_as_bytes(item_format="xlsx")

            # 5. Save to Staging
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"raw_scrape_{timestamp}_{run_id}.xlsx"
            file_path = Settings.INGEST_STAGING_DIR / filename

            with open(file_path, "wb") as f:
                f.write(dataset_bytes)

            print(f"✅ [Scraper] Saved raw data to: {file_path}")
            return file_path

        except Exception as e:
            print(f"💥 [Scraper] Critical Error: {e}")
            return None
