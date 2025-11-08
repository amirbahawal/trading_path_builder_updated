"""
Email Service - Sends OTP codes via Gmail SMTP
Free service, no paid API required
"""

import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

# Gmail configuration - lazy loaded to avoid circular imports
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def _get_gmail_credentials():
    """Lazy load Gmail credentials from settings"""
    from core.config import settings
    return settings.GMAIL_ADDRESS, settings.GMAIL_APP_PASSWORD

def _get_frontend_url():
    """Lazy load frontend URL from settings"""
    from core.config import settings
    return settings.FRONTEND_URL


def send_otp_email(email: str, otp_code: str, purpose: str = "login") -> bool:
    """
    Send OTP code via Gmail SMTP
    
    Args:
        email: Recipient email address
        otp_code: 6-digit OTP code
        purpose: 'login' or 'unlock' - determines email template
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    # Get credentials
    GMAIL_ADDRESS, GMAIL_APP_PASSWORD = _get_gmail_credentials()
    
    # If no Gmail configured, just log it (development mode)
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logger.warning(f"Gmail not configured. Mock email sent to {email} with OTP: {otp_code}")
        print(f"[MOCK EMAIL] To: {email} | OTP: {otp_code} | Purpose: {purpose}")
        return True
    
    try:
        # Email templates
        if purpose == "login":
            subject = "Your Trading Path Login Code"
            heading = "Welcome to Trading Path Builder"
            message_text = "Use this code to sign in:"
            footer_text = "This code expires in 10 minutes."
        elif purpose == "unlock":
            subject = "Unlock Your Trading Path - Complete Purchase"
            heading = "Unlock All Stages"
            message_text = "Use this code to complete your $5 plan purchase:"
            footer_text = "This code expires in 10 minutes. Complete your purchase to unlock all stages."
        else:
            subject = "Your Verification Code"
            heading = "Verification Required"
            message_text = "Use this code to verify your email:"
            footer_text = "This code expires in 10 minutes."
        
        # Create HTML email
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    h2 {{ color: #333; font-size: 24px; margin-bottom: 20px; }}
                    .otp-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; margin: 30px 0; border-radius: 8px; }}
                    .otp-code {{ color: white; font-size: 48px; font-weight: bold; letter-spacing: 8px; margin: 0; font-family: 'Courier New', monospace; }}
                    .otp-label {{ color: rgba(255,255,255,0.9); font-size: 14px; margin-top: 10px; }}
                    p {{ color: #666; font-size: 16px; line-height: 1.6; margin: 15px 0; }}
                    .footer {{ color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
                    .security-note {{ background-color: #f0f8ff; padding: 12px; border-left: 4px solid #667eea; margin-top: 20px; font-size: 13px; color: #333; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>{heading}</h2>
                    <p>{message_text}</p>
                    
                    <div class="otp-box">
                        <div class="otp-code">{otp_code}</div>
                        <div class="otp-label">One-Time Password</div>
                    </div>
                    
                    <p><strong>{footer_text}</strong></p>
                    
                    <div class="security-note">
                        <strong>🔒 Security Note:</strong> Never share this code with anyone. We will never ask for it via email.
                    </div>
                    
                    <div class="footer">
                        <p>If you didn't request this code, please ignore this email or contact our support team.</p>
                        <p style="margin-top: 20px; color: #aaa;">Trading Path Builder - Sent at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Create MIME message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = email
        
        # Add plain text version (fallback)
        text_content = f"""
Trading Path Builder - {heading}

{message_text}

OTP CODE: {otp_code}

{footer_text}

Security: Never share this code with anyone.

---
Sent: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """
        
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        # Send via Gmail SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure connection
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"[EMAIL] OTP sent successfully | to={email} | purpose={purpose}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail authentication failed. Check GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env")
        print(f"[ERROR] Gmail authentication failed. OTP: {otp_code}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending OTP to {email}: {e}")
        print(f"[ERROR] Failed to send email: {e}. OTP: {otp_code}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending OTP to {email}: {e}")
        print(f"[ERROR] Unexpected error: {e}. OTP: {otp_code}")
        return False


def test_email_configuration() -> dict:
    """Test email configuration and return status"""
    # Get credentials
    GMAIL_ADDRESS, GMAIL_APP_PASSWORD = _get_gmail_credentials()
    
    result = {
        "gmail_address_configured": bool(GMAIL_ADDRESS),
        "gmail_password_configured": bool(GMAIL_APP_PASSWORD),
        "gmail_address": GMAIL_ADDRESS[:3] + "***" if GMAIL_ADDRESS else "Not set",
        "password_length": len(GMAIL_APP_PASSWORD) if GMAIL_APP_PASSWORD else 0,
        "smtp_server": SMTP_SERVER,
        "smtp_port": SMTP_PORT
    }
    
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        result["status"] = "not_configured"
        result["message"] = "Gmail credentials not configured. Running in mock mode."
        return result
    
    try:
        # Try to connect and authenticate
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            result["status"] = "success"
            result["message"] = "Gmail SMTP connection successful!"
    except smtplib.SMTPAuthenticationError as e:
        result["status"] = "auth_failed"
        result["message"] = f"Gmail authentication failed: {str(e)}"
        result["error"] = "Invalid Gmail address or App Password"
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Connection failed: {str(e)}"
        result["error"] = str(e)
    
    return result


def send_welcome_email(email: str, user_name: str = "User") -> bool:
    """Send welcome email after successful signup"""
    # Get credentials
    GMAIL_ADDRESS, GMAIL_APP_PASSWORD = _get_gmail_credentials()
    
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logger.warning(f"Mock welcome email sent to {email}")
        print(f"[MOCK EMAIL] Welcome email to {email}")
        return True
    
    try:
        frontend_url = _get_frontend_url()
        subject = "Welcome to Trading Path Builder! 🚀"
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 40px; border-radius: 10px; }}
                    h1 {{ color: #667eea; }}
                    .button {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Welcome, {user_name}! 🎉</h1>
                    <p>Your Trading Path Builder account is ready.</p>
                    <p>Complete the quiz to get your personalized trading plan.</p>
                    <a href="{frontend_url}" class="button">Start Your Journey</a>
                    <p style="margin-top: 40px; color: #999; font-size: 12px;">Questions? Contact us at support@tradingpath.com</p>
                </div>
            </body>
        </html>
        """
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = email
        
        text_content = f"Welcome, {user_name}! Your Trading Path Builder account is ready. Visit {frontend_url} to start."
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"[EMAIL] Welcome email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {e}")
        return False
