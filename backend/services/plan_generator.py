from typing import Dict, Any, Optional, List
import uuid
import logging
from models.plan_model import PlanResponse, Stage
from utils.fingerprint import generate_fingerprint
from core.config import settings
from ai_client import generate_all_stages, AIClientError
from core.db_helpers import save_plan_to_db, get_cached_plan_by_fingerprint
from database.connection import SessionLocal
from database.models import Plan
from database.models import Stage as StageModel
import re

logger = logging.getLogger(__name__)

# Minimum content length for valid stages (in characters)
MIN_STAGE_CONTENT_LENGTH = 100

# Mock content indicators that should not be cached
MOCK_CONTENT_INDICATORS = ["Mock content", "Mock steps", "Mock trap", "Mock response"]


def _short_guid():
    """Generate a short unique ID"""
    return uuid.uuid4().hex[:12]


def _is_valid_stage_content(content: str) -> bool:
    """
    Validate that stage content is valid (not mock/incomplete).
    
    Args:
        content: Stage content to validate
    
    Returns:
        True if content is valid, False otherwise
    """
    if not content or not isinstance(content, str):
        return False
    
    # Check minimum length
    if len(content.strip()) < MIN_STAGE_CONTENT_LENGTH:
        return False
    
    # Check for mock content indicators
    if any(indicator in content for indicator in MOCK_CONTENT_INDICATORS):
        return False
    
    return True


def _validate_cached_plan(cached_data: dict) -> bool:
    """
    Validate that cached plan has all 3 stages with valid content.
    
    Args:
        cached_data: Cached plan data dictionary
    
    Returns:
        True if cached plan is valid, False otherwise
    """
    if not cached_data:
        return False
    
    stages = cached_data.get("stages", [])
    
    # Must have exactly 3 stages
    if len(stages) != 3:
        logger.warning(f"❌ Cached plan has {len(stages)} stages, expected 3")
        return False
    
    # Validate each stage has valid content
    for i, stage_data in enumerate(stages, 1):
        content = stage_data.get("content_md", "") or stage_data.get("content", "")
        
        if not _is_valid_stage_content(content):
            logger.warning(
                f"❌ Cached plan stage {i} has invalid content "
                f"(length: {len(content) if content else 0}, "
                f"has mock indicators: {any(indicator in content for indicator in MOCK_CONTENT_INDICATORS if content)})"
            )
            return False
    
    return True


def _delete_invalid_cache_entry(fingerprint: str):
    """
    Delete invalid cache entry from database.
    
    Args:
        fingerprint: Fingerprint of the invalid cache entry
    """
    db = SessionLocal()
    try:
        # Find plan by fingerprint
        plan = db.query(Plan).filter(Plan.answers_fingerprint == fingerprint).first()
        
        if plan:
            logger.warning(f"🗑️  Deleting invalid cache entry: plan_id={plan.id}, fingerprint={fingerprint[:16]}...")
            
            # Delete associated stages
            db.query(StageModel).filter(StageModel.plan_id == plan.id).delete()
            
            # Delete plan
            db.delete(plan)
            db.commit()
            
            logger.info(f"✅ Deleted invalid cache entry: plan_id={plan.id}")
        else:
            logger.warning(f"⚠️  Cache entry not found for fingerprint: {fingerprint[:16]}...")
    
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error deleting invalid cache entry: {e}", exc_info=True)
    finally:
        db.close()


def _extract_teaser_bullets(content: str, max_bullets: int = 5, min_bullets: int = 3) -> List[str]:
    """
    Extract 3-5 bullet points from markdown content to create a teaser.
    
    Args:
        content: Markdown content
        max_bullets: Maximum number of bullets to extract (default: 5)
        min_bullets: Minimum number of bullets to extract (default: 3)
        
    Returns:
        List of teaser bullet points (3-5 items, or as many as available)
    """
    # Handle empty or None content
    if not content or not isinstance(content, str):
        return []
    
    bullets = []
    lines = content.split('\n')
    
    # First pass: Extract actual bullet points
    for line in lines:
        # Match lines that start with bullet markers (-, *, +) or numbered lists (1., 2., etc.)
        if re.match(r'^\s*[-*+]\s+', line):
            # Remove bullet marker and clean up
            bullet = re.sub(r'^\s*[-*+]\s+', '', line).strip()
            if bullet and len(bullet) > 5:  # Only include meaningful bullets
                bullets.append(bullet)
        elif re.match(r'^\s*\d+\.\s+', line):
            # Handle numbered lists
            bullet = re.sub(r'^\s*\d+\.\s+', '', line).strip()
            if bullet and len(bullet) > 5:
                bullets.append(bullet)
    
    # If we have enough bullets, return them (up to max)
    if len(bullets) >= min_bullets:
        return bullets[:max_bullets]
    
    # Second pass: Extract from paragraphs if we don't have enough bullets
    if len(bullets) < min_bullets:
        for line in lines:
            cleaned = line.strip()
            # Extract meaningful paragraphs (not empty, not headings, not already added bullets)
            if cleaned and not cleaned.startswith('#') and len(cleaned) > 20:
                # Skip if this line was already added as a bullet
                if cleaned not in bullets:
                    # Split by period and take first sentence, or use full line if it's short enough
                    if '.' in cleaned:
                        sentence = cleaned.split('.')[0].strip()
                        if sentence and len(sentence) > 10:
                            bullets.append(sentence + '.')
                    else:
                        # Use the full line if it's a good length
                        if len(cleaned) <= 150:  # Reasonable length for a bullet
                            bullets.append(cleaned)
                    
                    if len(bullets) >= min_bullets:
                        break
    
    # If still not enough, try to split long paragraphs into multiple bullets
    if len(bullets) < min_bullets:
        for line in lines:
            cleaned = line.strip()
            if cleaned and not cleaned.startswith('#') and len(cleaned) > 50:
                # Split by common sentence delimiters
                sentences = re.split(r'[.!?]+', cleaned)
                for sent in sentences:
                    sent = sent.strip()
                    if sent and len(sent) > 15 and sent not in bullets:
                        bullets.append(sent + '.')
                        if len(bullets) >= min_bullets:
                            break
                if len(bullets) >= min_bullets:
                    break
    
    # Return bullets (up to max, but at least what we found)
    result = bullets[:max_bullets]
    
    # Ensure we have at least 3 bullets if possible
    if len(result) < min_bullets and len(bullets) > len(result):
        # Take more from available bullets
        result = bullets[:max(min_bullets, len(bullets))]
    
    return result


def generate_stage_content(answers: Dict[str, Any], stage_index: int) -> str:
    """
    Generate stage content using AI (legacy function for backward compatibility).
    
    Args:
        answers: Quiz answers dictionary
        stage_index: Stage index (0-based)
        
    Returns:
        Generated markdown content
    
    Raises:
        AIClientError: If API call fails
    """
    from prompt_builder import build_prompt
    from ai_client import get_ai_response
    
    # Build prompt for this stage
    stage_number = stage_index + 1
    prompt = build_prompt(answers, stage_number)
    
    # Get AI response
    content = get_ai_response(prompt)
    
    return content


def _extract_persona_from_content(content: str) -> str:
    """
    Extract persona label from stage content.
    
    Args:
        content: Markdown content
        
    Returns:
        Persona label (default: "Pattern-Seeker")
    """
    # Try to extract from first heading
    lines = content.split('\n')
    for line in lines:
        if line.startswith('#'):
            # Remove markdown heading markers
            label = re.sub(r'^#+\s*', '', line).strip()
            if label:
                return label
    
    # Default persona
    return "Pattern-Seeker"


def check_cached_plan(fingerprint: str) -> Optional[PlanResponse]:
    """
    Check for cached plan by fingerprint and validate it.
    If cached plan is invalid, delete it and return None.
    
    Args:
        fingerprint: Answers fingerprint
        
    Returns:
        PlanResponse if found and valid, None otherwise
    """
    cached_data = get_cached_plan_by_fingerprint(fingerprint)
    if not cached_data:
        return None
    
    # Validate cached plan
    if not _validate_cached_plan(cached_data):
        logger.warning(f"❌ Cached plan is invalid, deleting and regenerating")
        _delete_invalid_cache_entry(fingerprint)
        return None
    
    # Convert cached data to PlanResponse
    stages = []
    for i, stage_data in enumerate(cached_data.get("stages", [])):
        stage_number = i + 1
        content = stage_data.get("content_md", "") or stage_data.get("content", "")
        
        # Extract teaser for locked stages
        teaser = None
        if i > 0:  # Stages 2 and 3 are locked
            teaser = _extract_teaser_bullets(content)
        
        stage = Stage(
            id=stage_number,
            title=stage_data.get("title", f"Stage {stage_number}"),
            is_free=stage_data.get("is_free", i == 0),  # Stage 1 is free
            content=content,
            locked=not stage_data.get("is_free", i == 0),
            teaser=teaser
        )
        stages.append(stage)
    
    logger.info(f"✅ Retrieved valid plan from cache: {cached_data['plan_id']}")
    return PlanResponse(
        plan_id=cached_data["plan_id"],
        stages=stages
    )


def generate_plan_object(user_id: Optional[str], answers: Dict[str, Any]) -> PlanResponse:
    """
    Generate plan object from quiz answers.
    Uses fingerprint caching - only generates new plan if not in cache or cache is invalid.
    
    Args:
        user_id: Optional user ID
        answers: Quiz answers dictionary
        
    Returns:
        PlanResponse object
    
    Raises:
        AIClientError: If API generation fails
    """
    # Generate fingerprint for caching
    fingerprint = generate_fingerprint(answers, settings.TEMPLATE_VERSION)
    logger.info(f"Generated fingerprint: {fingerprint[:16]}...")
    
    # Check for cached plan (with validation)
    cached_plan = check_cached_plan(fingerprint)
    if cached_plan:
        logger.info(f"✅ Retrieved valid plan from cache: {cached_plan.plan_id}")
        return cached_plan
    
    # Generate new plan using AI
    logger.info(f"🚀 Generating new plan via OpenAI API...")
    
    db = SessionLocal()
    try:
        # Generate all 3 stages via OpenAI API
        try:
            stages_data = generate_all_stages(answers)
            logger.info(f"✅ API call successful, creating plan in database...")
        except AIClientError as e:
            logger.error(f"❌ Failed to generate plan via OpenAI API: {e}")
            db.rollback()
            raise
        
        # Generate plan ID from fingerprint (deterministic)
        import hashlib
        hash_obj = hashlib.md5(fingerprint.encode())
        hash_hex = hash_obj.hexdigest()
        plan_uuid = uuid.UUID(hex=hash_hex)
        plan_id = f"plan-{plan_uuid}"
        
        # Extract persona from Stage 1
        stage1_content = stages_data[0]['content']
        persona_label = _extract_persona_from_content(stage1_content)
        overview_md = stage1_content
        
        # Build stages for PlanResponse
        stages = []
        titles = [
            "Intro and Diagnostic",
            "Insights and Routine",
            "Frameworks and Playbooks"
        ]
        
        for i, stage_data in enumerate(stages_data):
            stage_number = i + 1
            is_free = (i == 0)  # Stage 1 is free
            
            # Extract teaser for locked stages
            teaser = None
            if i > 0:  # Stages 2 and 3 are locked
                teaser = _extract_teaser_bullets(stage_data['content'])
            
            stage = Stage(
                id=stage_number,
                title=titles[i],
                is_free=is_free,
                content=stage_data['content'],
                locked=not is_free,
                teaser=teaser
            )
            stages.append(stage)
        
        # Build plan data for database
        plan_data = {
            "plan_id": plan_uuid,  # Use UUID directly
            "user_id": user_id,
            "answers_json": answers,
            "answers_fingerprint": fingerprint,
            "template_version": settings.TEMPLATE_VERSION,
            "persona_label": persona_label,
            "overview_md": overview_md,
            "stages": [
                {
                    "stage_number": stage_data['stage_number'],
                    "title": stage_data['title'],
                    "is_free": (stage_data['stage_number'] == 1),
                    "content_md": stage_data['content']
                }
                for stage_data in stages_data
            ]
        }
        
        # Save to database (only if all stages are valid)
        try:
            saved_plan_id = save_plan_to_db(plan_data)
            logger.info(f"✅ Plan cached successfully: {saved_plan_id}")
            # Use the saved plan_id to ensure consistency (already has "plan-" prefix from save_plan_to_db)
            plan_id = saved_plan_id
            
            # Get the actual plan from database to verify it exists and get the UUID
            from core.db_helpers import get_plan_from_db
            saved_plan_data = get_plan_from_db(saved_plan_id)
            if saved_plan_data:
                # Use the actual plan_id from database (might be different format)
                actual_plan_id = saved_plan_data.get("plan_id", saved_plan_id)
                logger.info(f"✅ Verified plan exists in database: {actual_plan_id}")
            else:
                logger.warning(f"⚠️ Plan not found in database after save: {saved_plan_id}")
        except Exception as db_error:
            db.rollback()
            logger.error(f"❌ Error saving plan to database: {db_error}", exc_info=True)
            # Don't fail the request if DB save fails - return plan anyway
            # But log it so we know there's an issue
        
        # Automatically grant entitlement for the generated plan (all stages unlocked)
        # Use the plan_uuid directly to ensure consistency with database
        try:
            from services.entitlement_service import grant_entitlement
            logger.info(f"🔓 Auto-granting entitlement for plan {plan_id} (user={user_id})")
            
            # Grant 'pro' tier entitlement (all stages unlocked)
            # Pass the plan_id string - grant_entitlement will convert it properly
            entitlement_success = grant_entitlement(user_id, plan_id, "pro")
            
            if entitlement_success:
                logger.info(f"✅ Entitlement granted: user={user_id}, plan={plan_id}, tier=pro")
                
                # Verify entitlement was created
                from services.entitlement_service import check_entitlement
                verified_tier = check_entitlement(user_id, plan_id)
                logger.info(f"✅ Verified entitlement tier: {verified_tier} for plan {plan_id}")
            else:
                logger.warning(f"⚠️ Failed to grant entitlement: user={user_id}, plan={plan_id}")
        except Exception as entitlement_error:
            logger.error(f"⚠️ Error granting entitlement: {entitlement_error}", exc_info=True)
            # Don't fail the entire operation if entitlement fails
            # The plan is still created, user can unlock manually
        
        return PlanResponse(plan_id=plan_id, stages=stages)
        
    except AIClientError:
        # Re-raise AIClientError (don't catch and suppress)
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Unexpected error generating plan: {e}", exc_info=True)
        raise AIClientError(f"Failed to generate plan: {e}") from e
    finally:
        db.close()
