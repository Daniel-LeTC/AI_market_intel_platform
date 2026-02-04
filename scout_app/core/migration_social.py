import duckdb
from config import Settings

def migrate_social():
    """
    Initialize 'social_posts' and 'social_comments' tables on ISOLATED Social DBs.
    """
    # Use Isolated Social DBs
    databases = [Settings.DB_SOCIAL_A, Settings.DB_SOCIAL_B]
    
    sql_posts = """
        CREATE TABLE IF NOT EXISTS social_posts (
            platform VARCHAR,
            post_id VARCHAR,
            keyword VARCHAR,
            author VARCHAR,
            text VARCHAR,
            url VARCHAR,
            likes INTEGER,
            shares INTEGER,
            comments_count INTEGER,
            views INTEGER,
            created_at TIMESTAMP,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (platform, post_id)
        );
    """
    
    sql_comments = """
        CREATE TABLE IF NOT EXISTS social_comments (
            comment_id VARCHAR,
            post_url VARCHAR,
            platform VARCHAR,
            author VARCHAR,
            text VARCHAR,
            likes INTEGER,
            reply_count INTEGER,
            created_at TIMESTAMP,
            sentiment VARCHAR,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    
    print("📱 Social Scout Migration Started (Isolated DB)...")
    
    for db_path in databases:
        # Ensure parent dir exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
            
        try:
            print(f"   -> Migrating {db_path.name}...")
            with duckdb.connect(str(db_path)) as conn:
                conn.execute(sql_posts)
                conn.execute(sql_comments)
        except Exception as e:
            print(f"   ❌ Error migrating {db_path.name}: {e}")

    print("✅ Social Migration Completed.")

if __name__ == "__main__":
    migrate_social()
