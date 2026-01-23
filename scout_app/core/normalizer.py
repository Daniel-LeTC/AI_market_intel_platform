import duckdb
import os
import json
import time
from typing import List, Dict, Optional
from pathlib import Path
from google import genai
from google.genai import types
from .config import Settings
from .ai_batch import AIBatchHandler

class TagNormalizer:
    # Precision Model for Normalization (Cheap & Smart)
    MODEL_NAME = "models/gemini-2.5-flash-lite-preview-09-2025"

    def __init__(self):
        self.api_key = Settings.GEMINI_JANITOR_KEY
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            print("⚠️ Warning: Janitor API Key not set.")

    def _get_conn(self, read_only=False):
        # Always use dynamic path for Blue-Green safety
        return duckdb.connect(str(Settings.get_active_db_path()), read_only=read_only)

    def get_unmapped_aspects(self) -> List[str]:
        """Fetch unique RAW aspects that are NOT yet standardized."""
        conn = self._get_conn(read_only=True)
        query = """
            SELECT DISTINCT lower(trim(rt.aspect))
            FROM review_tags rt
            LEFT JOIN aspect_mapping am ON lower(trim(rt.aspect)) = lower(trim(am.raw_aspect))
            WHERE am.raw_aspect IS NULL
            AND length(rt.aspect) BETWEEN 2 AND 40
            AND rt.aspect NOT SIMILAR TO '^[0-9]+$' -- Ignore purely numeric noise
        """
        res = conn.execute(query).fetchall()
        conn.close()
        return [row[0] for row in res]

    def get_existing_standards(self) -> List[str]:
        """Fetch existing standard terms to maintain consistency (RAG Shield)."""
        try:
            conn = self._get_conn(read_only=True)
            res = conn.execute("SELECT DISTINCT standard_aspect FROM aspect_mapping WHERE standard_aspect IS NOT NULL ORDER BY 1").fetchall()
            vocab = [r[0] for r in res if r[0]]
            conn.close()
            return vocab
        except:
            return []

    def _build_prompt(self, raw_aspects: List[str], existing_standards: List[str]) -> str:
        vocab_str = ", ".join(f'"{s}"' for s in existing_standards)
        
        return f"""
        You are a Data Normalizer for E-commerce Reviews. 
        Map these RAW terms to standard NOUN PHRASES.
        
        **CRITICAL CONSISTENCY RULE:**
        You MUST prioritize mapping to these EXISTING STANDARD TERMS if they fit:
        [{vocab_str}]
        
        If no existing term fits, create a new succinct Noun Phrase (e.g., 'Softness', 'Zipper Quality').

        **Goal:** Group synonyms. Remove adjectives.
        - 'very soft', 'so soft', 'soft' -> 'Softness' (or existing equivalent)
        - 'great value', 'worth the price' -> 'Value for Money'
        
        **Allowed Categories:** 
        Quality, Design, Size, Material, Price, Service, Functionality, Comfort, Performance.

        **Input:** {raw_aspects}

        **Output:** JSON List of objects: {{"raw": "original_term", "std": "Standard Noun", "cat": "Category"}}
        """

    def run_live(self, batch_size=50):
        """Standardize aspects in real-time. Fast & Precise."""
        if not self.client: return
        
        unmapped = self.get_unmapped_aspects()
        if not unmapped:
            print("✨ [Janitor] Market data is already standardized.")
            return

        print(f"🧹 [Janitor-Live] Scrubbing {len(unmapped)} aspects...")
        
        shield = self.get_existing_standards()
        print(f"🛡️ RAG Shield active with {len(shield)} standard terms.")

        for i in range(0, len(unmapped), batch_size):
            batch = unmapped[i:i+batch_size]
            prompt = self._build_prompt(batch, shield)
            
            try:
                response = self.client.models.generate_content(
                    model=self.MODEL_NAME,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                mappings = json.loads(response.text)
                self.save_mappings(mappings)
                print(f"   ✅ Scrubbed batch {i//batch_size + 1}")
                time.sleep(1) # Rate limit safety
            except Exception as e:
                print(f"💥 [Janitor-Live] Error: {e}")

    def run_batch_prepare(self, limit=5000) -> Optional[Path]:
        """Prepare JSONL for large-scale Batch Normalization (Cheap mode)."""
        unmapped = self.get_unmapped_aspects()
        if not unmapped: return None
        
        if len(unmapped) > limit: unmapped = unmapped[:limit]
            
        print(f"📦 [Janitor-Batch] Preparing {len(unmapped)} aspects for batch...")

        timestamp = int(time.time())
        file_path = Settings.INGEST_STAGING_DIR / f"janitor_batch_{timestamp}.jsonl"
        
        shield = self.get_existing_standards()
        batch_size = 100 
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for i in range(0, len(unmapped), batch_size):
                batch = unmapped[i:i+batch_size]
                prompt = self._build_prompt(batch, shield)
                
                request_body = {
                    "request": {
                        "model": self.MODEL_NAME,
                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "responseMimeType": "application/json",
                            "temperature": 0.1
                        }
                    }
                }
                f.write(json.dumps(request_body) + "\n")
        
        return file_path

    def save_mappings(self, mappings: List[Dict]):
        """Save results to aspect_mapping table. Updates existing ones if needed."""
        if not mappings: return
        
        data_to_insert = []
        for m in mappings:
            raw, std, cat = m.get('raw'), m.get('std'), m.get('cat')
            if raw and std and cat:
                data_to_insert.append((raw.lower().strip(), std, cat))
        
        if data_to_insert:
            conn = self._get_conn()
            conn.executemany("""
                INSERT OR REPLACE INTO aspect_mapping (raw_aspect, standard_aspect, category)
                VALUES (?, ?, ?)
            """, data_to_insert)
            conn.close()

    def ingest_batch_results(self, jsonl_content: str):
        """Universal parser for Janitor batch results."""
        print("⚙️ [Janitor-Batch] Ingesting results...")
        all_mappings = []
        
        for line in jsonl_content.strip().split('\n'):
            try:
                resp = json.loads(line)
                if "response" not in resp: continue
                
                raw_text = resp['response']['candidates'][0]['content']['parts'][0]['text']
                raw_text = raw_text.replace('```json', '').replace('```', '').strip()
                chunk_mappings = json.loads(raw_text)
                if isinstance(chunk_mappings, list):
                    all_mappings.extend(chunk_mappings)
            except: continue

        if all_mappings:
            self.save_mappings(all_mappings)
            print(f"✅ [Janitor-Batch] Successfully synchronized {len(all_mappings)} standard terms.")