# backend/core/database.py
import json
import os
from typing import Optional
from core.config import settings

def _ensure_data_dir():
    d = os.path.dirname(settings.PLANS_FILE)
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

"""
LEGACY FUNCTION - NOT USED IN PRODUCTION

These functions were used before SQLAlchemy implementation.
They are kept for backward compatibility but should not be used.
All new code should use database/connection.py instead.
"""
def load_json(path) -> Optional[dict]:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return None
    return None

"""
LEGACY FUNCTION - NOT USED IN PRODUCTION

These functions were used before SQLAlchemy implementation.
They are kept for backward compatibility but should not be used.
All new code should use database/connection.py instead.
"""
def save_json(path, data):
    _ensure_data_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

"""
LEGACY FUNCTION - NOT USED IN PRODUCTION

These functions were used before SQLAlchemy implementation.
They are kept for backward compatibility but should not be used.
All new code should use database/connection.py instead.
"""
def load_plans():
    data = load_json(settings.PLANS_FILE)
    if not data:
        return {}
    return data

"""
LEGACY FUNCTION - NOT USED IN PRODUCTION

These functions were used before SQLAlchemy implementation.
They are kept for backward compatibility but should not be used.
All new code should use database/connection.py instead.
"""
def get_plan(plan_id: str):
    plans = load_plans()
    return plans.get(plan_id)

"""
LEGACY FUNCTION - NOT USED IN PRODUCTION

These functions were used before SQLAlchemy implementation.
They are kept for backward compatibility but should not be used.
All new code should use database/connection.py instead.
"""
def save_plan(plan_obj: dict):
    plans = load_plans()
    plans[plan_obj["plan_id"]] = plan_obj
    save_json(settings.PLANS_FILE, plans)
    return plan_obj