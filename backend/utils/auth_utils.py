"""
Lightweight authentication helpers for mock login or magic link flow.
Replace this with real auth for production.
"""

import os
import hmac
import hashlib
import base64
import time
from typing import Optional

try:
    import jwt  # PyJWT provided via requirements.txt
    from jwt import PyJWTError, ExpiredSignatureError
except ImportError as exc:  # pragma: no cover - development safety net
    raise RuntimeError(
        "PyJWT is required but not installed. Please run 'pip install pyjwt' inside the backend venv."
    ) from exc

from fastapi import Depends, Header, HTTPException
from core.config import settings

SECRET_KEY = os.environ.get("APP_AUTH_SECRET", "dev-secret-change-me")
TOKEN_TTL_SECONDS = 60 * 60 * 24  # 24 hours


def _sign_message(message: bytes) -> str:
    sig = hmac.new(SECRET_KEY.encode("utf-8"), message, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode("utf-8")


def _verify_message_signature(message: bytes, signature: str) -> bool:
    expected = _sign_message(message)
    return hmac.compare_digest(expected, signature)


def generate_magic_link_token(email: str, ttl: int = TOKEN_TTL_SECONDS) -> str:
    """Generate signed token: base64(email|expiry|sig)."""
    expiry = int(time.time()) + ttl
    payload = f"{email}|{expiry}".encode("utf-8")
    sig = _sign_message(payload)
    raw = b"|".join([email.encode("utf-8"), str(expiry).encode("utf-8"), sig.encode("utf-8")])
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def validate_magic_link_token(token: str) -> Optional[str]:
    """Return email if token valid & not expired, else None."""
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8"))
        email, expiry, sig = raw.split(b"|")
        message = b"|".join([email, expiry])
        if not _verify_message_signature(message, sig.decode("utf-8")):
            return None
        if int(time.time()) > int(expiry.decode("utf-8")):
            return None
        return email.decode("utf-8")
    except Exception:
        return None


def get_user_from_token(token: str) -> Optional[dict]:
    """Resolve token → user dict (stub for demo)."""
    email = validate_magic_link_token(token)
    if email is None:
        return None
    return {"id": f"user:{email}", "email": email}


def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no user_id")
        return {"user_id": user_id}
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(authorization: str = Header(...)):
    """FastAPI dependency for requiring JWT. Returns `{"user_id": ...}`."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.replace("Bearer ", "", 1).strip()
    return verify_jwt_token(token)


def get_current_user_optional(authorization: Optional[str] = Header(None)):
    """FastAPI dependency for optional JWT. Returns `{"user_id": ...}` or `{"user_id": "anon"}`."""
    if not authorization or not authorization.startswith("Bearer "):
        return {"user_id": "anon"}
    token = authorization.replace("Bearer ", "", 1).strip()
    try:
        return verify_jwt_token(token)
    except HTTPException:
        # If token is invalid, allow anonymous access
        return {"user_id": "anon"}