import openai
from typing import Optional, Dict, Any, List
from core.config import settings
from prompt_builder import build_prompt
import logging
import uuid

logger = logging.getLogger(__name__)


class AIClientError(Exception):
    """Custom exception for AI client errors"""
    pass


def _get_openai_client():
    """Get configured OpenAI client"""
    if not settings.OPENAI_API_KEY:
        raise AIClientError("OPENAI_API_KEY not configured")
    
    api_key = settings.OPENAI_API_KEY.strip()
    
    if len(api_key) < 20:
        raise AIClientError(f"API key seems too short ({len(api_key)} chars)")
    
    # Check if this is an OpenAI Router key (starts with sk-or-v1-)
    is_router_key = api_key.startswith("sk-or-v1-")
    
    if is_router_key:
        import os
        custom_url = os.getenv("OPENAI_ROUTER_URL", "")
        if custom_url:
            logger.info(f"Using custom router URL: {custom_url}")
            return openai.OpenAI(api_key=api_key, base_url=custom_url)
        else:
            return openai.OpenAI(api_key=api_key)
    else:
        return openai.OpenAI(api_key=api_key)


def call_openai_for_stage(
    answers: Dict[str, Any],
    stage_number: int,
    stage_focus: str
) -> str:
    """
    Make actual OpenAI API call for a specific stage.
    
    Args:
        answers: Quiz answers dictionary
        stage_number: Stage number (1, 2, or 3)
        stage_focus: Description of stage focus for logging
    
    Returns:
        Generated markdown content
    
    Raises:
        AIClientError: If API call fails or returns insufficient content
    """
    try:
        # Build prompt for this stage
        prompt = build_prompt(answers, stage_number)
        
        logger.info(f"📡 Calling OpenAI API for Stage {stage_number} ({stage_focus})...")
        
        # Get OpenAI client
        client = _get_openai_client()
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a neutral trading mentor providing educational content only. No financial advice or promises of results."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_OUTPUT_TOKENS
        )
        
        # Extract content from response
        if not response.choices or len(response.choices) == 0:
            raise AIClientError(f"Stage {stage_number} returned no choices")
        
        content = response.choices[0].message.content
        
        if not content or len(content.strip()) < 100:
            raise AIClientError(
                f"Stage {stage_number} returned insufficient content "
                f"(got {len(content) if content else 0} characters, need at least 100)"
            )
        
        # Check for mock content indicators
        mock_indicators = ["Mock content", "Mock steps", "Mock trap", "Mock response"]
        if any(indicator in content for indicator in mock_indicators):
            raise AIClientError(f"Stage {stage_number} returned mock content - API call may have failed")
        
        logger.info(f"✅ Stage {stage_number} generated successfully ({len(content)} characters)")
        return content
        
    except AIClientError:
        # Re-raise AIClientError as-is
        raise
    except openai.AuthenticationError as e:
        error_msg = f"OpenAI Authentication Error: {e}"
        logger.error(f"❌ {error_msg}")
        raise AIClientError(error_msg) from e
    except openai.APIError as e:
        error_msg = f"OpenAI API Error: {e}"
        logger.error(f"❌ {error_msg}")
        raise AIClientError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error calling OpenAI API for Stage {stage_number}: {e}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        raise AIClientError(error_msg) from e


def generate_all_stages(answers: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate all 3 stages via OpenAI API.
    
    Args:
        answers: Quiz answers dictionary
    
    Returns:
        List of stage dictionaries with stage_number, title, content, and teaser
    
    Raises:
        AIClientError: If any stage fails or has insufficient content
    """
    stages = []
    
    # Stage 1: Intro and Diagnostic
    try:
        stage1_content = call_openai_for_stage(
            answers=answers,
            stage_number=1,
            stage_focus="introduction and self-diagnostic assessment"
        )
        stages.append({
            'stage_number': 1,
            'title': 'Intro and Diagnostic',
            'content': stage1_content,
            'teaser': None  # Stage 1 doesn't need teaser (it's free)
        })
    except AIClientError as e:
        logger.error(f"❌ Failed to generate Stage 1: {e}")
        raise AIClientError(f"Stage 1 generation failed: {e}") from e
    
    # Stage 2: Insights and Routine
    try:
        stage2_content = call_openai_for_stage(
            answers=answers,
            stage_number=2,
            stage_focus="personalized insights and daily trading routine"
        )
        stages.append({
            'stage_number': 2,
            'title': 'Insights and Routine',
            'content': stage2_content,
            'teaser': None  # Teaser will be extracted later
        })
    except AIClientError as e:
        logger.error(f"❌ Failed to generate Stage 2: {e}")
        raise AIClientError(f"Stage 2 generation failed: {e}") from e
    
    # Stage 3: Frameworks and Playbooks
    try:
        stage3_content = call_openai_for_stage(
            answers=answers,
            stage_number=3,
            stage_focus="frameworks, playbooks, and action plans"
        )
        stages.append({
            'stage_number': 3,
            'title': 'Frameworks and Playbooks',
            'content': stage3_content,
            'teaser': None  # Teaser will be extracted later
        })
    except AIClientError as e:
        logger.error(f"❌ Failed to generate Stage 3: {e}")
        raise AIClientError(f"Stage 3 generation failed: {e}") from e
    
    # Validate all stages have content
    if len(stages) != 3:
        raise AIClientError(f"Expected 3 stages, got {len(stages)}")
    
    for idx, stage in enumerate(stages):
        if not stage.get('content') or len(stage['content']) < 100:
            raise AIClientError(f"Stage {idx + 1} has insufficient content")
    
    logger.info("✅ All 3 stages generated successfully via OpenAI API")
    return stages


# Legacy function for backward compatibility
def get_ai_response(prompt: str) -> str:
    """
    Legacy function - Get AI-generated response from OpenAI API.
    This is kept for backward compatibility but should not be used for new code.
    Use generate_all_stages() instead.
    
    Args:
        prompt: The prompt to send to OpenAI
    
    Returns:
        Raw markdown content from AI response
    
    Raises:
        AIClientError: If API call fails
    """
    try:
        client = _get_openai_client()
        
        logger.info("📡 Calling OpenAI API...")
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a neutral trading mentor providing educational content only. No financial advice or promises of results."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_OUTPUT_TOKENS
        )
        
        if not response.choices or len(response.choices) == 0:
            raise AIClientError("OpenAI API returned no choices")
        
        content = response.choices[0].message.content
        
        if not content or len(content.strip()) < 100:
            raise AIClientError(
                f"Insufficient content returned "
                f"(got {len(content) if content else 0} characters, need at least 100)"
            )
        
        logger.info("✅ OpenAI API call successful!")
        return content
        
    except AIClientError:
        raise
    except openai.AuthenticationError as e:
        error_msg = f"OpenAI Authentication Error: {e}"
        logger.error(f"❌ {error_msg}")
        raise AIClientError(error_msg) from e
    except openai.APIError as e:
        error_msg = f"OpenAI API Error: {e}"
        logger.error(f"❌ {error_msg}")
        raise AIClientError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error calling OpenAI API: {e}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        raise AIClientError(error_msg) from e
