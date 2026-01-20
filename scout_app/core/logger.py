import json
from datetime import datetime
from pathlib import Path
from .config import Settings

def log_event(event_type: str, data: dict):
    """
    Append atomic JSON line to local buffer.
    Rotation is daily to prevent single file bloat.
    """
    if not isinstance(data, dict):
        return

    log_path = Settings.LOGS_BUFFER_DIR / f"{event_type}_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except Exception:
        pass
