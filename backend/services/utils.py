# backend/services/utils.py
import json
import os
from database.models import RateLimitEvent
from datetime import datetime, timedelta
import uuid

def load_mock_plan():
    from core.config import settings
    try:
        if os.path.exists(settings.MOCK_PLANS_FILE):
            with open(settings.MOCK_PLANS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    # final fallback
    return {
        "plan_id": "mock-plan-001",
        "stages": [
            {"title":"Stage 1: Foundation","content":"Learn the fundamentals.","locked":False},
            {"title":"Stage 2: Execution","content":"Start executing your routine.","locked":True},
            {"title":"Stage 3: Optimization","content":"Refine and scale.","locked":True},
        ]
    }

def log_rate_event(db, ip, email, endpoint, event_type):
    event = RateLimitEvent(
        id=str(uuid.uuid4()),
        email=email,
        ip=ip,
        endpoint=endpoint,
        event_type=event_type,
        timestamp=datetime.utcnow()
    )
    db.add(event)
    db.commit()

def can_rate_limit(db, ip, email, endpoint, event_type, period_sec, max_count):
    window_start = datetime.utcnow() - timedelta(seconds=period_sec)
    q = db.query(RateLimitEvent).filter(
        RateLimitEvent.endpoint == endpoint,
        RateLimitEvent.event_type == event_type,
        RateLimitEvent.timestamp >= window_start
    )
    if ip:
        q = q.filter(RateLimitEvent.ip == ip)
    if email:
        q = q.filter(RateLimitEvent.email == email)
    count = q.count()
    return count < max_count
