#!/usr/bin/env python3
"""
Clear any cached plans that contain mock content from the database.
Run this if you're seeing mock content after updating your API key.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from database.models import Plan, Stage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_mock_plans():
    """Remove all plans that contain mock content"""
    db = SessionLocal()
    try:
        # Find all plans
        all_plans = db.query(Plan).all()
        logger.info(f"Found {len(all_plans)} total plans in database")
        
        # Find plans with mock content
        mock_plan_ids = []
        for plan in all_plans:
            # Check overview_md
            if plan.overview_md and "Mock content" in plan.overview_md:
                mock_plan_ids.append(plan.id)
                logger.info(f"Found mock plan: {plan.id} (created: {plan.created_at})")
                continue
            
            # Check stages
            stages = db.query(Stage).filter(Stage.plan_id == plan.id).all()
            for stage in stages:
                if stage.content_md and ("Mock content" in stage.content_md or "Mock steps" in stage.content_md or "Mock trap" in stage.content_md):
                    if plan.id not in mock_plan_ids:
                        mock_plan_ids.append(plan.id)
                        logger.info(f"Found mock plan (in stage): {plan.id} (created: {plan.created_at})")
                    break
        
        if not mock_plan_ids:
            logger.info("✅ No mock plans found in database")
            return
        
        # Delete mock plans
        logger.info(f"Deleting {len(mock_plan_ids)} mock plans...")
        for plan_id in mock_plan_ids:
            # Delete stages first
            db.query(Stage).filter(Stage.plan_id == plan_id).delete()
            # Delete plan
            db.query(Plan).filter(Plan.id == plan_id).delete()
        
        db.commit()
        logger.info(f"✅ Successfully deleted {len(mock_plan_ids)} mock plans")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error clearing mock plans: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🧹 Clearing Mock Plans from Database")
    print("=" * 60)
    clear_mock_plans()
    print("=" * 60)

