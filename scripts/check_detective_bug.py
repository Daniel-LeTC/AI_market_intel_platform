import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from scout_app.core.detective import DetectiveAgent

def debug_bug():
    agent = DetectiveAgent()
    print("🐞 Debugging search_review_evidence...")
    
    # Test case failed previously
    res = agent.search_review_evidence(
        asin='B09R94H5FS', 
        keyword='hot, sweat, sweaty, warm, suffocating',
        aspect='Breathability'
    )
    print(f"Result: {res}")

if __name__ == "__main__":
    debug_bug()
