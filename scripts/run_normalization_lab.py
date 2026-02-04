import duckdb
import os
import json
import time
from google import genai
from google.genai import types
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

def load_env(path: Path):
    if not path.exists():
        print(f"⚠️ .env not found at {path}")
        return
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ[k] = v.strip().strip("'").strip('"')
    except Exception as e: 
        print(f"⚠️ Error reading .env: {e}")

load_env(ENV_PATH)

DB_PATH = str(BASE_DIR / "scout_app/database/scout.duckdb")
API_KEY = os.getenv("GEMINI_JANITOR_KEY")
MODEL = "gemini-2.5-flash-lite-preview-09-2025"

def get_top_dirty_aspects(conn, limit=100):
    """Lấy những aspect phổ biến nhất mà chưa được map."""
    query = """
        SELECT lower(trim(t.aspect)) as raw_aspect, count(*) as c
        FROM review_tags t
        LEFT JOIN aspect_mapping m ON lower(trim(t.aspect)) = lower(trim(m.raw_aspect))
        WHERE m.raw_aspect IS NULL
        AND length(t.aspect) < 50
        GROUP BY 1
        ORDER BY c DESC
        LIMIT ?
    """
    return conn.execute(query, [limit]).fetchall()

def get_existing_standards(conn):
    """Lấy danh sách các term chuẩn đã có để làm mốc tham chiếu."""
    try:
        res = conn.execute("SELECT DISTINCT standard_aspect FROM aspect_mapping").fetchall()
        return [r[0] for r in res if r[0]]
    except:
        return []

def build_prompt(aspects, existing_standards):
    aspect_list = [a[0] for a in aspects]
    vocab_str = ", ".join(f'"{s}"' for s in existing_standards)
    
    return f"""
    You are a Data Normalizer. Map these raw e-commerce review terms to STANDARD NOUN PHRASES.
    
    **CRITICAL RULE (Consistency Shield):**
    You MUST prioritize mapping to these EXISTING STANDARD TERMS if applicable:
    [{vocab_str}]
    
    If no existing term fits, create a new succinct Noun Phrase.

    **Goal:** Group synonyms. Remove adjectives.
    - "very soft", "so soft" -> "Softness" (or existing term)
    - "worth it", "good value" -> "Value for Money" 
    
    **Allowed Categories:** 
    Quality, Design, Size, Material, Price, Service, Functionality, Comfort.

    **Input:** {aspect_list}

    **Output:** JSON List of objects: {{"raw": "original_term", "std": "Standard Noun", "cat": "Category"}}
    """

def run_lab():
    if not API_KEY:
        print("❌ Missing JANITOR_KEY")
        return

    conn = duckdb.connect(DB_PATH)
    client = genai.Client(api_key=API_KEY)
    
    # 1. Get Data
    batch = get_top_dirty_aspects(conn, limit=100) # Tang len 100 con
    if not batch:
        print("✨ No unmapped aspects found.")
        return

    # 2. Get Shield
    existing_standards = get_existing_standards(conn)
    print(f"🛡️ Shield loaded with {len(existing_standards)} existing terms.")

    print(f"🔬 [LAB] Scrubbing {len(batch)} aspects...")
    
    # 3. Call AI
    prompt = build_prompt(batch, existing_standards)
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        mappings = json.loads(response.text)
        
        # 4. Print Preview
        print(f"\n{'RAW':<30} | {'STANDARD':<20} | {'CATEGORY':<15}")
        print("-" * 70)
        
        data_to_save = []
        for m in mappings:
            print(f"{m.get('raw', ''):<30} | {m.get('std', ''):<20} | {m.get('cat', ''):<15}")
            if m.get('raw') and m.get('std'):
                data_to_save.append((m['raw'], m['std'], m['cat']))
        
        # 5. Auto Save (User approved)
        if data_to_save:
            conn.executemany("INSERT OR REPLACE INTO aspect_mapping (raw_aspect, standard_aspect, category) VALUES (?, ?, ?)", data_to_save)
            print(f"✅ Auto-Saved {len(data_to_save)} mappings.")

    except Exception as e:
        print(f"💥 Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    run_lab()