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

class AIMiner:
    def __init__(self):
        self.db_path = str(Settings.DB_PATH)
        self.api_key = Settings.GEMINI_MINER_KEY
        self.model = Settings.GEMINI_MODEL
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            print("⚠️ Warning: Gemini API Key not set. AI operations will fail.")

    def _get_conn(self):
        return duckdb.connect(self.db_path)

    def get_unmined_reviews(self, limit=200, status='PENDING') -> List[Dict]:
        """Lay reviews chua phân tích."""
        conn = self._get_conn()
        query = f"""
            SELECT review_id, parent_asin, text 
            FROM reviews 
            WHERE mining_status = '{status}'
            AND text IS NOT NULL
            AND length(text) > 10
            LIMIT {limit}
        """
        df = conn.execute(query).df()
        conn.close()
        return df.to_dict(orient='records')

    def _build_prompt(self, reviews_chunk: List[Dict]) -> str:
        """Gom reviews thành prompt tối ưu token."""
        reviews_text = ""
        for r in reviews_chunk:
            # Clean text to avoid breaking JSON structure in prompt
            t = r['text'].replace('"', "'").replace('\n', ' ')
            reviews_text += f"ID: {r['review_id']}\nText: {t}\n---\n"

        prompt = f"""
        Analyze Amazon reviews to extract product aspects.
        **Categories:** Quality, Design, Size, Material, Price, Service, Functionality, Performance.
        **Output Format:** A Single JSON List of objects. 
        Each object: {{"id": "review_id", "c": "Category", "a": "Aspect", "s": "Pos/Neg/Neu", "q": "Short Quote"}}. 
        
        **Reviews to process:**
        {reviews_text}
        """
        return prompt

    def run_live(self, limit=50):
        """Phân tích ngay lập tức (Real-time)."""
        if not self.client: return
        
        reviews = self.get_unmined_reviews(limit=limit)
        if not reviews:
            print("✨ No reviews to mine (Live).")
            return

        print(f"🧠 [Miner-Live] Processing {len(reviews)} reviews...")
        
        # We can process in smaller chunks even for live to avoid token limits
        chunk_size = 20
        for i in range(0, len(reviews), chunk_size):
            chunk = reviews[i:i+chunk_size]
            prompt = self._build_prompt(chunk)
            
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                tags = json.loads(response.text)
                self._save_tags_to_db(tags, chunk)
                print(f"   ✅ Processed chunk of {len(chunk)}")
            except Exception as e:
                print(f"💥 [Miner-Live] Error: {e}")

    def run_batch_prepare(self, limit=4000) -> Optional[Path]:
        """Chuẩn bị file JSONL cho Batch Job (200 reviews/request)."""
        reviews = self.get_unmined_reviews(limit=limit)
        if not reviews:
            print("✨ No reviews for Batch.")
            return None

        print(f"📦 [Miner-Batch] Preparing {len(reviews)} reviews for Batch Job...")
        
        timestamp = int(time.time())
        file_path = Settings.INGEST_STAGING_DIR / f"miner_batch_{timestamp}.jsonl"
        
        chunk_size = 200
        review_ids_queued = []
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for i in range(0, len(reviews), chunk_size):
                chunk = reviews[i:i+chunk_size]
                prompt = self._build_prompt(chunk)
                
                request_body = {
                    "request": {
                        "model": self.model,
                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "responseMimeType": "application/json",
                            "temperature": 0.1,
                            "maxOutputTokens": 60000 
                        }
                    }
                }
                f.write(json.dumps(request_body) + "\n")
                review_ids_queued.extend([r['review_id'] for r in chunk])

        # Mark as QUEUED in DB
        self._update_mining_status(review_ids_queued, "QUEUED")
        return file_path

    def _save_tags_to_db(self, minified_tags: List[Dict], original_chunk: List[Dict]):
        """Lưu tags và đánh dấu COMPLETED."""
        if not minified_tags: return
        
        asin_map = {r['review_id']: r['parent_asin'] for r in original_chunk}
        sentiment_map = {"Pos": "Positive", "Neg": "Negative", "Neu": "Neutral"}
        
        data_to_insert = []
        for tag in minified_tags:
            rid = tag.get("id")
            pasin = asin_map.get(rid)
            if rid and pasin:
                data_to_insert.append((
                    rid, pasin, tag.get("c"), tag.get("a"), 
                    sentiment_map.get(tag.get("s"), "Neutral"), tag.get("q")
                ))

        if data_to_insert:
            conn = self._get_conn()
            conn.executemany("""
                INSERT INTO review_tags (review_id, parent_asin, category, aspect, sentiment, quote)
                VALUES (?, ?, ?, ?, ?, ?)
            """, data_to_insert)
            
            # Update status
            rids = list(set([r[0] for r in data_to_insert]))
            self._update_mining_status(rids, "COMPLETED")
            conn.close()

    def _update_mining_status(self, review_ids: List[str], status: str):
        if not review_ids: return
        conn = self._get_conn()
        # DuckDB handles large IN clauses but let's be safe with batches if needed
        # For simple tool, standard IN is fine for thousands
        id_list = "', '".join(review_ids)
        conn.execute(f"UPDATE reviews SET mining_status = '{status}' WHERE review_id IN ('{id_list}')")
        conn.close()

    def ingest_batch_results(self, jsonl_content: str):
        """Xử lý kết quả từ Batch Job (JSONL rác rưởi của Google)."""
        print("⚙️ [Miner-Batch] Ingesting results...")
        
        # We need a global mapping for ASINs since results don't have them
        conn = self._get_conn()
        reviews_df = conn.execute("SELECT review_id, parent_asin FROM reviews").df()
        asin_map = dict(zip(reviews_df['review_id'], reviews_df['parent_asin']))
        conn.close()

        success_count = 0
        all_tags = []
        all_processed_ids = []

        lines = jsonl_content.strip().split('\n')
        sentiment_map = {"Pos": "Positive", "Neg": "Negative", "Neu": "Neutral"}

        for line in lines:
            try:
                resp = json.loads(line)
                if "response" not in resp: continue
                
                raw_text = resp['response']['candidates'][0]['content']['parts'][0]['text']
                raw_text = raw_text.replace('```json', '').replace('```', '').strip()
                chunk_tags = json.loads(raw_text)

                for tag in chunk_tags:
                    rid = tag.get("id")
                    pasin = asin_map.get(rid)
                    if rid and pasin:
                        all_tags.append((
                            rid, pasin, tag.get("c"), tag.get("a"),
                            sentiment_map.get(tag.get("s"), "Neutral"), tag.get("q")
                        ))
                        all_processed_ids.append(rid)
                        success_count += 1
            except Exception as e:
                print(f"   ⚠️ Line Parse Error: {e}")

        if all_tags:
            conn = self._get_conn()
            conn.executemany("""
                INSERT INTO review_tags (review_id, parent_asin, category, aspect, sentiment, quote)
                VALUES (?, ?, ?, ?, ?, ?)
            """, all_tags)
            
            # Mark COMPLETED
            unique_ids = list(set(all_processed_ids))
            self._update_mining_status(unique_ids, "COMPLETED")
            conn.close()
            print(f"✅ [Miner-Batch] Successfully processed {success_count} tags.")