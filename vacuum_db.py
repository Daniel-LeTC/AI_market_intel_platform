
import duckdb
import os

db_paths = [
    "scout_app/database/scout_a.duckdb",
    "scout_app/database/scout_b.duckdb"
]

for db_path in db_paths:
    if os.path.exists(db_path):
        print(f"🧹 Vacuuming {db_path}...")
        try:
            con = duckdb.connect(db_path)
            con.execute("VACUUM;")
            con.close()
            print(f"✅ Vacuumed {db_path}")
        except Exception as e:
            print(f"❌ Failed to vacuum {db_path}: {e}")
    else:
        print(f"⚠️ {db_path} not found.")
