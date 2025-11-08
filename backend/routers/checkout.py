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
        
        # Get plan data to check if stages 2 and 3 need to be generated
        from core.db_helpers import get_plan_from_db
        plan_data = get_plan_from_db(request.plan_id)
        
        # Generate missing stages (2 and 3) if they don't have content
        if plan_data:
            stages_data = plan_data.get("stages", [])
            stages_dict = {s.get("stage_number"): s for s in stages_data}
            
            # Check if stages 2 and 3 need content generation
            stage2_content = stages_dict.get(2, {}).get("content_md", "").strip()
            stage3_content = stages_dict.get(3, {}).get("content_md", "").strip()
            
            if not stage2_content or not stage3_content:
                logger.info(f"[CHECKOUT] Stages 2 or 3 missing content. Stage 2: {len(stage2_content)} chars, Stage 3: {len(stage3_content)} chars. Generating...")
                
                # Generate all stages by calling plan generation
                try:
                    from services.plan_generator import generate_plan_object
                    answers = plan_data.get("answers_json", {})
                    
                    if not answers:
                        logger.error(f"[CHECKOUT] Cannot generate stages - plan has no answers_json")
                    else:
                        logger.info(f"[CHECKOUT] Generating full plan with answers: {list(answers.keys())}")
                        # Generate full plan with all 3 stages
                        plan_response = generate_plan_object(user_identifier, answers)
                        logger.info(f"[CHECKOUT] Generated plan with {len(plan_response.stages)} stages")
                        
                        # Update database with generated stages 2 and 3
                        from database.connection import SessionLocal
                        from database.models import Plan, Stage
                        import uuid as uuid_lib
                        
                        db = SessionLocal()
                        try:
                            # Convert plan_id to UUID using the same logic as entitlement service
                            from services.entitlement_service import _convert_plan_id_to_uuid
                            try:
                                plan_uuid = _convert_plan_id_to_uuid(request.plan_id)
                                logger.info(f"[CHECKOUT] Converted plan_id '{request.plan_id}' to UUID: {plan_uuid}")
                            except Exception as convert_error:
                                logger.error(f"[CHECKOUT] Failed to convert plan_id to UUID: {convert_error}")
                                plan_uuid = None
                            
                            # Look up plan by UUID
                            plan = None
                            if plan_uuid:
                                plan = db.query(Plan).filter(Plan.id == plan_uuid).first()
                                if plan:
                                    logger.info(f"[CHECKOUT] Found plan in DB: {plan.id}")
                                else:
                                    logger.warning(f"[CHECKOUT] Plan not found with UUID: {plan_uuid}")
                            
                            # If still not found, try to find by fingerprint (fallback)
                            if not plan:
                                logger.warning(f"[CHECKOUT] Plan not found by UUID, trying to find by fingerprint...")
                                # This is a fallback - shouldn't normally be needed
                            
                            if plan:
                                logger.info(f"[CHECKOUT] Found plan in DB: {plan.id}, updating stages 2 and 3")
                                
                                # Delete existing stages 2 and 3 if they exist
                                deleted_count = db.query(Stage).filter(
                                    Stage.plan_id == plan.id,
                                    Stage.stage_number.in_([2, 3])
                                ).delete()
                                logger.info(f"[CHECKOUT] Deleted {deleted_count} existing stages 2/3")
                                
                                # Add stages 2 and 3 with generated content
                                stages_added = 0
                                for i, stage_obj in enumerate(plan_response.stages):
                                    stage_number = i + 1
                                    # Only add stages 2 and 3 (stage 1 already exists)
                                    if stage_number in [2, 3] and stage_obj.content and stage_obj.content.strip():
                                        stage = Stage(
                                            id=uuid_lib.uuid4(),
                                            plan_id=plan.id,
                                            stage_number=stage_number,
                                            title=stage_obj.title,
                                            is_free=(stage_number == 1),
                                            content_md=stage_obj.content
                                        )
                                        db.add(stage)
                                        stages_added += 1
                                        logger.info(f"[CHECKOUT] ✅ Added stage {stage_number} with {len(stage_obj.content)} chars of content")
                                
                                if stages_added > 0:
                                    db.commit()
                                    logger.info(f"[CHECKOUT] ✅ Successfully committed {stages_added} stages to database")
                                    
                                    # Verify stages were saved
                                    saved_stages = db.query(Stage).filter(
                                        Stage.plan_id == plan.id,
                                        Stage.stage_number.in_([2, 3])
                                    ).all()
                                    logger.info(f"[CHECKOUT] Verified: {len(saved_stages)} stages saved (stages 2 and 3)")
                                    for saved_stage in saved_stages:
                                        logger.info(f"[CHECKOUT]   - Stage {saved_stage.stage_number}: {len(saved_stage.content_md)} chars")
                                else:
                                    logger.error(f"[CHECKOUT] ❌ No stages were added! Generated stages: {[s.stage_number for s in plan_response.stages]}")
                                    db.rollback()
                            else:
                                logger.error(f"[CHECKOUT] ❌ Plan not found in database. Tried plan_id: {request.plan_id}, clean_plan_id: {clean_plan_id}, plan_uuid: {plan_uuid}")
                        except Exception as db_error:
                            db.rollback()
                            logger.error(f"[CHECKOUT] Failed to update plan stages in DB: {db_error}", exc_info=True)
                            # Don't fail unlock - continue even if DB update fails
                        finally:
                            db.close()
                except Exception as gen_error:
                    logger.error(f"[CHECKOUT] Failed to generate missing stages: {gen_error}", exc_info=True)
                    # Continue with unlock even if generation fails - user can still access what exists
            else:
                logger.info(f"[CHECKOUT] Stages 2 and 3 already have content. Stage 2: {len(stage2_content)} chars, Stage 3: {len(stage3_content)} chars")
        
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