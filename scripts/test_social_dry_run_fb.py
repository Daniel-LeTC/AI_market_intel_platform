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
            # Print sample values for verification
            print("SAMPLE VALUES:")
            for k in ['url', 'postUrl', 'text', 'caption', 'likes', 'likesCount', 'comments', 'commentsCount']:
                if k in first_item:
                    print(f"  - {k}: {first_item[k]}")

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

# --- EXECUTE TESTS ---

# 1. Facebook Hashtag (Check keywordList param)
run_test(
    "Facebook Hashtag", 
    "apify/facebook-hashtag-scraper", 
    {
        "keywordList": ["bedding"], 
        "resultsLimit": 1
    }
)

# 2. Facebook Comments (Check startUrls param)
# Need a valid public post URL. Assuming a random one or generic structure check.
# Using a generic public page post for test (CNN/BBC etc)
run_test(
    "Facebook Comments", 
    "apify/facebook-comments-scraper", 
    {
        "startUrls": [{"url": "https://www.facebook.com/Apify/posts/pfbid02R7..."}], # Example URL, might fail if invalid
        "resultsLimit": 1,
        "includeNestedComments": False
    }
)
