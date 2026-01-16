import duckdb
import json
import os
import time
import sys
from typing import List
from google import genai
from google.genai import types

# --- Config ---
DB_PATH = "scout_app/database/scout.duckdb"
MODEL_NAME = "models/gemini-2.5-flash-lite-preview-09-2025"

class BatchProcessor:
    def __init__(self, api_key=None):
        self.db_path = DB_PATH
        self._conn = None
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            print("⚠️ Warning: No API Key found. Operations strictly requiring API will fail.")
            self.client = None

    @property
    def conn(self):
        """Lazy connection to avoid locking issues"""
        if self._conn is None:
            self._conn = duckdb.connect(self.db_path)
        return self._conn

    def get_unmined_reviews(self, limit=None) -> List[dict]:
        """Lay danh sach review chua duoc xu ly (PENDING) tu DB"""
        limit_clause = f"LIMIT {limit}" if limit else ""
        query = f"""
            SELECT review_id, text, parent_asin
            FROM reviews 
            WHERE (mining_status IS NULL OR mining_status = 'PENDING')
            AND text IS NOT NULL
            AND length(text) > 10
            {limit_clause}
        """
        df = self.conn.execute(query).df()
        return df.to_dict(orient='records')

    def _build_chunk_prompt(self, reviews_chunk: List[dict]) -> str:
        """Tao prompt gom nhieu reviews de tiet kiem token"""
        reviews_text = ""
        for r in reviews_chunk:
            clean_text = r['text'].replace('"', "'").replace('\n', ' ')
            reviews_text += f"ID: {r['review_id']}\nText: {clean_text}\n---\n"

        prompt = f"""
        Analyze Amazon reviews to extract product aspects.
        **Categories:** Quality, Design, Size, Material, Price, Service, Functionality.
        **Output Format:** A Single JSON List of objects. 
        Each object: {{"id": "review_id", "c": "Category", "a": "Aspect", "s": "Pos/Neg/Neu", "q": "Short Quote"}}.
        
        **Reviews to process:**
        {reviews_text}
        """
        return prompt

    def prepare_batch_file(self, output_prefix="batch_input", chunk_size=200, requests_per_file=20, limit=None):
        """
        1. Lay reviews PENDING
        2. Gom 200 reviews/request để tiết kiệm token prompt.
        3. Mỗi file tối đa 20 requests (4000 reviews).
        """
        reviews = self.get_unmined_reviews(limit)
        total = len(reviews)
        print(f"📦 Found {total} PENDING reviews.")
        
        if total == 0:
            print("Nothing to mine.")
            return False

        file_count = 1
        current_filename = f"{output_prefix}_part_{file_count}.jsonl"
        current_f = open(current_filename, 'w', encoding='utf-8')
        print(f"   Writing to {current_filename}...")

        queued_ids = []
        current_requests_in_file = 0
        total_input_tokens = 0
        
        try:
            for i in range(0, total, chunk_size):
                # Check split file
                if current_requests_in_file >= requests_per_file:
                    current_f.close()
                    file_count += 1
                    current_requests_in_file = 0
                    current_filename = f"{output_prefix}_part_{file_count}.jsonl"
                    current_f = open(current_filename, 'w', encoding='utf-8')
                    print(f"   Writing to {current_filename}...")

                chunk = reviews[i:i + chunk_size]
                prompt = self._build_chunk_prompt(chunk)
                
                # Request Object
                request_body = {
                    "request": {
                        "model": MODEL_NAME,
                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "responseMimeType": "application/json",
                            "temperature": 0.1,
                            "maxOutputTokens": 60000 
                        }
                    }
                }
                current_f.write(json.dumps(request_body) + "\n")
                
                queued_ids.extend([r['review_id'] for r in chunk])
                current_requests_in_file += 1
                total_input_tokens += len(prompt) // 4

        finally:
            if current_f: current_f.close()

        # Update DB Status
        if queued_ids:
            print(f"🔄 Updating status to 'QUEUED' for {len(queued_ids)} reviews...")
            chunk_update_size = 5000
            for k in range(0, len(queued_ids), chunk_update_size):
                batch_ids = queued_ids[k:k+chunk_update_size]
                id_list_str = "', '".join(batch_ids)
                self.conn.execute(f"UPDATE reviews SET mining_status = 'QUEUED' WHERE review_id IN ('{id_list_str}')")
        
        print(f"✅ Prepared {file_count} files.")
        print(f"   - Total Reviews Queued: {len(queued_ids)}")
        print(f"   - Est. Input Tokens: {total_input_tokens:,} (SAVED ~90% prompt cost!)")
        return True

    def reset_queued_status(self):
        """Reset QUEUED -> PENDING"""
        count = self.conn.execute("SELECT COUNT(*) FROM reviews WHERE mining_status = 'QUEUED'").fetchone()[0]
        if count > 0:
            self.conn.execute("UPDATE reviews SET mining_status = 'PENDING' WHERE mining_status = 'QUEUED'")
            print(f"✅ Reset {count} reviews back to PENDING.")
        else:
            print("No QUEUED reviews found.")

    def submit_job(self, jsonl_file):
        """Upload file & Submit Batch Job"""
        if not self.client: return
        print(f"🚀 Uploading {jsonl_file}...")
        batch_file = self.client.files.upload(
            file=jsonl_file,
            config=types.UploadFileConfig(
                display_name=os.path.basename(jsonl_file),
                mime_type='text/plain' 
            )
        )
        while batch_file.state == "PROCESSING":
            time.sleep(2)
            batch_file = self.client.files.get(name=batch_file.name)

        display_name = f"Batch_200_{os.path.basename(jsonl_file)}_{int(time.time())}"
        print(f"🚀 Creating Job '{display_name}'...")
        job = self.client.batches.create(
            model=MODEL_NAME,
            src=batch_file.name,
            config={'display_name': display_name}
        )
        print(f"✅ Submitted! ID: {job.name}")
        return job.name

    def list_jobs(self):
        """List jobs WITHOUT DB connection"""
        if not self.client: return
        print("📋 Recent Batch Jobs:")
        for job in self.client.batches.list():
            print(f"   - {job.name} | {job.state} | {job.create_time}")

    def download_and_ingest(self, job_name):
        """Download results & Ingest to DB"""
        if not self.client: return
        job = self.client.batches.get(name=job_name)
        if "SUCCEEDED" not in str(job.state):
            print(f"⚠️ Job not ready: {job.state}")
            return

        print("✅ Downloading results...")
        output_file_name = job.dest.file_name
        content = self.client.files.download(file=output_file_name)
        result_text = content.decode('utf-8')
        
        # Save raw result
        res_file = f"result_{job_name.split('/')[-1]}.jsonl"
        with open(res_file, 'w') as f: f.write(result_text)
        
        self._ingest_chunk_results(result_text)

    def _ingest_chunk_results(self, jsonl_content):
        """Parse result JSONL where each line contains MULTIPLE tags"""
        print("⚙️ Ingesting chunked results...")
        success_count = 0
        data_to_insert = []
        
        reviews_df = self.conn.execute("SELECT review_id, parent_asin FROM reviews").df()
        asin_map = dict(zip(reviews_df['review_id'], reviews_df['parent_asin']))
        
        lines = jsonl_content.strip().split('\n')
        for line in lines:
            try:
                resp = json.loads(line)
                if "response" not in resp: continue
                
                raw_text = resp['response']['candidates'][0]['content']['parts'][0]['text']
                # Clean markdown if present
                raw_text = raw_text.replace('```json', '').replace('```', '').strip()
                minified_tags = json.loads(raw_text)

                sentiment_map = {"Pos": "Positive", "Neg": "Negative", "Neu": "Neutral"}

                for tag in minified_tags:
                    review_id = tag.get("id")
                    category = tag.get("c")
                    aspect = tag.get("a")
                    sentiment = sentiment_map.get(tag.get("s"), "Neutral")
                    quote = tag.get("q")
                    parent_asin = asin_map.get(review_id)

                    if review_id and parent_asin and category and aspect:
                        data_to_insert.append((review_id, parent_asin, category, aspect, sentiment, quote))
                        success_count += 1
            except Exception as e:
                print(f"   Line Parse Error: {e}")

        if data_to_insert:
            self.conn.executemany("""
                INSERT INTO review_tags (review_id, parent_asin, category, aspect, sentiment, quote)
                VALUES (?, ?, ?, ?, ?, ?)
            """, data_to_insert)
            
            completed_ids = list(set([r[0] for r in data_to_insert]))
            print(f"🔄 Updating status to 'COMPLETED' for {len(completed_ids)} reviews...")
            for k in range(0, len(completed_ids), 5000):
                batch_ids = completed_ids[k:k+5000]
                id_list_str = "', '".join(batch_ids)
                self.conn.execute(f"UPDATE reviews SET mining_status = 'COMPLETED' WHERE review_id IN ('{id_list_str}')")
            print(f"✅ Successfully processed {success_count} tags.")

if __name__ == "__main__":
    processor = BatchProcessor()
    if len(sys.argv) < 2: sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "prepare":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
        processor.prepare_batch_file(limit=limit)
    elif cmd == "submit":
        file_path = sys.argv[2] if len(sys.argv) > 2 else "batch_input_part_1.jsonl"
        processor.submit_job(file_path)
    elif cmd == "list": processor.list_jobs()
    elif cmd == "get": processor.download_and_ingest(sys.argv[2])
    elif cmd == "reset": processor.reset_queued_status()
