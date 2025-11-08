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
        user_identifier = request.user_id or request.email or "anon"
        logger.info(f"[CHECKOUT] Unlock request received: user_id={user_identifier} plan_id={request.plan_id}")
        
        emit_event(AnalyticsEvents.UNLOCK_CLICK, user_identifier, request.plan_id)
        
        # Instant unlock - grant pro entitlement immediately
        session_id = f"unlock_{uuid.uuid4().hex[:10]}"
        
        # Grant pro entitlement immediately (works with "anon" user_id)
        logger.info(f"[CHECKOUT] Attempting to grant entitlement: user_id={user_identifier} plan_id={request.plan_id}")
        
        try:
            entitlement_success = grant_entitlement(user_identifier, request.plan_id, "pro")
            
            if not entitlement_success:
                logger.error(f"[CHECKOUT] ❌ Failed to grant entitlement: user_id={user_identifier} plan_id={request.plan_id}")
                # Try to check what went wrong
                from services.entitlement_service import check_entitlement
                current_tier = check_entitlement(user_identifier, request.plan_id)
                logger.error(f"[CHECKOUT] Current tier after failed grant: {current_tier}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to grant access. Check server logs for details. user_id={user_identifier} plan_id={request.plan_id}"
                )
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"[CHECKOUT] ❌ Exception during entitlement grant: {e}", exc_info=True)
            import traceback
            logger.error(f"[CHECKOUT] Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to grant access: {str(e)}. Check server logs for details."
            )
        
        # Emit analytics event for tier upgrade
        emit_event(AnalyticsEvents.TIER_UPGRADED_TO_PRO, user_identifier, request.plan_id)
        
        # Broadcast WebSocket event for real-time update
        try:
            from routers.websocket import broadcast_plan_unlock
            await broadcast_plan_unlock(request.plan_id, user_identifier)
        except Exception as ws_error:
            # WebSocket broadcast failure should not break the unlock flow
            logger.warning(f"[CHECKOUT] Failed to broadcast WebSocket event: {ws_error}")
        
        logger.info(f"[AUDIT] ✅ Plan unlocked successfully | user_id={user_identifier} plan_id={request.plan_id} tier=pro")
        
        return CheckoutResponse(
            success=True,
            session_id=session_id,
            message="Plan unlocked successfully"
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"[CHECKOUT] ❌ Unlock failed with exception: {e}", exc_info=True)
        import traceback
        logger.error(f"[CHECKOUT] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Unlock failed: {str(e)}")


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
        
        # Broadcast WebSocket event for real-time update
        try:
            from routers.websocket import broadcast_plan_unlock
            await broadcast_plan_unlock(request.plan_id, request.user_id)
        except Exception as ws_error:
            # WebSocket broadcast failure should not break the unlock flow
            logger.warning(f"[CHECKOUT] Failed to broadcast WebSocket event: {ws_error}")
        
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