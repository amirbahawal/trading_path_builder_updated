#!/usr/bin/env python3
"""
Test script to verify fingerprint caching system
Tests that identical quiz answers return the same cached plan
"""

import sys
import time
from utils.fingerprint import generate_fingerprint
from core.config import settings
from core.db_helpers import get_cached_plan_by_fingerprint, save_plan_to_db

# Test quiz answers
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

print("=" * 60)
print("FINGERPRINT CACHING TEST")
print("=" * 60)

# Test 1: Generate fingerprints
print("\n1. Testing Fingerprint Generation:")
print("-" * 60)
fp1 = generate_fingerprint(test_answers_1, settings.TEMPLATE_VERSION)
fp2 = generate_fingerprint(test_answers_2, settings.TEMPLATE_VERSION)
fp3 = generate_fingerprint(test_answers_3, settings.TEMPLATE_VERSION)

print(f"Answers Set 1 Fingerprint: {fp1[:16]}...")
print(f"Answers Set 2 Fingerprint: {fp2[:16]}... (same answers, different order)")
print(f"Answers Set 3 Fingerprint: {fp3[:16]}... (different answers)")

if fp1 == fp2:
    print("✅ PASS: Same answers produce same fingerprint (order-independent)")
else:
    print("❌ FAIL: Same answers should produce same fingerprint")
    sys.exit(1)

if fp1 != fp3:
    print("✅ PASS: Different answers produce different fingerprint")
else:
    print("❌ FAIL: Different answers should produce different fingerprint")
    sys.exit(1)

# Test 2: Check cache lookup (should be empty initially)
print("\n2. Testing Cache Lookup (should be empty):")
print("-" * 60)
cached = get_cached_plan_by_fingerprint(fp1)
if cached is None:
    print("✅ PASS: No cached plan found (expected for first run)")
else:
    print(f"ℹ️  INFO: Found existing cached plan: {cached['plan_id']}")

# Test 3: Save a mock plan with fingerprint
print("\n3. Testing Plan Save with Fingerprint:")
print("-" * 60)
import uuid as uuid_module
mock_plan = {
    "user_id": str(uuid_module.uuid4()),  # Use a valid UUID
    "answers_json": test_answers_1,
    "answers_fingerprint": fp1,
    "template_version": settings.TEMPLATE_VERSION,
    "persona_label": "Test Persona",
    "overview_md": "# Test Overview\nThis is a test plan for caching.",
    "stages": [
        {
            "stage_number": 1,
            "title": "Stage 1: Test Foundation",
            "is_free": True,
            "content_md": "# Stage 1\nTest content for stage 1"
        },
        {
            "stage_number": 2,
            "title": "Stage 2: Test Execution",
            "is_free": False,
            "content_md": "# Stage 2\nTest content for stage 2"
        },
        {
            "stage_number": 3,
            "title": "Stage 3: Test Advanced",
            "is_free": False,
            "content_md": "# Stage 3\nTest content for stage 3"
        }
    ]
}

try:
    plan_id = save_plan_to_db(mock_plan)
    print(f"✅ PASS: Plan saved successfully with ID: {plan_id}")
    print(f"   Fingerprint: {fp1[:16]}...")
except Exception as e:
    print(f"❌ FAIL: Error saving plan: {e}")
    sys.exit(1)

# Test 4: Retrieve from cache using same fingerprint
print("\n4. Testing Cache Retrieval:")
print("-" * 60)
time.sleep(0.5)  # Small delay to ensure DB write completes

cached_plan = get_cached_plan_by_fingerprint(fp1)
if cached_plan:
    print(f"✅ PASS: Plan retrieved from cache")
    print(f"   Plan ID: {cached_plan['plan_id']}")
    print(f"   Persona: {cached_plan['persona_label']}")
    print(f"   Stages: {len(cached_plan['stages'])}")
    print(f"   Fingerprint Match: {cached_plan['answers_fingerprint'] == fp1}")
else:
    print(f"❌ FAIL: Could not retrieve cached plan")
    sys.exit(1)

# Test 5: Verify fingerprint matching with different key order
print("\n5. Testing Fingerprint Matching (different key order):")
print("-" * 60)
cached_plan_2 = get_cached_plan_by_fingerprint(fp2)
if cached_plan_2:
    if cached_plan_2['plan_id'] == cached_plan['plan_id']:
        print(f"✅ PASS: Same plan retrieved with reordered answers")
        print(f"   Plan ID: {cached_plan_2['plan_id']}")
    else:
        print(f"❌ FAIL: Different plan returned (should be same)")
        sys.exit(1)
else:
    print(f"❌ FAIL: Could not retrieve cached plan with reordered answers")
    sys.exit(1)

# Test 6: Verify different answers don't match
print("\n6. Testing Different Answers (should not match):")
print("-" * 60)
cached_plan_3 = get_cached_plan_by_fingerprint(fp3)
if cached_plan_3 is None:
    print(f"✅ PASS: No cached plan for different answers (expected)")
else:
    print(f"ℹ️  INFO: Found plan for different answers: {cached_plan_3['plan_id']}")
    print(f"   (This might be from a previous test run)")

# Final summary
print("\n" + "=" * 60)
print("FINGERPRINT CACHING TEST SUMMARY")
print("=" * 60)
print("✅ All tests passed!")
print("\nKey Features Verified:")
print("  ✓ Deterministic fingerprint generation")
print("  ✓ Order-independent hashing (key order doesn't matter)")
print("  ✓ Database persistence with fingerprint")
print("  ✓ Cache lookup by fingerprint")
print("  ✓ Same answers return same cached plan")
print("  ✓ Different answers generate different fingerprints")
print("\n" + "=" * 60)

