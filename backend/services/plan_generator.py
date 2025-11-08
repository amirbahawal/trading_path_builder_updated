from typing import Dict, Any, Optional, List
import uuid
import logging
from models.plan_model import PlanResponse, Stage
from utils.fingerprint import generate_fingerprint
from core.config import settings
from prompt_builder import build_prompt
from ai_client import get_ai_response
from core.db_helpers import save_plan_to_db, get_cached_plan_by_fingerprint
import re

logger = logging.getLogger(__name__)


def _short_guid():
    """Generate a short unique ID"""
    return uuid.uuid4().hex[:12]


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
    Generate stage content using AI.
    
    Args:
        answers: Quiz answers dictionary
        stage_index: Stage index (0-based)
        
    Returns:
        Generated markdown content
    """
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
    Check for cached plan by fingerprint.
    
    Args:
        fingerprint: Answers fingerprint
        
    Returns:
        PlanResponse if found, None otherwise
    """
    cached_data = get_cached_plan_by_fingerprint(fingerprint)
    if not cached_data:
        return None
    
    # Convert cached data to PlanResponse
    stages = []
    for i, stage_data in enumerate(cached_data.get("stages", [])):
        # Extract teaser for locked stages
        teaser = None
        if i > 0:  # Stages 2 and 3 are locked
            content = stage_data.get("content_md", "")
            teaser = _extract_teaser_bullets(content)
        
        stage = Stage(
            id=i+1,  # Stage ID: 1, 2, or 3
            title=stage_data.get("title", f"Stage {i+1}"),
            is_free=stage_data.get("is_free", i == 0),  # Stage 1 is free
            content=stage_data.get("content_md", ""),
            locked=not stage_data.get("is_free", i == 0),
            teaser=teaser
        )
        stages.append(stage)
    
    return PlanResponse(
        plan_id=cached_data["plan_id"],
        stages=stages
    )


def generate_plan_object(user_id: Optional[str], answers: Dict[str, Any]) -> PlanResponse:
    """
    Generate plan object from quiz answers.
    
    Args:
        user_id: Optional user ID
        answers: Quiz answers dictionary
        
    Returns:
        PlanResponse object
    """
    # Generate fingerprint for caching
    fingerprint = generate_fingerprint(answers, settings.TEMPLATE_VERSION)
    
    # Check for cached plan
    cached_plan = check_cached_plan(fingerprint)
    if cached_plan:
        logger.info(f"Retrieved from cache: plan {cached_plan.plan_id} with fingerprint {fingerprint[:16]}...")
        return cached_plan
    
    # Generate new plan using AI
    plan_id = f"plan-{_short_guid()}"
    stages = []
    
    # Generate all 3 stages
    for i in range(3):
        stage_number = i + 1
        try:
            content_md = generate_stage_content(answers, i)
            # Validate content
            if not content_md or content_md.strip() == "":
                logger.error(f"Stage {stage_number} content is empty after generation")
                # Use fallback content instead of failing
                content_md = f"Stage {stage_number} content is being generated. Please try again in a moment."
        except Exception as stage_error:
            logger.error(f"Error generating stage {stage_number}: {stage_error}", exc_info=True)
            # Use fallback content instead of failing - this prevents server crashes
            content_md = f"Stage {stage_number} content generation encountered an error. Please try again."
        
        # Stage 1 is free, others are locked initially
        is_free = (i == 0)
        
        # Determine title - Match CONTEXT.md exactly
        titles = [
            "Intro and Diagnostic",
            "Insights and Routine",
            "Frameworks and Playbooks"
        ]
        
        # Extract teaser for locked stages
        teaser = None
        if i > 0:  # Stages 2 and 3 are locked
            try:
                teaser = _extract_teaser_bullets(content_md)
            except Exception as teaser_error:
                logger.warning(f"Error extracting teaser for stage {stage_number}: {teaser_error}")
                teaser = []  # Empty teaser if extraction fails
        
        stage = Stage(
            id=stage_number,  # Stage ID: 1, 2, or 3
            title=titles[i],
            is_free=is_free,  # Stage 1 is free, others are not
            content=content_md,
            locked=not is_free,
            teaser=teaser
        )
        stages.append(stage)
    
    # Extract persona from Stage 1
    persona_label = _extract_persona_from_content(stages[0].content)
    
    # Create overview_md from Stage 1 content
    overview_md = stages[0].content
    
    # Build plan data for database
    plan_data = {
        "user_id": user_id,
        "answers_json": answers,
        "answers_fingerprint": fingerprint,
        "template_version": settings.TEMPLATE_VERSION,
        "persona_label": persona_label,
        "overview_md": overview_md,
        "stages": [
            {
                "stage_number": i + 1,
                "title": stage.title,
                "is_free": (i == 0),
                "content_md": stage.content
            }
            for i, stage in enumerate(stages)
        ]
    }
    
    # Save to database
    try:
        save_plan_to_db(plan_data)
        logger.info(f"Generated new plan {plan_id} with fingerprint {fingerprint[:16]}...")
    except Exception as e:
        logger.error(f"Error saving plan to database: {e}")
        # Continue anyway
    
    return PlanResponse(plan_id=plan_id, stages=stages)