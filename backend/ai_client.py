import openai
from typing import Optional
from core.config import settings
import json
import logging

logger = logging.getLogger(__name__)


def get_ai_response(prompt: str) -> str:
    """
    Get AI-generated response from OpenAI API.
    
    Args:
        prompt: The prompt to send to OpenAI
        
    Returns:
        Raw markdown content from AI response
    """
    # Fallback mock response
    mock_response = """## What Fits You

Mock content for testing.

## Next Steps

Mock steps.

## Top Trap to Avoid

Mock trap."""
    
    try:
        # Check if API key is configured
        if not settings.OPENAI_API_KEY:
            logger.error("⚠️ OPENAI_API_KEY not configured, using mock response")
            print("⚠️ OPENAI_API_KEY not configured, using mock response")
            return mock_response
        
        # Clean and validate API key
        api_key = settings.OPENAI_API_KEY.strip()
        
        # Check key length and format
        if len(api_key) < 20:
            logger.error(f"⚠️ API key seems too short ({len(api_key)} chars). Using mock response.")
            print(f"⚠️ API key seems too short ({len(api_key)} chars). Using mock response.")
            return mock_response
        
        # Log API key info (first 10 chars only for security)
        logger.info(f"🔑 Using OpenAI API key: {api_key[:10]}... (length: {len(api_key)}, model: {settings.OPENAI_MODEL})")
        print(f"🔑 Attempting OpenAI API call with model: {settings.OPENAI_MODEL}")
        
        # Check if this is an OpenAI Router key (starts with sk-or-v1-)
        # Router keys typically work with standard OpenAI endpoint, but may need custom base URL
        is_router_key = api_key.startswith("sk-or-v1-")
        
        if is_router_key:
            logger.info(f"Detected OpenAI Router key format (length: {len(api_key)})")
            print(f"Detected OpenAI Router key format (length: {len(api_key)})")
            # Router keys usually work with standard endpoint, but check for custom URL
            import os
            custom_url = os.getenv("OPENAI_ROUTER_URL", "")
            if custom_url:
                logger.info(f"Using custom router URL: {custom_url}")
                print(f"Using custom router URL: {custom_url}")
                client = openai.OpenAI(api_key=api_key, base_url=custom_url)
            else:
                # Try standard OpenAI endpoint (most routers proxy to this)
                client = openai.OpenAI(api_key=api_key)
        else:
            # Standard OpenAI key
            client = openai.OpenAI(api_key=api_key)
        
        # Call OpenAI API
        logger.info("📡 Calling OpenAI API...")
        print("📡 Calling OpenAI API...")
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
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            if content:
                logger.info("✅ OpenAI API call successful!")
                print("✅ OpenAI API call successful!")
                return content
            else:
                logger.warning("⚠️ OpenAI API returned empty content, using mock response")
                print("⚠️ OpenAI API returned empty content, using mock response")
                return mock_response
        
        logger.warning("⚠️ OpenAI API returned no choices, using mock response")
        print("⚠️ OpenAI API returned no choices, using mock response")
        return mock_response
        
    except openai.AuthenticationError as e:
        error_msg = str(e)
        logger.error(f"❌ OpenAI Authentication Error: {e}")
        print("=" * 60)
        print("❌ OPENAI AUTHENTICATION ERROR")
        print("=" * 60)
        print(f"Error: {error_msg}")
        print("\nPossible issues:")
        print("1. API key is invalid or expired")
        print("2. API key has incorrect format (check for line breaks or extra spaces)")
        print("3. API key doesn't have access to the requested model")
        print("=" * 60)
        print(f"API Key length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0} characters")
        print(f"API Key starts with: {settings.OPENAI_API_KEY[:10] if settings.OPENAI_API_KEY else 'N/A'}...")
        print(f"Model: {settings.OPENAI_MODEL}")
        print("=" * 60)
        print("Falling back to mock response")
        return mock_response
        
    except openai.APIError as e:
        error_msg = str(e)
        logger.error(f"❌ OpenAI API Error: {e}")
        print("=" * 60)
        print("❌ OPENAI API ERROR")
        print("=" * 60)
        print(f"Error: {error_msg}")
        print("\nPossible issues:")
        print("1. Rate limit exceeded - wait a moment and try again")
        print("2. Server error - OpenAI service may be down")
        print("3. Invalid request parameters")
        print("=" * 60)
        print("Falling back to mock response")
        return mock_response
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"❌ Unexpected error calling OpenAI API: {error_type}: {e}", exc_info=True)
        print("=" * 60)
        print(f"❌ UNEXPECTED ERROR: {error_type}")
        print("=" * 60)
        print(f"Error: {error_msg}")
        print("\nPossible issues:")
        print("1. Network connectivity problem")
        print("2. Invalid API key format")
        print("3. For Router keys (sk-or-v1-): Check if router endpoint is configured")
        print("4. For Router keys: Verify OPENAI_ROUTER_URL in .env if using custom endpoint")
        print("=" * 60)
        print(f"API Key length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0} characters")
        print(f"API Key starts with: {settings.OPENAI_API_KEY[:10] if settings.OPENAI_API_KEY else 'N/A'}...")
        print(f"Model: {settings.OPENAI_MODEL}")
        print("=" * 60)
        print("Falling back to mock response")
        return mock_response