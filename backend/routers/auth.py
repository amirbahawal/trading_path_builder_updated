from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from core.db_helpers import create_user_if_not_exists
from services.entitlement_service import grant_entitlement
from routers.analytics import emit_event, AnalyticsEvents
from services.email_service import send_otp_email, test_email_configuration
import logging
logger = logging.getLogger(__name__)

# Use regular str instead of EmailStr to avoid dependency issues
EmailStr = str

# Optional imports for database functionality
SQLALCHEMY_AVAILABLE = False
try:
    from sqlalchemy.orm import Session  # type: ignore
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    # Mock Session for development
    class Session:
        def query(self, model):
            return MockQuery()
        def add(self, obj):
            pass
        def commit(self):
            pass
        def refresh(self, obj):
            pass
        def delete(self, obj):
            pass
        def join(self, model):
            return MockQuery()
        def filter(self, *args):
            return MockQuery()
        def first(self):
            return None

class MockQuery:
    def join(self, model):
        return self
    def filter(self, *args):
        return self
    def first(self):
        return None

from database.connection import get_db
from database.models import User, AuthToken
from database.models import VerificationCode
import secrets
from datetime import datetime, timedelta
import uuid
import os

# Optional imports for email functionality
SENDGRID_AVAILABLE = False
try:
    import sendgrid  # type: ignore
    from sendgrid import SendGridAPIClient  # type: ignore
    from sendgrid.helpers.mail import Mail  # type: ignore
    SENDGRID_AVAILABLE = True
except ImportError:
    # Mock classes for development
    class SendGridAPIClient:
        def __init__(self, api_key):
            pass
        def send(self, message):
            pass
    
    class Mail:
        def __init__(self, from_email, to_emails, subject, html_content):
            self.from_email = from_email
            self.to_emails = to_emails
            self.subject = subject
            self.html_content = html_content

# Optional imports for JWT functionality
JWT_AVAILABLE = False
try:
    import jwt  # type: ignore
    JWT_AVAILABLE = True
except ImportError:
    # Mock jwt for development
    class jwt:
        @staticmethod
        def encode(payload, secret, algorithm):
            return f"mock_jwt_{payload.get('user_id', 'unknown')}_{payload.get('exp', 0)}"

from services.utils import can_rate_limit, log_rate_event

router = APIRouter(tags=["Auth"])

class AuthRequest(BaseModel):
    email: EmailStr

class VerifyRequest(BaseModel):
    email: EmailStr
    token: str

class EmailVerificationRequest(BaseModel):
    email: EmailStr

class CodeVerificationRequest(BaseModel):
    email: EmailStr
    code: str

class UnlockRequest(BaseModel):
    email: EmailStr
    code: str
    plan_id: str  # Add plan_id to request

class LoginResponse(BaseModel):
    success: bool
    message: str
    session_token: Optional[str] = None
    user_id: Optional[str] = None

def send_magic_link(email: str, token: str):
    if not SENDGRID_AVAILABLE:
        print(f"Mock email sent to {email} with token: {token}")
        return
    
    try:
        sg = SendGridAPIClient(os.getenv("EMAIL_SERVICE_API_KEY"))
        message = Mail(
            from_email="no-reply@tradingpath.com",
            to_emails=email,
            subject="Your Trading Path Builder Magic Link",
            html_content=f"Click to sign in: <a href='{os.getenv('FRONTEND_URL')}/auth?token={token}'>Login</a>. Expires in 15 minutes."
        )
        sg.send(message)
    except Exception as e:
        print(f"Failed to send email: {e}")
        print(f"Mock email sent to {email} with token: {token}")

def generate_jwt(user_id: str) -> str:
    if not JWT_AVAILABLE:
        # Return a mock token for development
        return f"mock_jwt_{user_id}_{datetime.utcnow().timestamp()}"
    
    payload = {"user_id": str(user_id), "exp": datetime.utcnow() + timedelta(hours=24)}
    return jwt.encode(payload, os.getenv("JWT_SECRET", "dev_secret"), algorithm="HS256")

@router.post("/magic-link")
async def send_magic_link_endpoint(auth: AuthRequest, db: Session = Depends(get_db)):
    if not SQLALCHEMY_AVAILABLE:
        # Mock response for development
        token = str(uuid.uuid4())
        send_magic_link(auth.email, token)
        return {"message": "Magic link sent (mock mode)"}
    
    user = db.query(User).filter(User.email == auth.email).first()
    if not user:
        user = User(email=auth.email)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    token = str(uuid.uuid4())
    auth_token = AuthToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )
    db.add(auth_token)
    db.commit()
    
    send_magic_link(auth.email, token)
    return {"message": "Magic link sent"}

@router.post("/verify")
async def verify_magic_link(verify: VerifyRequest, db: Session = Depends(get_db)):
    if not SQLALCHEMY_AVAILABLE:
        # Mock response for development
        session_token = generate_jwt("mock_user_id")
        return {"session_token": session_token, "user_id": "mock_user_id"}
    
    auth_token = db.query(AuthToken).join(User).filter(
        User.email == verify.email,
        AuthToken.token == verify.token,
        AuthToken.expires_at > datetime.utcnow()
    ).first()
    
    if not auth_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    db.delete(auth_token)  # One-time use
    db.commit()
    
    session_token = generate_jwt(str(auth_token.user_id))
    return {"session_token": session_token, "user_id": str(auth_token.user_id)}

@router.post("/send-login-code", response_model=LoginResponse)
async def send_login_code(request: EmailVerificationRequest, db: Session = Depends(get_db), http_req: Request = None):
    ip = http_req.client.host if http_req and http_req.client else None
    if not can_rate_limit(db, ip, request.email, "/send-login-code", "send", 3600, 5):
        log_rate_event(db, ip, request.email, "/send-login-code", "blocked")
        logger.warning(f"[AUDIT] Rate-limit block (login code) | email={request.email} ip={ip}")
        raise HTTPException(status_code=429, detail="Too many login code requests, please try again later.")
    log_rate_event(db, ip, request.email, "/send-login-code", "send")
    logger.info(f"[AUDIT] Login code sent | email={request.email} ip={ip}")
    """Send one-time login code to email, securely stored in DB with 10-min expiry"""
    try:
        # Generate a cryptographically strong 6-digit code
        verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        # Clean up any previous unexpired login codes for this email
        db.query(VerificationCode).filter(
            VerificationCode.email == request.email,
            VerificationCode.code_type == 'login',
            VerificationCode.expires_at > datetime.utcnow()
        ).delete()
        # Store the code in DB
        code_entry = VerificationCode(
            id=str(uuid.uuid4()),
            email=request.email,
            code=verification_code,
            code_type='login',
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        db.add(code_entry)
        db.commit()
        
        # Send OTP via Gmail SMTP
        email_sent = send_otp_email(request.email, verification_code, purpose="login")
        if not email_sent:
            logger.error(f"[ERROR] Failed to send OTP email to {request.email}")
            raise HTTPException(status_code=500, detail="Failed to send OTP email. Please check server logs.")
        
        return LoginResponse(
            success=True,
            message="Login code sent to your email",
            session_token=None,
            user_id=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send login code: {str(e)}")

@router.post("/verify-login-code", response_model=LoginResponse)
async def verify_login_code(request: CodeVerificationRequest, db: Session = Depends(get_db), http_req: Request = None):
    ip = http_req.client.host if http_req and http_req.client else None
    if not can_rate_limit(db, ip, request.email, "/verify-login-code", "verify", 3600, 5):
        log_rate_event(db, ip, request.email, "/verify-login-code", "blocked")
        logger.warning(f"[AUDIT] Rate-limit block (login code) | email={request.email} ip={ip}")
        raise HTTPException(status_code=429, detail="Too many login attempts, please try again later.")
    log_rate_event(db, ip, request.email, "/verify-login-code", "verify")
    logger.info(f"[AUDIT] Login code verified | email={request.email} ip={ip}")
    """Verify the login code and sign in user (persistent, secure)"""
    try:
        # Look for valid, unexpired code
        code_row = db.query(VerificationCode).filter(
            VerificationCode.email == request.email,
            VerificationCode.code == request.code,
            VerificationCode.code_type == 'login',
            VerificationCode.expires_at > datetime.utcnow()
        ).first()
        if code_row is not None:
            # Single-use: delete immediately
            db.delete(code_row)
            db.commit()
            # Clean up all expired codes (optional best-effort cleanup)
            db.query(VerificationCode).filter(
                VerificationCode.expires_at < datetime.utcnow()
            ).delete()
            db.commit()
            # Create or get user
            user_id = create_user_if_not_exists(request.email)
            # Generate session token
            session_token = generate_jwt(user_id)
            return LoginResponse(
                success=True,
                message="Welcome! You are now signed in.",
                session_token=session_token,
                user_id=user_id
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid or expired login code")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Login failed: {str(e)}")

@router.get("/check-login")
async def check_login_status():
    """Check if user is logged in"""
    # This would check the session token in production
    return {
        "logged_in": False,
        "message": "Not logged in"
    }

@router.get("/test-email-config")
async def test_email_config():
    """Test email configuration - useful for debugging"""
    return test_email_configuration()

@router.post("/unlock-plan")
async def unlock_plan(request: EmailVerificationRequest, db: Session = Depends(get_db), http_req: Request = None):
    ip = http_req.client.host if http_req and http_req.client else None
    if not can_rate_limit(db, ip, request.email, "/unlock-plan", "send", 3600, 5):
        log_rate_event(db, ip, request.email, "/unlock-plan", "blocked")
        logger.warning(f"[AUDIT] Rate-limit block (unlock code) | email={request.email} ip={ip}")
        raise HTTPException(status_code=429, detail="Too many unlock code requests, please try again later.")
    log_rate_event(db, ip, request.email, "/unlock-plan", "send")
    logger.info(f"[AUDIT] Unlock code sent | email={request.email} ip={ip}")
    """Unlock the $5 plan - requires email verification. Send unlock code securely stored in DB."""
    try:
        # Generate secure unlock code
        unlock_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        # Clean up any previous unexpired unlock codes for this email
        db.query(VerificationCode).filter(
            VerificationCode.email == request.email,
            VerificationCode.code_type == 'unlock',
            VerificationCode.expires_at > datetime.utcnow()
        ).delete()
        # Store code in DB
        code_entry = VerificationCode(
            id=str(uuid.uuid4()),
            email=request.email,
            code=unlock_code,
            code_type='unlock',
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        db.add(code_entry)
        db.commit()
        
        # Send OTP via Gmail SMTP
        email_sent = send_otp_email(request.email, unlock_code, purpose="unlock")
        if not email_sent:
            logger.error(f"[ERROR] Failed to send unlock OTP email to {request.email}")
            raise HTTPException(status_code=500, detail="Failed to send unlock OTP email. Please check server logs.")
        
        return {
            "success": True,
            "message": "Unlock code sent to your email",
            "requires_verification": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send unlock code: {str(e)}")

@router.post("/complete-unlock")
async def complete_unlock(request: UnlockRequest, db: Session = Depends(get_db), http_req: Request = None):
    ip = http_req.client.host if http_req and http_req.client else None
    if not can_rate_limit(db, ip, request.email, "/complete-unlock", "verify", 3600, 5):
        log_rate_event(db, ip, request.email, "/complete-unlock", "blocked")
        logger.warning(f"[AUDIT] Rate-limit block (unlock code) | email={request.email} ip={ip}")
        raise HTTPException(status_code=429, detail="Too many unlock attempts, please try again later.")
    log_rate_event(db, ip, request.email, "/complete-unlock", "verify")
    logger.info(f"[AUDIT] Unlock code verified and entitlement granted | email={request.email} ip={ip} plan_id={request.plan_id}")
    """Complete the plan unlock after code verification and grant entitlement, secure persistent code verification."""
    try:
        # Look for valid, unexpired unlock code
        code_row = db.query(VerificationCode).filter(
            VerificationCode.email == request.email,
            VerificationCode.code == request.code,
            VerificationCode.code_type == 'unlock',
            VerificationCode.expires_at > datetime.utcnow()
        ).first()
        if code_row is not None:
            db.delete(code_row)
            db.commit()
            # Clean up all expired codes (optional best-effort cleanup)
            db.query(VerificationCode).filter(
                VerificationCode.expires_at < datetime.utcnow()
            ).delete()
            db.commit()
            # Create or get user
            user_id = create_user_if_not_exists(request.email)
            # Grant pro entitlement
            grant_entitlement(user_id, request.plan_id, "pro")
            
            # Emit analytics event for tier upgrade
            emit_event(AnalyticsEvents.TIER_UPGRADED_TO_PRO, user_id, request.plan_id)
            
            # Mock payment processing
            payment_id = f"payment_{uuid.uuid4().hex[:10]}"
            print(f"Processing $5 payment for {request.email}, plan: {request.plan_id}")
            return {
                "success": True,
                "message": "All stages unlocked! Your full trading path is ready.",
                "payment_id": payment_id,
                "plan_unlocked": True,
                "user_email": request.email,
                "user_id": user_id,
                "plan_id": request.plan_id,
                "tier": "pro"
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid or expired unlock code")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unlock failed: {str(e)}")