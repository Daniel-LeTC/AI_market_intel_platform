import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from scout_app.core.detective import DetectiveAgent

def run_stress_test():
    print("🕵️ STARTING DETECTIVE AGENT STRESS TEST (V4.4) - EXTENDED")
    print("=========================================================")
    
    agent = DetectiveAgent()
    
    # Context: B09R94H5FS (Comforter Set)
    default_asin = "B09R94H5FS" 

    test_cases = [
        # --- PHASE 1: DNA & VARIATIONS (Basic Tool Check) ---
        "Con B09R94H5FS này có bao nhiêu biến thể tất cả? Kể tên vài màu nổi bật xem.",
        
        # --- PHASE 2: FACT CHECKING (Trap: Silk vs Polyester) ---
        "Sản phẩm này có phải làm bằng lụa tơ tằm (Silk) 100% không? Check kỹ thông số và review xem người ta nói gì.",
        
        # --- PHASE 3: CONFLICT CHECK (Description vs Reality) ---
        "Hãng thì bảo là thoáng khí (breathable), nhưng thực tế người dùng có thấy nóng (hot/sweat) khi ngủ không?",
        
        # --- PHASE 4: MIXED LANGUAGE & KEYWORDS ---
        "Check giùm tao cái durability của con này, xem có bị rách (torn) hay phai màu (fade) after washing không?",
        
        # --- PHASE 5: QUANTIFICATION TRAP (AI often fails to count exact numbers) ---
        "Ước lượng xem có nhiều người chê nó bị vón cục (lumpy) sau khi giặt không? Tìm khoảng 5 bằng chứng cụ thể.",
        
        # --- PHASE 6: MARKET SCOUTING ---
        "Thấy con này bị chê nhiều quá. Tìm cho tao 3 con khác cùng loại (Niche) mà xịn hơn, ít bị chê hơn xem.",
        
        # --- PHASE 7: MULTI-ASIN COMPARISON & MEMORY ---
        # Giả sử Phase 6 trả về B09MS2SHNP.
        "So sánh con B09R94H5FS với con B09MS2SHNP. Con nào được khen về độ mềm (Softness) nhiều hơn?",
        
        # --- PHASE 8: NEGATIVE LOGIC (Hard for Search) ---
        "Tìm những review nào khen về bao bì (packaging) của sản phẩm này. Tao muốn biết nó đóng gói có đẹp để làm quà tặng không.",
        
        # --- PHASE 9: SEMANTIC AMBIGUITY (Smell) ---
        "Sản phẩm này mở ra có mùi gì lạ không? Mùi hóa chất nồng nặc hay là mùi thơm?",
        
        # --- PHASE 10: AGGREGATION & FINAL VERDICT ---
        "Chốt lại, với tư cách là chuyên gia, mày có khuyên tao mua con B09R94H5FS này cho mùa hè ở Sài Gòn (nóng) không? Tại sao?"
    ]

    for i, q in enumerate(test_cases):
        print(f"\n🔹 [Test {i+1}] USER: {q}")
        try:
            response = agent.answer(q, default_asin=default_asin)
            print(f"🔸 AI: {response}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        print("-" * 60)

if __name__ == "__main__":
    run_stress_test()