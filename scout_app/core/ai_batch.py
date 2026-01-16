import os
import time
import json
from pathlib import Path
from typing import Optional, List
from google import genai
from google.genai import types
from .config import Settings

class AIBatchHandler:
    def __init__(self, api_key: Optional[str] = None):
        # Default to Miner Key if none provided (common use case)
        self.api_key = api_key or Settings.GEMINI_MINER_KEY
        
        if not self.api_key:
            raise ValueError("API Key is missing for Batch Handler")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model = Settings.GEMINI_MODEL

    def submit_batch_job(self, jsonl_path: Path, display_name_suffix: str = "") -> str:
        """Uploads a file and starts a Batch Job."""
        print(f"🚀 [AI-Batch] Uploading {jsonl_path.name}...")
        
        # 1. Upload
        batch_file = self.client.files.upload(
            file=str(jsonl_path),
            config=types.UploadFileConfig(
                display_name=jsonl_path.name,
                mime_type='text/plain' 
            )
        )
        
        # 2. Wait for processing (Google requirement)
        while batch_file.state == "PROCESSING":
            time.sleep(2)
            batch_file = self.client.files.get(name=batch_file.name)

        if batch_file.state == "FAILED":
             raise Exception(f"File upload failed: {batch_file.name}")

        # 3. Create Job
        display_name = f"Scout_{display_name_suffix}_{int(time.time())}"
        print(f"🚀 [AI-Batch] Creating Job: {display_name}...")
        
        job = self.client.batches.create(
            model=self.model,
            src=batch_file.name,
            config={'display_name': display_name}
        )
        
        return job.name

    def list_active_jobs(self):
        """List current batch jobs."""
        print("📋 [AI-Batch] Recent Jobs:")
        for job in self.client.batches.list():
            print(f"   - {job.name} | {job.state} | {job.create_time}")

    def get_job_results(self, job_name: str) -> Optional[str]:
        """
        Downloads results if job is SUCCEEDED.
        Returns the raw text of the result JSONL.
        """
        job = self.client.batches.get(name=job_name)
        
        if "SUCCEEDED" not in str(job.state):
            print(f"⚠️ [AI-Batch] Job {job_name} is not ready (State: {job.state})")
            return None

        print(f"✅ [AI-Batch] Downloading results for {job_name}...")
        output_file_name = job.dest.file_name
        content = self.client.files.download(file=output_file_name)
        
        return content.decode('utf-8')

    def check_job_status(self, job_name: str) -> str:
        """Returns the status string."""
        job = self.client.batches.get(name=job_name)
        return str(job.state)
