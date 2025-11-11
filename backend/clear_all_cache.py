"""Clear all cached plans from the database."""

import sqlite3
import os

DB_PATH = "dev.db"


def clear_all_cache():
    if not os.path.exists(DB_PATH):
        print("❌ Database file not found at:", DB_PATH)
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM plans")
        plans_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stages")
        stages_count = cursor.fetchone()[0]
        
        print(f"📊 Found {plans_count} cached plans and {stages_count} stages")
        
        if plans_count == 0:
            print("✅ Database already empty")
            conn.close()
            return
        
        print("🗑️  Deleting all cached plans...")
        cursor.execute("DELETE FROM stages")
        cursor.execute("DELETE FROM plans")
        
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM plans")
        remaining = cursor.fetchone()[0]
        
        if remaining == 0:
            print("✅ All cached plans successfully deleted!")
        else:
            print(f"⚠️  Warning: {remaining} plans still remain")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("="*60)
    print("🧹 CACHE CLEANER")
    print("="*60)
    clear_all_cache()
    print("="*60)

