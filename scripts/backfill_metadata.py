import os
from pathlib import Path
import sys

# Add root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scout_app.core.ingest import DataIngester

def backfill():
    ingester = DataIngester()
    root_dir = Path(__file__).resolve().parent.parent # Root of project
    
    # Tìm tất cả các folder upload_batch_
    # Note: Use list(root_dir.glob(...)) to actually execute generator
    batch_dirs = [d for d in root_dir.glob("upload_batch_*") if d.is_dir()]
    batch_dirs.sort() 

    print(f"🚀 Found {len(batch_dirs)} batch directories to process.")

    for bdir in batch_dirs:
        print(f"\n📂 Processing {bdir.name}...")
        # Tìm tất cả file .xlsx trong batch
        excel_files = list(bdir.glob("*.xlsx"))
        
        for f in excel_files:
            print(f"   📄 Ingesting {f.name}...")
            # Ingest logic handles deduping reviews and replacing product info
            result = ingester.ingest_file(f)
            if "error" in result:
                print(f"   ❌ Error: {result['error']}")
            else:
                print(f"   ✅ Success. Active DB is now: {result.get('db_switched_to')}")

if __name__ == "__main__":
    print("WARNING: This will re-ingest all files to update Product Metadata.")
    print("Review IDs are deduped, so no duplicates will be created.")
    backfill()
    print("\n✨ Backfill Metadata Complete.")

