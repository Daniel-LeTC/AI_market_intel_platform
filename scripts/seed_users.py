import duckdb
import bcrypt
from pathlib import Path

# Config
DB_PATH = Path("scout_app/database/system.duckdb")
DEFAULT_PASS = "123456"

# Data: (user_id, username, role, budget)
users_data = [
    ('u_test', 'test', 'USER', 20.0),
    ('u_admin', 'admin', 'ADMIN', 100.0),
    ('u_1000', 'user_1000', 'USER', 20.0)
]

def hash_password(plain_text):
    """Hash password with random salt using bcrypt."""
    # gensalt() generates a random salt. 
    # hashpw returns bytes, so we decode to utf-8 for storage.
    return bcrypt.hashpw(plain_text.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed():
    print(f"🔐 Seeding users into {DB_PATH}...")
    
    # Ensure DB Directory exists
    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(str(DB_PATH))
    
    # Hash the default password once to save time (or hash per user if unique)
    # Here we use same pass for all, but let's hash individually to have unique salts
    
    count = 0
    for uid, uname, role, budget in users_data:
        try:
            hashed = hash_password(DEFAULT_PASS)
            
            # Upsert User (Insert or Ignore if exists)
            # DuckDB doesn't strictly have INSERT OR IGNORE in all versions, 
            # so we check existence first or use TRY/CATCH logic if constraints are set.
            # Simple way: Check if exists
            
            exists = conn.execute("SELECT 1 FROM users WHERE user_id = ?", [uid]).fetchone()
            
            if not exists:
                conn.execute("""
                    INSERT INTO users (user_id, username, password_hash, role, monthly_budget)
                    VALUES (?, ?, ?, ?, ?)
                """, [uid, uname, hashed, role, budget])
                
                # Init Wallet
                conn.execute("""
                    INSERT INTO user_wallets (user_id, current_spend)
                    VALUES (?, 0.0)
                """, [uid])
                
                print(f"✅ Added: {uname} (Pass: {DEFAULT_PASS})")
                count += 1
            else:
                print(f"ℹ️ Skipped: {uname} (Already exists)")
                
        except Exception as e:
            print(f"❌ Error adding {uname}: {e}")
            
    conn.close()
    print(f"🏁 Done. Added {count} users.")

if __name__ == "__main__":
    seed()
