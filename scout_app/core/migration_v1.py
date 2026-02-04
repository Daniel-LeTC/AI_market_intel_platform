import duckdb

DB_PATH = "scout_app/database/scout.duckdb"
conn = duckdb.connect(DB_PATH)

try:
    print("🛠 Adding 'mining_status' column to 'reviews' table...")
    # Add column if not exists logic is tricky in SQL standard, rely on exception or check
    # Simple try-catch block as planned
    conn.execute("ALTER TABLE reviews ADD COLUMN mining_status VARCHAR DEFAULT 'PENDING'")
    
    # Optional: Update existing to PENDING explicitly if needed, but DEFAULT handles new ones.
    # Existing rows get NULL if added this way in some DBs, or Default. 
    # In DuckDB, adding column with DEFAULT populates existing rows? Let's verify or force update.
    conn.execute("UPDATE reviews SET mining_status = 'PENDING' WHERE mining_status IS NULL")
    
    print("✅ Migration Successful: Added 'mining_status' and set default to 'PENDING'.")
    
except Exception as e:
    if "already exists" in str(e) or "Duplicate column" in str(e):
        print("ℹ️ Column 'mining_status' already exists. Skipping.")
    else:
        print(f"❌ Migration Failed: {e}")
