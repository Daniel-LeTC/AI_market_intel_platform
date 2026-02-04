import duckdb
import bcrypt
from .config import Settings

class AuthManager:
    def __init__(self):
        self.db_path = str(Settings.SYSTEM_DB)

    def verify_user(self, username, password):
        """
        Verifies user credentials.
        Returns: User Dict {user_id, role, budget} if valid, else None.
        """
        try:
            with duckdb.connect(self.db_path, read_only=True) as conn:
                # Fetch user by username
                query = "SELECT user_id, password_hash, role, monthly_budget FROM users WHERE username = ?"
                result = conn.execute(query, [username]).fetchone()

                if not result:
                    return None
                
                user_id, stored_hash, role, budget = result
                
                # Verify password using bcrypt
                # stored_hash is string, bcrypt needs bytes
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                    return {
                        "user_id": user_id,
                        "username": username,
                        "role": role,
                        "budget": budget
                    }
                else:
                    return None
                    
        except Exception as e:
            print(f"Auth Error: {e}")
            return None
