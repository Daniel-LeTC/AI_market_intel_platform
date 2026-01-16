import os
from pathlib import Path
import sys

# --- 1. Path Resolution ---
# scout_app/core/config.py -> scout_app/core/ -> scout_app/ -> ROOT
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

# --- 2. Environment Loader (Zero Dependency) ---
def load_env_manual(path: Path):
    """
    Load .env manually.
    Priority: System Env > .env File
    """
    if not path.exists():
        # Dev might rely purely on system env vars (Docker/Cloud)
        return
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("'").strip('"')
                    
                    # Only set if not already in system env
                    if key not in os.environ:
                        os.environ[key] = value
    except Exception as e:
        print(f"⚠️ Warning: Failed to read .env file: {e}")

# Load immediately on import
load_env_manual(ENV_PATH)

# --- 3. Configuration Class ---
class Settings:
    # Paths
    BASE_DIR = BASE_DIR
    DB_PATH = BASE_DIR / "scout_app" / "database" / "scout.duckdb"
    
    # Pipeline Directories
    # Staging: Nơi file JSONL/Excel từ Scraper được lưu tạm
    INGEST_STAGING_DIR = BASE_DIR / "staging_data"
    # Archive: Nơi lưu file gốc sau khi đã nạp DB thành công
    ARCHIVE_DIR = BASE_DIR / "archived_data"

    # Secrets (Fail Fast handled in validate)
    APIFY_TOKEN = os.getenv("APIFY_TOKEN")
    GEMINI_MINER_KEY = os.getenv("GEMINI_MINER_KEY")
    GEMINI_JANITOR_KEY = os.getenv("GEMINI_JANITOR_KEY")

    # Scraper Constants
    APIFY_ACTOR_ID = "axesso_data/amazon-reviews-scraper"
    
    # AI Constants - Upgraded to latest Gemini 3 (Jan 2026)
    GEMINI_MODEL = "models/gemini-3-flash-preview"

    @classmethod
    def validate(cls):
        """
        Zero Trust: Ensure critical secrets exist.
        Call this at the start of any entry point.
        """
        missing = []
        if not cls.APIFY_TOKEN:
            missing.append("APIFY_TOKEN")
        if not cls.GEMINI_MINER_KEY:
            missing.append("GEMINI_MINER_KEY")
        if not cls.GEMINI_JANITOR_KEY:
            missing.append("GEMINI_JANITOR_KEY")
        
        if missing:
            raise ValueError(f"❌ CRITICAL ERROR: Missing Environment Variables: {', '.join(missing)}")

    @classmethod
    def ensure_dirs(cls):
        """Create scaffolding directories if missing."""
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.INGEST_STAGING_DIR.mkdir(parents=True, exist_ok=True)
        cls.ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# --- 4. Auto-Initialization ---
# Ensure directories exist implies side-effect on import. 
# Safe for this project context.
Settings.ensure_dirs()
