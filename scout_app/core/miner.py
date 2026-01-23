import duckdb
import os
import json
import time
from typing import List, Dict, Optional
from pathlib import Path
from google import genai
from google.genai import types
from .config import Settings

class AIMiner:
    # Production Backend Model (Jan 2026)
    MODEL_NAME = "models/gemini-2.5-flash-lite-preview-09-2025"

    def __init__(self):
        self.api_key = Settings.GEMINI_MINER_KEY
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            print("⚠️ Warning: Gemini API Key not set. AI operations will fail.")

    def _get_conn(self, read_only=False):
        # Use active DB path from Settings (Blue-Green aware)
        return duckdb.connect(str(Settings.get_active_db_path()), read_only=read_only)

    def get_unmined_reviews(self, limit=200, status='PENDING') -> List[Dict]:
        """Fetch reviews that need AI analysis. Auto-completes trash (too short)."""
        conn = self._get_conn()
        
        # 1. AUTO-COMPLETE TRASH (Length <= 10 or NULL)
        # This keeps the system clean without wasting money on AI
        trash_sql = f"""
            UPDATE reviews 
            SET mining_status = 'COMPLETED' 
            WHERE mining_status = '{status}' 
            AND (text IS NULL OR length(trim(text)) <= 10)
        """
        conn.execute(trash_sql)
        
        # 2. FETCH QUALIFIED
        query = f"""
            SELECT review_id, parent_asin, text, rating_score 
            FROM reviews 
            WHERE mining_status = '{status}'
            AND text IS NOT NULL
            AND length(trim(text)) > 10
            LIMIT {limit}
        """
        df = conn.execute(query).df()
        conn.close()
        return df.to_dict(orient='records')

    def _build_prompt(self, reviews_chunk: List[Dict]) -> str:
        """Optimized prompt for RAW Aspect Extraction."""
        reviews_text = ""
        for r in reviews_chunk:
            t = r['text'].replace('"', "'").replace('\n', ' ')
            reviews_text += f"ID: {r['review_id']}\nText: {t}\n---\n"

        return f"""
        Analyze Amazon reviews to extract product aspects. 
        Focus on RAW aspects (e.g., 'softness', 'color accuracy', 'zipper quality').
        
        **Categories:** Quality, Design, Size, Material, Price, Service, Functionality, Performance.
        **Output Format:** A Single JSON List of objects. 
        Each object: {{"id": "review_id", "c": "Category", "a": "Raw Aspect", "s": "Pos/Neg/Neu", "q": "Short Quote"}}. 
        
        **Reviews to process:**
        {reviews_text}
        """

    def run_live(self, limit=100):
        """Live mining using 2.5 Flash Lite. Immediate results with locking."""
        if not self.client: return
        
        reviews = self.get_unmined_reviews(limit=limit, status='PENDING')
        if not reviews:
            print("✨ No pending reviews for Live Mining.")
            return

        review_ids = [r['review_id'] for r in reviews]
        
        # --- LAYER 1: LOCKING ---
        print(f"🔒 [Miner-Live] Locking {len(review_ids)} reviews as 'QUEUED'...")
        self._update_mining_status(review_ids, "QUEUED")

        print(f"🧠 [Miner-Live] Dispatching to AI ({self.MODEL_NAME})...")
        
        chunk_size = 50 
        for i in range(0, len(reviews), chunk_size):
            chunk = reviews[i:i+chunk_size]
            prompt = self._build_prompt(chunk)
            
            try:
                response = self.client.models.generate_content(
                    model=self.MODEL_NAME,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                tags = json.loads(response.text)
                
                # --- LAYER 2: SAVE & FALLBACK ---
                self._save_tags_to_db(tags, chunk)
                print(f"   ✅ Processed chunk ({len(chunk)} reviews)")
            except Exception as e:
                print(f"💥 [Miner-Live] API Error: {e}. Items remain 'QUEUED'.")

    def prepare_batch_file(self, limit=10000) -> Optional[Path]:
        """Prepare JSONL for Batch API."""
        reviews = self.get_unmined_reviews(limit=limit, status='PENDING')
        if not reviews:
            print("✨ No pending reviews for Batch.")
            return None

        print(f"📦 [Miner-Batch] Preparing {len(reviews)} reviews for Cheap Batch Inference...")
        
        timestamp = int(time.time())
        file_path = Settings.INGEST_STAGING_DIR / f"miner_batch_{timestamp}.jsonl"
        
        chunk_size = 200 
        review_ids_to_lock = []
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for i in range(0, len(reviews), chunk_size):
                chunk = reviews[i:i+chunk_size]
                prompt = self._build_prompt(chunk)
                
                request_body = {
                    "request": {
                        "model": self.MODEL_NAME,
                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "responseMimeType": "application/json",
                            "temperature": 0.1,
                            "maxOutputTokens": 60000 
                        }
                    }
                }
                f.write(json.dumps(request_body) + "\n")
                review_ids_to_lock.extend([r['review_id'] for r in chunk])

        # LOCK as QUEUED
        self._update_mining_status(review_ids_to_lock, "QUEUED")
        print(f"✅ Prepared {file_path.name}. Reviews locked as 'QUEUED'.")
        return file_path

    def _save_tags_to_db(self, minified_tags: List[Dict], original_chunk: List[Dict]):
        """Deduplicate and save extracted tags. Includes FALLBACK logic."""
        original_ids = [r['review_id'] for r in original_chunk]
        asin_map = {r['review_id']: r['parent_asin'] for r in original_chunk}
        rating_map = {r['review_id']: r['rating_score'] for r in original_chunk}
        text_map = {r['review_id']: r['text'] for r in original_chunk}
        
        sentiment_map = {"Pos": "Positive", "Neg": "Negative", "Neu": "Neutral"}
        
        data_to_insert = []
        processed_with_tags = set()
        
        # 1. Process AI Tags
        if minified_tags:
            for tag in minified_tags:
                rid = tag.get("id")
                pasin = asin_map.get(rid)
                if rid and pasin:
                    data_to_insert.append((
                        rid, pasin, tag.get("c"), tag.get("a"), 
                        sentiment_map.get(tag.get("s"), "Neutral"), tag.get("q")
                    ))
                    processed_with_tags.add(rid)

        # 2. FALLBACK LOGIC: If a review has no tags but was in the chunk, create a general tag
        for rid in original_ids:
            if rid not in processed_with_tags:
                pasin = asin_map.get(rid)
                score = rating_map.get(rid) or 3
                # Determine sentiment from stars
                if score >= 4: sent = "Positive"
                elif score <= 2: sent = "Negative"
                else: sent = "Neutral"
                
                data_to_insert.append((
                    rid, pasin, "Satisfaction", "general feedback", 
                    sent, text_map.get(rid, "N/A")[:100]
                ))

        if data_to_insert:
            conn = self._get_conn()
            # DEDUPLICATION
            id_list = "', '".join(original_ids)
            conn.execute(f"DELETE FROM review_tags WHERE review_id IN ('{id_list}')")
            
            conn.executemany("""
                INSERT INTO review_tags (review_id, parent_asin, category, aspect, sentiment, quote)
                VALUES (?, ?, ?, ?, ?, ?)
            """, data_to_insert)
            
            # --- STATUS UPGRADE ---
            self._update_mining_status(original_ids, "COMPLETED")
            conn.close()

    def _update_mining_status(self, review_ids: List[str], status: str):
        if not review_ids: return
        conn = self._get_conn()
        id_list = "', '".join(review_ids)
        conn.execute(f"UPDATE reviews SET mining_status = '{status}' WHERE review_id IN ('{id_list}')")
        conn.close()

    def ingest_batch_results(self, jsonl_content: str):
        """Universal Batch Ingest with Fallback support."""
        print("⚙️ [Miner-Batch] Ingesting results...")
        
        conn = self._get_conn(read_only=True)
        reviews_df = conn.execute("SELECT review_id, parent_asin, text, rating_score FROM reviews").df()
        asin_map = dict(zip(reviews_df['review_id'], reviews_df['parent_asin']))
        rating_map = dict(zip(reviews_df['review_id'], reviews_df['rating_score']))
        text_map = dict(zip(reviews_df['review_id'], reviews_df['text']))
        conn.close()

        success_count = 0
        sentiment_map = {"Pos": "Positive", "Neg": "Negative", "Neu": "Neutral"}

        # For Batch, we process line by line (each line is a chunk response)
        for line in jsonl_content.strip().split('\n'):
            try:
                resp = json.loads(line)
                if "response" not in resp: continue
                
                raw_text = resp['response']['candidates'][0]['content']['parts'][0]['text']
                raw_text = raw_text.replace('```json', '').replace('```', '').strip()
                chunk_tags = json.loads(raw_text)

                # Batch fallback is tricky because we don't know the exact original chunk here. 
                # However, our Live Miner fix covers the most frequent cases. 
                # For Batch, we will trust AI tags or mark the IDs as COMPLETED.
                processed_ids = set()
                data_to_insert = []
                for tag in chunk_tags:
                    rid, pasin = tag.get("id"), asin_map.get(tag.get("id"))
                    if rid and pasin:
                        data_to_insert.append((
                            rid, pasin, tag.get("c"), tag.get("a"),
                            sentiment_map.get(tag.get("s"), "Neutral"), tag.get("q")
                        ))
                        processed_ids.add(rid)
                        success_count += 1
                
                if data_to_insert:
                    conn = self._get_conn()
                    id_list = "', '".join(processed_ids)
                    conn.execute(f"DELETE FROM review_tags WHERE review_id IN ('{id_list}')")
                    conn.executemany("INSERT INTO review_tags (review_id, parent_asin, category, aspect, sentiment, quote) VALUES (?, ?, ?, ?, ?, ?)", data_to_insert)
                    self._update_mining_status(list(processed_ids), "COMPLETED")
                    conn.close()
            except: continue