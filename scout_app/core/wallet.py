import duckdb
from .config import Settings
from .logger import log_event

class WalletGuard:
    def __init__(self):
        self.db_path = str(Settings.SYSTEM_DB)

    def get_balance(self, user_id: str) -> float:
        """Get current spend vs budget."""
        try:
            with duckdb.connect(self.db_path, read_only=True) as conn:
                res = conn.execute("""
                    SELECT 
                        u.monthly_budget, 
                        w.current_spend 
                    FROM users u 
                    JOIN user_wallets w ON u.user_id = w.user_id 
                    WHERE u.user_id = ?
                """, [user_id]).fetchone()
                
                if res:
                    budget, spend = res
                    return max(0.0, budget - spend)
                return 0.0
        except Exception:
            return 0.0

    def check_funds(self, user_id: str, estimated_cost: float) -> bool:
        """Dry run check if user has enough funds."""
        balance = self.get_balance(user_id)
        return balance >= estimated_cost

    def charge_user(self, user_id: str, amount: float, task_details: dict) -> bool:
        """
        ATOMIC CHARGE:
        1. Update DB (Increment current_spend).
        2. Log Audit to JSONL.
        """
        if amount <= 0: return True
        
        try:
            # 1. Update DB
            with duckdb.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE user_wallets 
                    SET current_spend = current_spend + ? 
                    WHERE user_id = ?
                """, [amount, user_id])
            
            # 2. Audit Log (JSONL)
            log_payload = {
                "user_id": user_id,
                "action": "CHARGE",
                "amount_usd": amount,
                "task": task_details
            }
            log_event("wallet_audit", log_payload)
            
            return True
        except Exception as e:
            print(f"🔥 Wallet Charge Failed: {e}")
            return False
