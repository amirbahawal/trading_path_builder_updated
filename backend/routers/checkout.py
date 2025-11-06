from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
import uuid
from core.config import settings
from services.entitlement_service import grant_entitlement
from routers.analytics import emit_event, AnalyticsEvents
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class CheckoutRequest(BaseModel):
    plan_id: str
    email: str = ""  # Optional - not used for instant unlock
    user_id: Optional[str] = None


class CheckoutResponse(BaseModel):
    success: bool
    session_id: str
    message: str


class CheckoutCompleteRequest(BaseModel):
    session_id: str
    user_id: str
    plan_id: str


@router.post("/session", response_model=CheckoutResponse)
async def create_checkout_session(request: CheckoutRequest):
    """Create a checkout session - instantly grants access (no payment required)"""
    try:
        # Emit analytics event for unlock click
        user_identifier = request.user_id or request.email or "user"
        emit_event(AnalyticsEvents.UNLOCK_CLICK, user_identifier, request.plan_id)
        
        # Instant unlock - grant pro entitlement immediately
        session_id = f"unlock_{uuid.uuid4().hex[:10]}"
        
        # Grant pro entitlement immediately
        grant_entitlement(user_identifier, request.plan_id, "pro")
        
        # Emit analytics event for tier upgrade
        emit_event(AnalyticsEvents.TIER_UPGRADED_TO_PRO, user_identifier, request.plan_id)
        
        logger.info(f"[AUDIT] Plan unlocked | user_id={user_identifier} plan_id={request.plan_id}")
        
        return CheckoutResponse(
            success=True,
            session_id=session_id,
            message="Plan unlocked successfully"
        )
    except Exception as e:
        logger.error(f"Unlock failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete")
async def complete_checkout(request: CheckoutCompleteRequest):
    """Complete unlock process - verify and grant entitlement"""
    try:
        # Verify session_id format
        if not request.session_id.startswith("unlock_"):
            raise HTTPException(status_code=400, detail="Invalid session ID")
        
        # Grant entitlement if not already granted
        grant_entitlement(request.user_id, request.plan_id, "pro")
        
        # Emit analytics event for tier upgrade
        emit_event(AnalyticsEvents.TIER_UPGRADED_TO_PRO, request.user_id, request.plan_id)
        
        logger.info(f"[AUDIT] Plan unlocked | user_id={request.user_id} plan_id={request.plan_id}")
        
        return {
            "success": True,
            "tier": "pro",
            "message": "Plan unlocked"
        }
    except Exception as e:
        logger.error(f"Unlock failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{session_id}")
async def get_checkout_status(session_id: str):
    """Check unlock status"""
    try:
        if session_id.startswith("unlock_"):
            return {"status": "completed", "unlocked": True}
        else:
            return {"status": "unknown", "unlocked": False}
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))