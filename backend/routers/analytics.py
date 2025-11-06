from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
# Optional SQLAlchemy imports
try:
    from sqlalchemy.orm import Session  # type: ignore
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Mock Session for development
    class Session:
        pass

from database.connection import get_db
from datetime import datetime
# Stripe removed - instant unlock only
import os
import logging

logger = logging.getLogger(__name__)

# Create router for explicit endpoints
router = APIRouter()

# Request model for event logging
class LogEventRequest(BaseModel):
    event: str
    user_id: Optional[str] = None
    plan_id: Optional[str] = None
    stage_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None


# Analytics event categories for consistency
class AnalyticsEvents:
    """All supported analytics events"""
    # Quiz & Plan Events
    QUIZ_COMPLETED = "quiz_completed"
    PLAN_CREATED = "plan_created"
    
    # Stage Viewing Events
    STAGE2_PREVIEW_VIEWED = "stage2_preview_viewed"
    STAGE3_PREVIEW_VIEWED = "stage3_preview_viewed"
    STAGE2_VIEWED = "stage2_viewed"
    STAGE3_VIEWED = "stage3_viewed"
    
    # Unlock & Payment Events
    UNLOCK_CLICK = "unlock_click"
    CHECKOUT_STARTED = "checkout_started"
    TIER_UPGRADED_TO_PRO = "tier_upgraded_to_pro"
    PAYMENT_SUCCEEDED = "payment_succeeded"


def log_event(
    event_name: str,
    user_id: Optional[str] = None,
    plan_id: Optional[str] = None,
    stage_id: Optional[int] = None,
    db: Optional[Session] = None,
    extra_data: Optional[Dict[str, Any]] = None
):
    """
    Centralized event logging with consistent formatting.
    
    Args:
        event_name: Name of the event
        user_id: User identifier
        plan_id: Plan identifier
        stage_id: Stage identifier (for stage-specific events)
        db: Database session
        extra_data: Additional metadata
    """
    timestamp = datetime.utcnow().isoformat()
    
    # Build structured log message
    log_entry = {
        "timestamp": timestamp,
        "event": event_name,
        "user_id": user_id,
        "plan_id": plan_id,
        "stage_id": stage_id,
    }
    
    if extra_data:
        log_entry["metadata"] = extra_data
    
    # Log to console (production should use dedicated service like Mixpanel, Segment, etc.)
    logger.info(f"[ANALYTICS] {log_entry}")
    
    # Optional: Store to database if schema exists
    if SQLALCHEMY_AVAILABLE and db:
        # Can extend to store in dedicated analytics table
        pass


# Explicit endpoint for event logging
@router.post("/events")
async def log_frontend_event(request: LogEventRequest):
    """
    Endpoint for frontend to log analytics events.
    
    Args:
        request: Event data containing event type, user_id, plan_id, stage_id, and optional data
        
    Returns:
        Success response with timestamp
    """
    try:
        db = next(get_db())
        log_event(
            request.event,
            user_id=request.user_id,
            plan_id=request.plan_id,
            stage_id=request.stage_id,
            db=db,
            extra_data=request.data
        )
        return {
            "success": True,
            "message": f"Event '{request.event}' logged successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.warning(f"Analytics logging failed: {e}")
        return {
            "success": False,
            "message": "Event logging failed",
            "error": str(e)
        }


# Backend event emission function (for use in other routers)
def emit_event(
    event_name: str,
    user_id: Optional[str] = None,
    plan_id: Optional[str] = None,
    stage_id: Optional[int] = None,
    extra_data: Optional[Dict[str, Any]] = None
):
    """
    Emit event from backend (when routes are accessed).
    Call this from routers to track server-side events.
    
    Usage:
        from routers.analytics import emit_event
        emit_event(AnalyticsEvents.STAGE2_VIEWED, user_id, plan_id, stage_id=2)
    """
    try:
        db = next(get_db())
        log_event(event_name, user_id, plan_id, stage_id, db, extra_data)
    except Exception as e:
        logger.warning(f"Failed to emit event: {e}")


def setup_analytics(app: FastAPI):
    @app.middleware("http")
    async def analytics_middleware(request, call_next):
        response = await call_next(request)
        event_name = None
        user_id = None
        plan_id = None
        
        if request.method == "POST" and request.url.path == "/quiz/submit":
            event_name = "quiz_completed"
        elif request.method == "POST" and request.url.path == "/plan":
            event_name = "plan_created"
            # Don't read body here to avoid conflicts
        elif request.method == "POST" and request.url.path == "/checkout/session":
            event_name = "checkout_started"
            # Don't read body here to avoid conflicts
        # Payment webhooks removed - instant unlock only
        pass
        
        if event_name:
            try:
                db = next(get_db())
                log_event(event_name, user_id, plan_id, db=db)
            except Exception as e:
                logger.warning(f"Analytics logging failed: {e}")
                log_event(event_name, user_id, plan_id, db=None)
        
        return response