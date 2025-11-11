from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
from pydantic import BaseModel
from services.plan_generator import generate_plan_object, check_cached_plan
from services.plan_generator import _short_guid
from services.entitlement_service import check_entitlement, can_access_stage, grant_entitlement
from core.db_helpers import get_plan_from_db
from models.plan_model import PlanResponse, Stage, PlanRequest, SummaryRequest, SummaryResponse
from utils.auth_utils import get_current_user, get_current_user_optional
from utils.fingerprint import generate_fingerprint
from core.config import settings
from routers.analytics import emit_event, AnalyticsEvents
import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=PlanResponse)
async def create_plan(request: PlanRequest, current_user: dict = Depends(get_current_user_optional)):
    """Create a new plan from quiz answers"""
    user_id = current_user["user_id"]
    
    try:
        # Generate plan with fingerprint caching
        # Note: generate_plan_object automatically grants "pro" entitlement after generation
        plan_response = generate_plan_object(user_id, request.answers)
        
        # Check actual entitlement tier (should be "pro" after auto-grant)
        try:
            tier = check_entitlement(user_id, plan_response.plan_id)
            logger.info(f"[AUDIT] Plan created | user_id={user_id} plan_id={plan_response.plan_id} tier={tier}")
        except Exception as e:
            logger.warning(f"[AUDIT] Failed to check entitlement, defaulting to pro: {e}")
            tier = "pro"  # Default to pro since we just generated all 3 stages
        
        # Build response with spec fields
        persona = {"label": "Pattern-Seeker"}  # Default persona
        overview_md = plan_response.stages[0].content if plan_response.stages else ""  # Stage 1 content
        
        # Update stages with id and is_free
        # Since we auto-grant "pro" tier, all stages should be unlocked
        updated_stages = []
        for i, stage in enumerate(plan_response.stages):
            # For pro tier, all stages are unlocked
            is_locked = (tier != "pro" and i > 0)  # Only lock stages 2 & 3 if not pro
            
            # Send full content for unlocked stages
            stage_content = ""
            if not is_locked:
                stage_content = stage.content
            # Locked stages (2 and 3) get empty content - only teaser is sent
            
            updated_stage = Stage(
                id=i + 1,  # Stage ID: 1, 2, or 3
                title=stage.title,
                is_free=(i == 0),  # True for Stage 1, False for others
                content=stage_content,  # Empty for locked stages, full for unlocked
                locked=is_locked,
                teaser=stage.teaser if is_locked else None  # Only include teaser for locked stages
            )
            updated_stages.append(updated_stage)
        
        return PlanResponse(
            plan_id=plan_response.plan_id,
            tier=tier,
            persona=persona,
            overview_md=overview_md,
            stages=updated_stages
        )
    except Exception as e:
        from ai_client import AIClientError
        if isinstance(e, AIClientError):
            logger.error(f"[AUDIT] Plan creation failed (AI error) | user_id={user_id} error={e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate plan: {str(e)}")
        logger.error(f"[AUDIT] Plan creation failed | user_id={user_id} error={e}")
        raise


@router.post("/summary", response_model=SummaryResponse)
async def generate_summary(request: SummaryRequest, current_user: dict = Depends(get_current_user_optional)):
    """
    Generate summary (Stage 1 content) from quiz answers.
    Uses fingerprint caching to return cached summary if available.
    Faster than full plan generation since it only checks/returns Stage 1.
    """
    user_id = current_user["user_id"]
    
    try:
        # Generate fingerprint for caching
        fingerprint = generate_fingerprint(request.answers, settings.TEMPLATE_VERSION)
        
        # Check for cached plan
        cached_plan = check_cached_plan(fingerprint)
        
        if cached_plan:
            # Return Stage 1 from cached plan
            stage1 = next((s for s in cached_plan.stages if s.id == 1), None)
            if stage1:
                logger.info(f"[AUDIT] Summary from cache | plan_id={cached_plan.plan_id} fingerprint={fingerprint[:16]}...")
                emit_event(AnalyticsEvents.QUIZ_COMPLETED, user_id, cached_plan.plan_id)
                
                return SummaryResponse(
                    plan_id=cached_plan.plan_id,
                    summary=stage1.content,
                    persona={"label": "Pattern-Seeker"},  # Default, can be extracted from content
                    cached=True
                )
        
        # If not cached, generate ONLY Stage 1 for faster response
        # This is much faster than generating all 3 stages
        logger.info(f"[AUDIT] Generating Stage 1 only for summary | user_id={user_id}")
        try:
            # Generate only Stage 1 content using the new AI client
            from ai_client import call_openai_for_stage, AIClientError
            stage1_content = call_openai_for_stage(
                answers=request.answers,
                stage_number=1,
                stage_focus="introduction and self-diagnostic assessment"
            )
            
            if not stage1_content or stage1_content.strip() == "":
                logger.error(f"[AUDIT] Stage 1 content is empty after generation | user_id={user_id}")
                raise HTTPException(status_code=500, detail="Failed to generate summary - Stage 1 content is empty")
            
            # Generate a deterministic plan_id from fingerprint (same answers = same plan_id)
            import uuid as uuid_lib
            import hashlib
            # Create deterministic UUID from fingerprint
            hash_obj = hashlib.md5(fingerprint.encode())
            hash_hex = hash_obj.hexdigest()
            # Convert to UUID format (32 hex chars -> UUID)
            plan_uuid = uuid_lib.UUID(hex=hash_hex)
            plan_id = f"plan-{plan_uuid}"
            
            # Save Stage 1 to database (so we have a plan_id, but stages 2 & 3 will be generated later)
            from core.db_helpers import save_plan_to_db
            plan_data = {
                "plan_id": plan_uuid,  # Pass UUID directly
                "user_id": user_id,
                "answers_json": request.answers,
                "answers_fingerprint": fingerprint,
                "template_version": settings.TEMPLATE_VERSION,
                "persona_label": "Pattern-Seeker",  # Will be extracted later
                "overview_md": stage1_content,
                "stages": [
                    {
                        "stage_number": 1,
                        "title": "Intro and Diagnostic",
                        "is_free": True,
                        "content_md": stage1_content
                    }
                    # Stages 2 & 3 will be generated when user unlocks or when createPlan is called
                ]
            }
            
            try:
                saved_plan_id = save_plan_to_db(plan_data)
                logger.info(f"[AUDIT] Saved Stage 1 plan to database | plan_id={saved_plan_id} (requested: {plan_id})")
                # Use the saved plan_id (should match, but use what's actually in DB)
                plan_id = f"plan-{saved_plan_id}" if not saved_plan_id.startswith("plan-") else saved_plan_id
            except Exception as db_error:
                logger.warning(f"[AUDIT] Failed to save plan to database (non-critical): {db_error}")
                # Continue anyway - plan_id is still valid
            
        except AIClientError as ai_error:
            logger.error(f"[AUDIT] Stage 1 generation failed (AI error) | user_id={user_id} error={ai_error}")
            raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(ai_error)}")
        except HTTPException:
            raise
        except Exception as gen_error:
            logger.error(f"[AUDIT] Stage 1 generation failed in summary endpoint | user_id={user_id} error={gen_error}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(gen_error)}")
        
        # Extract persona from Stage 1 content
        try:
            from services.plan_generator import _extract_persona_from_content
            persona_label = _extract_persona_from_content(stage1_content)
            if not persona_label:
                persona_label = "Pattern-Seeker"  # Default fallback
        except Exception as persona_error:
            logger.warning(f"[AUDIT] Failed to extract persona | user_id={user_id} error={persona_error}")
            persona_label = "Pattern-Seeker"  # Default fallback
        
        # Create initial "free" entitlement (non-critical, don't fail if this fails)
        if user_id and user_id != "anon":
            try:
                grant_entitlement(user_id, plan_id, "free")
                logger.info(f"[AUDIT] Summary generated | user_id={user_id} plan_id={plan_id} tier=free")
            except Exception as e:
                logger.error(f"[AUDIT] Entitlement grant failed | user_id={user_id} plan_id={plan_id} error={e}", exc_info=True)
                # Don't fail the request if entitlement grant fails - it's non-critical
        
        # Emit analytics event (non-critical, don't fail if this fails)
        try:
            emit_event(AnalyticsEvents.QUIZ_COMPLETED, user_id, plan_id)
        except Exception as analytics_error:
            logger.warning(f"[AUDIT] Analytics event failed | user_id={user_id} error={analytics_error}")
        
        return SummaryResponse(
            plan_id=plan_id,
            summary=stage1_content,
            persona={"label": persona_label},
            cached=False
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (they already have proper status codes)
        raise
    except Exception as e:
        from ai_client import AIClientError
        if isinstance(e, AIClientError):
            logger.error(f"[AUDIT] Summary generation failed (AI error) | user_id={user_id} error={e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")
        logger.error(f"[AUDIT] Summary generation failed | user_id={user_id} error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str, current_user: dict = Depends(get_current_user_optional)):
    """Get a specific plan by ID with tier-based access control"""
    try:
        effective_user_id = current_user["user_id"]
        
        # Get plan from database
        plan_data = get_plan_from_db(plan_id)
        if not plan_data:
            # Log at debug level to reduce noise - 404 is a valid response for missing plans
            logger.debug(f"Plan not found: {plan_id} (user_id={effective_user_id})")
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Log what we got from database
        logger.info(f"[DEBUG] Plan data from DB: plan_id={plan_id}, stages_count={len(plan_data.get('stages', []))}")
        for i, stage_data in enumerate(plan_data.get("stages", [])):
            logger.info(f"[DEBUG] Stage {i+1}: stage_number={stage_data.get('stage_number')}, title={stage_data.get('title', '')[:50]}, has_content={bool(stage_data.get('content_md'))}")
        
        # Get user's tier - wrap in try-except to handle errors gracefully
        # Use the actual plan_id from the database (not the input plan_id which might be partial)
        actual_plan_id = plan_data.get("plan_id", plan_id)
        try:
            tier = check_entitlement(effective_user_id, actual_plan_id)
            logger.info(f"[DEBUG] User tier: {tier} for user_id={effective_user_id}, plan_id={actual_plan_id}")
        except Exception as tier_error:
            logger.error(f"[ERROR] Failed to check entitlement: {tier_error}", exc_info=True)
            # Default to free tier if entitlement check fails
            tier = "free"
            logger.warning(f"[WARNING] Defaulting to 'free' tier due to entitlement check error")
        
        # Build stages with proper locked status based on tier
        stages = []
        stages_data = plan_data.get("stages", [])
        
        # Ensure we always return all 3 stages, even if some are missing from DB
        # This prevents stages 2 and 3 from not showing up
        expected_stages = [1, 2, 3]
        
        # If user is pro and stages 2/3 are missing content, try to generate them
        if tier == "pro":
            stages_dict = {s.get("stage_number"): s for s in stages_data}
            stage2_data = stages_dict.get(2, {})
            stage3_data = stages_dict.get(3, {})
            stage2_has_content = bool(stage2_data.get("content_md", "").strip())
            stage3_has_content = bool(stage3_data.get("content_md", "").strip())
            
            # If stages 2 or 3 are missing content for pro user, generate them
            if not stage2_has_content or not stage3_has_content:
                logger.warning(f"[GET_PLAN] Pro user but stages 2/3 missing content. Stage 2: {stage2_has_content}, Stage 3: {stage3_has_content}. This should have been generated on unlock!")
                # Note: We don't generate here to avoid blocking the request, but we log it
        
        for stage_id in expected_stages:
            stage_data = next((s for s in stages_data if s.get("stage_number") == stage_id), None)
            
            # If stage doesn't exist in DB, create a placeholder (shouldn't happen, but safety check)
            if not stage_data:
                logger.warning(f"[DEBUG] Stage {stage_id} not found in DB for plan_id={plan_id}, creating placeholder")
                stage_data = {
                    "stage_number": stage_id,
                    "title": f"Stage {stage_id}",
                    "is_free": (stage_id == 1),
                    "content_md": ""
                }
            
            # Determine if stage is locked based on tier
            if tier == "pro":
                is_locked = False  # All stages unlocked for pro users
            else:
                # Use actual_plan_id for access check
                try:
                    is_locked = not can_access_stage(effective_user_id, actual_plan_id, stage_id)
                except Exception:
                    # Default to locked if check fails
                    is_locked = (stage_id != 1)  # Stage 1 is always unlocked
            
            # Emit analytics event for stage preview viewing (locked stages)
            if is_locked:
                if stage_id == 2:
                    emit_event(AnalyticsEvents.STAGE2_PREVIEW_VIEWED, effective_user_id, actual_plan_id, stage_id)
                elif stage_id == 3:
                    emit_event(AnalyticsEvents.STAGE3_PREVIEW_VIEWED, effective_user_id, actual_plan_id, stage_id)
            
            # Extract teaser for locked stages
            teaser = None
            if is_locked:
                from services.plan_generator import _extract_teaser_bullets
                teaser = _extract_teaser_bullets(stage_data.get("content_md", ""))
            
            # SECURITY: Don't send full content for locked stages to free users
            # Only pro users should receive full content
            stage_content = ""
            if not is_locked:
                # Pro users get full content - check both content_md and content fields
                stage_content = stage_data.get("content_md", "") or stage_data.get("content", "")
                # Log warning if content is still empty for unlocked stages (this is a problem)
                if not stage_content and stage_id in [2, 3]:
                    logger.warning(f"[GET_PLAN] ⚠️ Stage {stage_id} is unlocked (tier={tier}) but has NO content! plan_id={plan_id}. This should not happen - content should be generated on unlock.")
            # Free users only get teaser (content is empty for locked stages)
            
            stage = Stage(
                id=stage_id,  # Add stage ID
                title=stage_data.get("title", ""),
                is_free=stage_data.get("is_free", stage_id == 1),  # Add is_free flag
                content=stage_content,  # Empty for locked stages, full content for unlocked
                locked=is_locked,
                teaser=teaser  # Include teaser for locked stages
            )
            stages.append(stage)
            logger.info(f"[DEBUG] Built stage {stage_id}: locked={is_locked}, content_len={len(stage_content)}, has_teaser={bool(teaser)}")
        
        # Get persona and overview from database
        persona = {"label": plan_data.get("persona_label", "Pattern-Seeker")}
        overview_md = plan_data.get("overview_md", "")
        
        logger.info(f"[DEBUG] Returning plan with {len(stages)} stages, tier={tier}")
        
        return PlanResponse(
            plan_id=actual_plan_id,  # Use actual plan_id from database
            tier=tier,
            persona=persona,
            overview_md=overview_md,
            stages=stages
        )
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions (404, etc.) - they will be handled by global handler with CORS
        raise
    except Exception as e:
        logger.error(f"[ERROR] Failed to get plan {plan_id}: {e}", exc_info=True)
        # Raise HTTPException - will be handled by global handler with CORS headers
        raise HTTPException(status_code=500, detail=f"Failed to retrieve plan: {str(e)}")


@router.get("/{plan_id}/stage/{stage_id}", response_model=Stage)
async def get_stage_content(plan_id: str, stage_id: int, current_user: dict = Depends(get_current_user)):
    """Get specific stage content with access verification"""
    user_id = current_user["user_id"]
    
    # Check if user can access this stage
    if not can_access_stage(user_id, plan_id, stage_id):
        raise HTTPException(status_code=403, detail="Unlock this stage for $5")
    
    # Emit analytics event for stage viewing (accessed stages)
    if stage_id == 2:
        emit_event(AnalyticsEvents.STAGE2_VIEWED, user_id, plan_id, stage_id)
    elif stage_id == 3:
        emit_event(AnalyticsEvents.STAGE3_VIEWED, user_id, plan_id, stage_id)
    
    # Get plan from database
    plan_data = get_plan_from_db(plan_id)
    if not plan_data:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Find the requested stage and return full content
    for stage_data in plan_data.get("stages", []):
        if stage_data.get("stage_number") == stage_id:
            return Stage(
                id=stage_id,  # Add stage ID
                title=stage_data.get("title", ""),
                is_free=stage_data.get("is_free", stage_id == 1),  # Add is_free flag
                content=stage_data.get("content_md", ""),
                locked=False
            )
    
    raise HTTPException(status_code=404, detail="Stage not found")