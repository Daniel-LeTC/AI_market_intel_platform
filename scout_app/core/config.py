import os
from pathlib import Path
import sys

# --- 1. Path Resolution ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

# --- 2. Environment Loader ---
def load_env_manual(path: Path):
    if not path.exists(): return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = value.strip().strip("'").strip('"')
    except Exception as e:
        print(f"⚠️ Warning: Failed to read .env file: {e}")

load_env_manual(ENV_PATH)

# --- 3. Configuration Class ---
class Settings:
    BASE_DIR = BASE_DIR
    DB_DIR = BASE_DIR / "scout_app" / "database"
    
    # Blue-Green DB Paths
    DB_PATH_A = DB_DIR / "scout_a.duckdb"
    DB_PATH_B = DB_DIR / "scout_b.duckdb"
    CURRENT_DB_PTR = DB_DIR / "current_db.txt"
    
    # Legacy Path (for migration support)
    DB_PATH_LEGACY = DB_DIR / "scout.duckdb"

    INGEST_STAGING_DIR = BASE_DIR / "staging_data"
    ARCHIVE_DIR = BASE_DIR / "archived_data"

    APIFY_TOKEN = os.getenv("APIFY_TOKEN")
    GEMINI_MINER_KEY = os.getenv("GEMINI_MINER_KEY")
    GEMINI_JANITOR_KEY = os.getenv("GEMINI_JANITOR_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    APIFY_ACTOR_ID = "axesso_data/amazon-reviews-scraper"
    GEMINI_MODEL = "models/gemini-3-flash-preview"

    @classmethod
    def get_active_db_path(cls) -> Path:
        """Read pointer to find which DB is ACTIVE (Read-Only for UI)."""
        if not cls.CURRENT_DB_PTR.exists():
            return cls.DB_PATH_A # Default to A
        
        try:
            with open(cls.CURRENT_DB_PTR, "r") as f:
                val = f.read().strip()
                return cls.DB_PATH_B if val == "B" else cls.DB_PATH_A
        except:
            return cls.DB_PATH_A

    @classmethod
    def get_standby_db_path(cls) -> Path:
        """Find the STANDBY DB (Write Target)."""
        active = cls.get_active_db_path()
        return cls.DB_PATH_B if active == cls.DB_PATH_A else cls.DB_PATH_A

    @classmethod
    def swap_db(cls):
        """Switch Active <-> Standby."""
        new_active = "B" if cls.get_active_db_path() == cls.DB_PATH_A else "A"
        with open(cls.CURRENT_DB_PTR, "w") as f:
            f.write(new_active)
        print(f"🔄 [System] Swapped Active DB to: {new_active}")

    @classmethod
    def ensure_dirs(cls):
        cls.DB_DIR.mkdir(parents=True, exist_ok=True)
        cls.INGEST_STAGING_DIR.mkdir(parents=True, exist_ok=True)
        cls.ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Init legacy migration if A/B don't exist
        if not cls.DB_PATH_A.exists() and cls.DB_PATH_LEGACY.exists():
            import shutil
            print("⚙️ Migrating legacy DB to Blue-Green...")
            shutil.copy(cls.DB_PATH_LEGACY, cls.DB_PATH_A)
            shutil.copy(cls.DB_PATH_LEGACY, cls.DB_PATH_B)

Settings.ensure_dirs()