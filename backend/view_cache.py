#!/usr/bin/env python3
"""
Script to view fingerprint cache in the database.
Shows all cached plans and their fingerprints.
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from database.connection import SessionLocal
from database.models import Plan, Stage
from utils.fingerprint import generate_fingerprint
from core.config import settings

def view_cache():
    """View all cached plans in the database"""
    db = SessionLocal()
    try:
        print("=" * 80)
        print("FINGERPRINT CACHE VIEWER")
        print("=" * 80)
        print()
        
        # Get all plans
        plans = db.query(Plan).order_by(Plan.created_at.desc()).all()
        
        if not plans:
            print("❌ No cached plans found in database.")
            print()
            print("To create cached plans:")
            print("  1. Complete the quiz in the frontend")
            print("  2. Plans will be automatically cached by fingerprint")
            return
        
        print(f"📊 Total Plans in Cache: {len(plans)}")
        print()
        
        # Group by fingerprint
        fingerprint_groups = {}
        for plan in plans:
            fp = plan.answers_fingerprint
            if fp not in fingerprint_groups:
                fingerprint_groups[fp] = []
            fingerprint_groups[fp].append(plan)
        
        unique_fingerprints = len(fingerprint_groups)
        print(f"🔑 Unique Fingerprints: {unique_fingerprints}")
        print(f"💾 Cache Efficiency: {(unique_fingerprints / len(plans) * 100):.1f}%")
        print()
        print("=" * 80)
        print()
        
        # Show each fingerprint group
        for idx, (fingerprint, group_plans) in enumerate(fingerprint_groups.items(), 1):
            print(f"📦 Fingerprint Group {idx}")
            print("-" * 80)
            print(f"   Fingerprint: {fingerprint[:32]}...")
            print(f"   Plans with this fingerprint: {len(group_plans)}")
            print()
            
            # Show first plan's details
            first_plan = group_plans[0]
            stages = db.query(Stage).filter(Stage.plan_id == first_plan.id).order_by(Stage.stage_number).all()
            
            print(f"   📋 Plan Details (showing first plan):")
            print(f"      Plan ID: {first_plan.id}")
            print(f"      User ID: {first_plan.user_id if first_plan.user_id else 'None (anonymous)'}")
            print(f"      Persona: {first_plan.persona_label}")
            print(f"      Template Version: {first_plan.template_version}")
            print(f"      Created: {first_plan.created_at}")
            print(f"      Stages: {len(stages)}")
            
            # Show answers
            answers = first_plan.answers_json
            if isinstance(answers, dict):
                print(f"      Answers:")
                print(f"        - Experience: {answers.get('experience', 'N/A')}")
                print(f"        - Timeframe: {answers.get('timeframe', 'N/A')}")
                print(f"        - Risk Tolerance: {answers.get('riskTolerance', 'N/A')}")
                print(f"        - Goal: {answers.get('goal', 'N/A')}")
            
            # Show all plan IDs with this fingerprint
            if len(group_plans) > 1:
                print(f"      Other plans with same fingerprint:")
                for plan in group_plans[1:]:
                    print(f"        - {plan.id} (created: {plan.created_at})")
            
            print()
        
        print("=" * 80)
        print()
        print("💡 Cache Information:")
        print("   - Same quiz answers = Same fingerprint = Cached plan returned")
        print("   - Different answers = Different fingerprint = New plan generated")
        print("   - Cache is stored in the 'plans' table with 'answers_fingerprint' column")
        # Get backend URL from environment or use default
        backend_url = os.getenv("BACKEND_HOST", "http://127.0.0.1:8000")
        print(f"   - View cache via API: GET {backend_url}/debug/cache/list")
        print()
        
    except Exception as e:
        print(f"❌ Error viewing cache: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_fingerprint_generation():
    """Test fingerprint generation with sample answers"""
    print("=" * 80)
    print("FINGERPRINT GENERATION TEST")
    print("=" * 80)
    print()
    
    test_answers_1 = {
        "experience": "beginner",
        "timeframe": "daily",
        "riskTolerance": "moderate",
        "goal": "income"
    }
    
    test_answers_2 = {
        "riskTolerance": "moderate",  # Different order
        "experience": "beginner",
        "goal": "income",
        "timeframe": "daily"
    }
    
    test_answers_3 = {
        "experience": "advanced",  # Different values
        "timeframe": "swing",
        "riskTolerance": "high",
        "goal": "growth"
    }
    
    fp1 = generate_fingerprint(test_answers_1, settings.TEMPLATE_VERSION)
    fp2 = generate_fingerprint(test_answers_2, settings.TEMPLATE_VERSION)
    fp3 = generate_fingerprint(test_answers_3, settings.TEMPLATE_VERSION)
    
    print("Test 1: Same answers, different order")
    print(f"   Answers 1: {test_answers_1}")
    print(f"   Fingerprint: {fp1[:32]}...")
    print(f"   Answers 2: {test_answers_2}")
    print(f"   Fingerprint: {fp2[:32]}...")
    print(f"   Match: {'✅ YES' if fp1 == fp2 else '❌ NO'}")
    print()
    
    print("Test 2: Different answers")
    print(f"   Answers 1: {test_answers_1}")
    print(f"   Fingerprint: {fp1[:32]}...")
    print(f"   Answers 3: {test_answers_3}")
    print(f"   Fingerprint: {fp3[:32]}...")
    print(f"   Match: {'❌ NO (expected)' if fp1 != fp3 else '✅ YES (unexpected)'}")
    print()
    
    print("=" * 80)
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_fingerprint_generation()
    else:
        view_cache()

