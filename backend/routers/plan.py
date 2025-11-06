from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
from pydantic import BaseModel
from services.plan_generator import generate_plan_object, check_cached_plan, generate_stage_content
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
        plan_response = generate_plan_object(user_id, request.answers)
        
        # Create initial "free" entitlement for the user
        if user_id and user_id != "anon":
            try:
                grant_entitlement(user_id, plan_response.plan_id, "free")
                logger.info(f"[AUDIT] Plan created | user_id={user_id} plan_id={plan_response.plan_id} context={{'tier':'free'}}")
            except Exception as e:
                logger.error(f"[AUDIT] Entitlement grant failed | user_id={user_id} plan_id={plan_response.plan_id} error={e}")
        
        # Build response with spec fields
        tier = "free"  # Initially free
        persona = {"label": "Pattern-Seeker"}  # Default persona
        overview_md = plan_response.stages[0].content if plan_response.stages else ""  # Stage 1 content
        
        # Update stages with id and is_free
        # SECURITY: Don't send full content for locked stages to free users
        updated_stages = []
        for i, stage in enumerate(plan_response.stages):
            is_locked = stage.locked
            
            # Only send full content for unlocked stages (Stage 1 for free users)
            stage_content = ""
            if not is_locked:
                stage_content = stage.content
            # Locked stages (2 and 3) get empty content - only teaser is sent
            
            updated_stage = Stage(
                id=i + 1,  # Stage ID: 1, 2, or 3
                title=stage.title,
                is_free=(i == 0),  # True for Stage 1, False for others
                content=stage_content,  # Empty for locked stages
                locked=is_locked,
                teaser=stage.teaser  # Include teaser for locked stages
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
        
        # If not cached, generate full plan (which creates Stage 1)
        # This ensures we have a plan_id for the summary page
        plan_response = generate_plan_object(user_id, request.answers)
        
        # Extract Stage 1 content
        stage1 = next((s for s in plan_response.stages if s.id == 1), None)
        if not stage1:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
        
        # Extract persona from Stage 1 content
        from services.plan_generator import _extract_persona_from_content
        persona_label = _extract_persona_from_content(stage1.content)
        
        # Create initial "free" entitlement
        if user_id and user_id != "anon":
            try:
                grant_entitlement(user_id, plan_response.plan_id, "free")
                logger.info(f"[AUDIT] Summary generated | user_id={user_id} plan_id={plan_response.plan_id} tier=free")
            except Exception as e:
                logger.error(f"[AUDIT] Entitlement grant failed | user_id={user_id} plan_id={plan_response.plan_id} error={e}")
        
        emit_event(AnalyticsEvents.QUIZ_COMPLETED, user_id, plan_response.plan_id)
        
        return SummaryResponse(
            plan_id=plan_response.plan_id,
            summary=stage1.content,
            persona={"label": persona_label},
            cached=False
        )
        
    except Exception as e:
        logger.error(f"[AUDIT] Summary generation failed | user_id={user_id} error={e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific plan by ID with tier-based access control"""
    effective_user_id = current_user["user_id"]
    
    # Get plan from database
    plan_data = get_plan_from_db(plan_id)
    if not plan_data:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Get user's tier
    tier = check_entitlement(effective_user_id, plan_id)
    
    # Build stages with proper locked status based on tier
    stages = []
    for stage_data in plan_data.get("stages", []):
        stage_id = stage_data.get("stage_number", 1)
        
        # Determine if stage is locked based on tier
        if tier == "pro":
            is_locked = False  # All stages unlocked for pro users
        else:
            is_locked = not can_access_stage(effective_user_id, plan_id, stage_id)
        
        # Emit analytics event for stage preview viewing (locked stages)
        if is_locked:
            if stage_id == 2:
                emit_event(AnalyticsEvents.STAGE2_PREVIEW_VIEWED, effective_user_id, plan_id, stage_id)
            elif stage_id == 3:
                emit_event(AnalyticsEvents.STAGE3_PREVIEW_VIEWED, effective_user_id, plan_id, stage_id)
        
        # Extract teaser for locked stages
        teaser = None
        if is_locked:
            from services.plan_generator import _extract_teaser_bullets
            teaser = _extract_teaser_bullets(stage_data.get("content_md", ""))
        
        # SECURITY: Don't send full content for locked stages to free users
        # Only pro users should receive full content
        stage_content = ""
        if not is_locked:
            # Pro users get full content
            stage_content = stage_data.get("content_md", "")
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
    
    # Get persona and overview from database
    persona = {"label": plan_data.get("persona_label", "Pattern-Seeker")}
    overview_md = plan_data.get("overview_md", "")
    
    return PlanResponse(
        plan_id=plan_id,
        tier=tier,
        persona=persona,
        overview_md=overview_md,
        stages=stages
    )


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