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
    def __init__(self):
        self.db_path = str(Settings.DB_PATH)
        self.api_key = Settings.GEMINI_JANITOR_KEY
        self.model = Settings.GEMINI_MODEL
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def _get_conn(self):
        return duckdb.connect(self.db_path)

    def get_unmapped_aspects(self) -> List[str]:
        """Fetch unique 'aspect' values that are NOT in aspect_mapping."""
        conn = self._get_conn()
        query = """
            SELECT DISTINCT lower(trim(rt.aspect))
            FROM review_tags rt
            LEFT JOIN aspect_mapping am ON lower(trim(rt.aspect)) = lower(trim(am.raw_aspect))
            WHERE am.raw_aspect IS NULL
            AND length(rt.aspect) < 50
        """
        res = conn.execute(query).fetchall()
        conn.close()
        return [row[0] for row in res]

    def get_existing_standards(self) -> List[str]:
        """Fetch existing standard aspects for RAG Shield."""
        conn = self._get_conn()
        try:
            res = conn.execute("SELECT DISTINCT standard_aspect FROM aspect_mapping WHERE standard_aspect IS NOT NULL ORDER BY 1").fetchall()
            vocab = [r[0] for r in res if r[0]]
            conn.close()
            return vocab
        except Exception:
            conn.close()
            return []

    def _build_prompt(self, raw_aspects: List[str], existing_standards: List[str]) -> str:
        vocab_str = ", ".join(f'"{s}"' for s in existing_standards)
        
        prompt = f"""
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

        **Input:** {raw_aspects}

        **Output:** JSON List of objects: {{"raw": "original_term", "std": "Standard Noun", "cat": "Category"}}
        """
        return prompt

    def run_live(self, batch_size=100):
        """Standardize unmapped aspects in real-time."""
        if not self.client: return
        
        unmapped = self.get_unmapped_aspects()
        if not unmapped:
            print("✨ [Janitor] Everything is already clean.")
            return

        print(f"🧹 [Janitor-Live] Scrubbing {len(unmapped)} aspects...")
        
        # Load shield once
        shield = self.get_existing_standards()
        print(f"🛡️ Shield active with {len(shield)} terms.")

        for i in range(0, len(unmapped), batch_size):
            batch = unmapped[i:i+batch_size]
            prompt = self._build_prompt(batch, shield)
            
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                mappings = json.loads(response.text)
                self.save_mappings(mappings)
                print(f"   ✅ Scrubbed batch {i//batch_size + 1}")
                time.sleep(1)
            except Exception as e:
                print(f"💥 [Janitor-Live] Error: {e}")

    def run_batch_prepare(self, limit=5000) -> Optional[Path]:
        """Prepare JSONL for Batch Normalization."""
        unmapped = self.get_unmapped_aspects()
        if not unmapped:
            print("✨ [Janitor] Nothing to batch.")
            return None
        
        if len(unmapped) > limit:
            unmapped = unmapped[:limit]
            
        print(f"📦 [Janitor-Batch] Preparing {len(unmapped)} aspects...")

        timestamp = int(time.time())
        file_path = Settings.INGEST_STAGING_DIR / f"janitor_batch_{timestamp}.jsonl"
        
        shield = self.get_existing_standards()
        batch_size = 200 
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for i in range(0, len(unmapped), batch_size):
                batch = unmapped[i:i+batch_size]
                prompt = self._build_prompt(batch, shield)
                
                request_body = {
                    "request": {
                        "model": self.model,
                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "generationConfig": {"responseMimeType": "application/json"}
                    }
                }
                f.write(json.dumps(request_body) + "\n")
        
        return file_path

    def save_mappings(self, mappings: List[Dict]):
        """Save to aspect_mapping table."""
        if not mappings: return
        
        data_to_insert = []
        for m in mappings:
            # AI returns 'raw', 'std', 'cat' based on new prompt
            raw = m.get('raw')
            std = m.get('std')
            cat = m.get('cat')
            if raw and std and cat:
                data_to_insert.append((raw, std, cat))
        
        if data_to_insert:
            conn = self._get_conn()
            conn.executemany(
                """
                INSERT OR REPLACE INTO aspect_mapping (raw_aspect, standard_aspect, category)
                VALUES (?, ?, ?)
            """, data_to_insert)
            conn.close()

    def ingest_batch_results(self, jsonl_content: str):
        """Parse results from Google Batch."""
        print("⚙️ [Janitor-Batch] Ingesting results...")
        all_mappings = []
        
        lines = jsonl_content.strip().split('\n')
        print(f"   🔍 Found {len(lines)} lines in response.")
        
        for i, line in enumerate(lines):
            try:
                resp = json.loads(line)
                if "response" not in resp:
                    print(f"   ⚠️ Line {i}: No 'response' key.")
                    continue
                
                # Check for error in response
                if "error" in resp:
                     print(f"   ⚠️ Line {i} Error: {resp['error']}")
                     continue

                candidates = resp['response'].get('candidates', [])
                if not candidates:
                    print(f"   ⚠️ Line {i}: No candidates.")
                    continue

                raw_text = candidates[0]['content']['parts'][0]['text']
                # Basic cleanup
                raw_text = raw_text.replace('```json', '').replace('```', '').strip()
                
                try:
                    chunk_mappings = json.loads(raw_text)
                    if isinstance(chunk_mappings, list):
                        all_mappings.extend(chunk_mappings)
                    else:
                        print(f"   ⚠️ Line {i}: JSON is not a list.")
                except json.JSONDecodeError as je:
                    print(f"   ⚠️ Line {i}: JSON Decode Error: {je} | Text snippet: {raw_text[:50]}...")

            except Exception as e:
                print(f"   ⚠️ Line {i} Parse Error: {e}")

        print(f"   📊 Parsed {len(all_mappings)} valid mappings.")
        if all_mappings:
            self.save_mappings(all_mappings)
            print(f"✅ [Janitor-Batch] Saved {len(all_mappings)} mappings.")