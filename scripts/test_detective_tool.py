import sys
import os
import json
from pathlib import Path

# Add root to path
sys.path.append(os.getcwd())

from scout_app.core.detective import DetectiveAgent

def test_tool():
    agent = DetectiveAgent()
    
    # Test ASIN: CozyLux (from logs)
    test_asin = "B09R94H5FS" 
    
    print(f"🕵️ Testing analyze_competitors for ASIN: {test_asin}")
    result = agent.analyze_competitors(test_asin)
    
    try:
        # Pretty print JSON
        parsed = json.loads(result)
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    except:
        print("Raw Output:", result)

if __name__ == "__main__":
    test_tool()
