#!/usr/bin/env python3
"""
Quick test script to verify OpenAI API key is working.
Run this to test your API key before starting the server.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import settings
import openai

def test_api_key():
    """Test if the OpenAI API key is valid and working"""
    
    print("=" * 60)
    print("🔍 Testing OpenAI API Key")
    print("=" * 60)
    
    # Check if key exists
    if not settings.OPENAI_API_KEY:
        print("❌ ERROR: OPENAI_API_KEY is not set in .env file")
        print("\nPlease add your API key to backend/.env:")
        print("OPENAI_API_KEY=your-key-here")
        return False
    
    api_key = settings.OPENAI_API_KEY.strip()
    
    # Check key length
    print(f"📏 API Key length: {len(api_key)} characters")
    print(f"🔑 API Key starts with: {api_key[:15]}...")
    print(f"🤖 Model: {settings.OPENAI_MODEL}")
    
    if len(api_key) < 20:
        print("❌ ERROR: API key seems too short")
        return False
    
    # Test API call
    print("\n📡 Testing API call...")
    try:
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": "Say 'API key is working!' if you can read this."
                }
            ],
            max_tokens=50
        )
        
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            print(f"✅ SUCCESS! API Response: {content}")
            print("\n" + "=" * 60)
            print("✅ Your API key is working correctly!")
            print("=" * 60)
            return True
        else:
            print("❌ ERROR: API returned no response")
            return False
            
    except openai.AuthenticationError as e:
        print("❌ AUTHENTICATION ERROR")
        print(f"Error: {e}")
        print("\nPossible issues:")
        print("1. API key is invalid or expired")
        print("2. API key doesn't have access to the requested model")
        print("3. Check if your API key has the correct format")
        return False
        
    except openai.APIError as e:
        print("❌ API ERROR")
        print(f"Error: {e}")
        print("\nPossible issues:")
        print("1. Rate limit exceeded")
        print("2. Server error")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {type(e).__name__}")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_api_key()
    sys.exit(0 if success else 1)

