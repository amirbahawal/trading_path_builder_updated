import openai
from typing import Optional
from core.config import settings
import json


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
            print("Warning: OPENAI_API_KEY not configured, using mock response")
            return mock_response
        
        # Clean and validate API key
        api_key = settings.OPENAI_API_KEY.strip()
        
        # Check key length and format
        if len(api_key) < 20:
            print(f"Warning: API key seems too short ({len(api_key)} chars). Using mock response.")
            return mock_response
        
        # Check if this is an OpenAI Router key (starts with sk-or-v1-)
        # Router keys typically work with standard OpenAI endpoint, but may need custom base URL
        is_router_key = api_key.startswith("sk-or-v1-")
        
        if is_router_key:
            print(f"Detected OpenAI Router key format (length: {len(api_key)})")
            # Router keys usually work with standard endpoint, but check for custom URL
            import os
            custom_url = os.getenv("OPENAI_ROUTER_URL", "")
            if custom_url:
                print(f"Using custom router URL: {custom_url}")
                client = openai.OpenAI(api_key=api_key, base_url=custom_url)
            else:
                # Try standard OpenAI endpoint (most routers proxy to this)
                client = openai.OpenAI(api_key=api_key)
        else:
            # Standard OpenAI key
            client = openai.OpenAI(api_key=api_key)
        
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
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            return content if content else mock_response
        
        return mock_response
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error calling OpenAI API: {e}")
        
        # Provide helpful diagnostics
        if "401" in error_msg or "unauthorized" in error_msg.lower() or "invalid_api_key" in error_msg.lower():
            print("=" * 60)
            print("⚠️  API KEY ERROR DETECTED")
            print("=" * 60)
            print("Possible issues:")
            print("1. API key is invalid or expired")
            print("2. API key has incorrect format (check for line breaks or extra spaces)")
            print("3. For Router keys (sk-or-v1-): Check if router endpoint is configured")
            print("4. For Router keys: Verify OPENAI_ROUTER_URL in .env if using custom endpoint")
            print("=" * 60)
            print(f"API Key length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0} characters")
            print(f"API Key starts with: {settings.OPENAI_API_KEY[:10] if settings.OPENAI_API_KEY else 'N/A'}...")
            print("=" * 60)
        
        print("Falling back to mock response")
        return mock_response