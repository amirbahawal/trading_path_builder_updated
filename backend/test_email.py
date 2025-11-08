#!/usr/bin/env python3
"""
Test script to verify Gmail email configuration is working.
Run this to test if emails can be sent.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.email_service import send_otp_email
from core.config import settings

def test_email():
    """Test sending an email"""
    
    print("=" * 60)
    print("📧 Testing Email Configuration")
    print("=" * 60)
    
    # Check configuration
    print(f"📧 Gmail Address: {settings.GMAIL_ADDRESS or 'NOT SET'}")
    print(f"🔑 Gmail Password: {'SET' if settings.GMAIL_APP_PASSWORD else 'NOT SET'} (length: {len(settings.GMAIL_APP_PASSWORD) if settings.GMAIL_APP_PASSWORD else 0})")
    
    if not settings.GMAIL_ADDRESS or not settings.GMAIL_APP_PASSWORD:
        print("\n❌ ERROR: Gmail credentials not configured!")
        print("Please add GMAIL_ADDRESS and GMAIL_APP_PASSWORD to .env file")
        return False
    
    # Test email
    test_email_address = input("\nEnter your email address to receive test OTP: ").strip()
    if not test_email_address:
        print("❌ No email address provided")
        return False
    
    print(f"\n📤 Sending test email to {test_email_address}...")
    
    try:
        test_otp = "123456"  # Test code
        success = send_otp_email(test_email_address, test_otp, purpose="login")
        
        if success:
            print("✅ Email sent successfully!")
            print(f"📧 Check your inbox at {test_email_address}")
            print(f"🔑 Test OTP code: {test_otp}")
            print("\n" + "=" * 60)
            print("✅ Email service is working correctly!")
            print("=" * 60)
            return True
        else:
            print("❌ Failed to send email")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check Gmail App Password is correct")
        print("2. Verify 2-Step Verification is enabled")
        print("3. Check backend logs for detailed error")
        return False

if __name__ == "__main__":
    success = test_email()
    sys.exit(0 if success else 1)

