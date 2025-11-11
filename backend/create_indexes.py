#!/usr/bin/env python3
"""
Script to create missing indexes in the database
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from database.connection import engine, SQLALCHEMY_AVAILABLE

def create_indexes():
    """Create missing indexes in the database"""
    if not SQLALCHEMY_AVAILABLE:
        print("❌ SQLAlchemy not available, cannot create indexes")
        return 1
    
    try:
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # Create fingerprint index
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_plans_fingerprint ON plans (answers_fingerprint)"))
                conn.commit()
                print("✅ Created index: idx_plans_fingerprint")
            except Exception as e:
                print(f"⚠️  Error creating idx_plans_fingerprint: {e}")
                # Try to continue with other indexes
            
            # Create entitlements user index
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_entitlements_user ON entitlements (user_id)"))
                conn.commit()
                print("✅ Created index: idx_entitlements_user")
            except Exception as e:
                print(f"⚠️  Error creating idx_entitlements_user: {e}")
        
        print("\n✅ Index creation completed!")
        return 0
        
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(create_indexes())

