import sys
from pathlib import Path
import glob

# Add root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scout_app.core.ingest import DataIngester

def ingest_old_batches():
    ingester = DataIngester()
    
    # Pattern cho batch 16 den 22
    for i in range(16, 23):
        pattern = f"upload_batch_{i}/*.xlsx"
        files = glob.glob(pattern)
        
        if not files:
            print(f"⚠️ No files found in upload_batch_{i}")
            continue
            
        print(f"📦 Processing Batch {i} ({len(files)} files)...")
        for f in files:
            res = ingester.ingest_file(Path(f))
            if "error" in res:
                print(f"   ❌ Error: {res['error']}")

if __name__ == "__main__":
    ingest_old_batches()
