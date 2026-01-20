import os
import json
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load Env
load_dotenv()
API_TOKEN = os.getenv("APIFY_TOKEN")

if not API_TOKEN:
    print("❌ Error: APIFY_TOKEN not found in env.")
    exit(1)

client = ApifyClient(API_TOKEN)

def run_test(name, actor_id, input_data):
    print(f"\n--- 🧪 TESTING: {name} ({actor_id}) ---")
    print(f"INPUT: {json.dumps(input_data, indent=2)}")
    
    try:
        # Start Actor
        run = client.actor(actor_id).call(run_input=input_data)
        
        # Check Status
        if run.get('status') != 'SUCCEEDED':
            print(f"❌ FAILED Status: {run.get('status')}")
            return

        # Get Dataset
        dataset_id = run["defaultDatasetId"]
        items = client.dataset(dataset_id).list_items(limit=1).items
        
        if not items:
            print("⚠️ WARNING: Actor finished but returned NO DATA.")
        else:
            print("✅ SUCCESS! Got Data.")
            first_item = items[0]
            print("RAW KEYS FOUND:", list(first_item.keys()))
            print("SAMPLE SAMPLE (First 3 fields):")
            # Print first 3 fields/values for sanity check
            for k in list(first_item.keys())[:5]:
                val = str(first_item[k])[:50] # Truncate
                print(f"  - {k}: {val}...")

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

# --- EXECUTE TESTS ---

# 1. TikTok (ApiDojo)
run_test(
    "TikTok Feed", 
    "apidojo/tiktok-scraper", 
    {
        "keywords": ["bedding"], 
        "maxItems": 1,
        "proxyConfiguration": {"useApifyProxy": True}
    }
)

# 2. Facebook Hashtag
run_test(
    "Facebook Hashtag", 
    "apify/facebook-hashtag-scraper", 
    {
        "hashtags": ["bedding"], 
        "resultsLimit": 1
    }
)

# 3. Instagram Hashtag
run_test(
    "Instagram Hashtag", 
    "apify/instagram-hashtag-scraper", 
    {
        "hashtags": ["bedding"], 
        "resultsLimit": 1,
        "resultsType": "posts"
    }
)
