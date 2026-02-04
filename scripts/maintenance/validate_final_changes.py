import duckdb
import pandas as pd
import sys

def validate():
    current_db = "/app/scout_app/database/scout_a.duckdb"
    backup_db = "/app/scout_app/database/scout_a_backup_PRE_TUMBLER_RESCUE.duckdb"
    
    print(f"🕵️ Validating Changes...")
    
    con = duckdb.connect(current_db)
    con.execute(f"ATTACH '{backup_db}' AS backup")
    
    # 1. Check for Regression (Loss of Data)
    print("\n--- CHECK 1: REGRESSION TEST ---")
    regression = con.execute("""
        SELECT p.asin, p.category, backup.products.rating_breakdown as old_bd, p.rating_breakdown as new_bd
        FROM products p
        JOIN backup.products ON p.asin = backup.products.asin
        WHERE backup.products.rating_breakdown IS NOT NULL 
        AND (p.rating_breakdown IS NULL OR CAST(p.rating_breakdown AS VARCHAR) != CAST(backup.products.rating_breakdown AS VARCHAR))
    """).df()
    
    if regression.empty:
        print("✅ PASSED: No existing breakdown data was lost or modified.")
    else:
        print(f"❌ FAILED: {len(regression)} ASINs lost data or changed unexpectedly!")
        print(regression.head().to_string())

    # 2. Check for Improvements (Gain of Data)
    print("\n--- CHECK 2: IMPROVEMENT TEST ---")
    improvements = con.execute("""
        SELECT p.asin, p.category, backup.products.rating_breakdown as old_bd, p.rating_breakdown as new_bd
        FROM products p
        JOIN backup.products ON p.asin = backup.products.asin
        WHERE backup.products.rating_breakdown IS NULL 
        AND p.rating_breakdown IS NOT NULL
    """).df()
    
    print(f"📈 GAINED: {len(improvements)} ASINs now have breakdown data.")
    print(f"   Breakdown by Category:")
    if not improvements.empty:
        print(improvements['category'].value_counts().to_string())
        print("\n   Sample Improvement:")
        print(improvements.head(3)[['asin', 'category', 'new_bd']].to_string(index=False))
    else:
        print("   No gains found.")

    con.close()

if __name__ == "__main__":
    validate()