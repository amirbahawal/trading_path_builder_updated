import pytest
from fastapi.testclient import TestClient
from main import app
from database.connection import SessionLocal, init_db
from database.models import VerificationCode, Entitlement
from datetime import datetime, timedelta
import uuid

client = TestClient(app)

EMAIL = "testuser@example.com"
PLAN_ID = str(uuid.uuid4())


def setup_module(module):
    # Reset/clean tables for repeatable tests
    db = SessionLocal()
    db.query(VerificationCode).delete()
    db.query(Entitlement).delete()
    db.commit()
    db.close()


def get_code_for_email(email, code_type):
    db = SessionLocal()
    row = db.query(VerificationCode).filter_by(email=email, code_type=code_type).first()
    code = row.code if row else None
    db.close()
    return code


def test_login_code_flow_happy():
    # Send login code
    r = client.post("/auth/send-login-code", json={"email": EMAIL})
    assert r.status_code == 200
    # Get code from DB directly (mocking send)
    code = get_code_for_email(EMAIL, "login")
    assert code and code.isdigit()
    # Verify code
    r2 = client.post("/auth/verify-login-code", json={"email": EMAIL, "code": code})
    assert r2.status_code == 200
    assert r2.json()["success"] is True
    assert "session_token" in r2.json()


def test_login_code_wrong_code():
    # Send code
    r = client.post("/auth/send-login-code", json={"email": EMAIL})
    assert r.status_code == 200
    # Try wrong code
    r2 = client.post("/auth/verify-login-code", json={"email": EMAIL, "code": "999999"})
    assert r2.status_code == 400
    assert r2.json()["detail"].lower().find("invalid") >= 0


def test_login_code_expired():
    # Send code
    r = client.post("/auth/send-login-code", json={"email": EMAIL})
    code = get_code_for_email(EMAIL, "login")
    db = SessionLocal()
    row = db.query(VerificationCode).filter_by(email=EMAIL, code_type="login").first()
    # Backdate expiry
    row.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()
    db.close()
    # Try expired code
    r2 = client.post("/auth/verify-login-code", json={"email": EMAIL, "code": code})
    assert r2.status_code == 400
    assert "expired" in r2.json()["detail"].lower()


def test_login_code_brute_force_rate_limit():
    for i in range(5):
        r = client.post("/auth/send-login-code", json={"email": EMAIL})
        assert r.status_code == 200
    # 6th request should fail (rate limit)
    r = client.post("/auth/send-login-code", json={"email": EMAIL})
    assert r.status_code == 429
    assert "rate" in r.json()["detail"].lower()


def test_unlock_flow_and_entitlement():
    # Send unlock code
    r = client.post("/auth/unlock-plan", json={"email": EMAIL})
    assert r.status_code == 200
    code = get_code_for_email(EMAIL, "unlock")
    # Complete unlock (positive)
    unlock_payload = {"email": EMAIL, "code": code, "plan_id": PLAN_ID}
    r2 = client.post("/auth/complete-unlock", json=unlock_payload)
    assert r2.status_code == 200
    assert r2.json()["plan_unlocked"] is True
    # Confirm entitlement in DB
    db = SessionLocal()
    ent = db.query(Entitlement).filter_by(user_id=r2.json()["user_id"], plan_id=PLAN_ID).first()
    db.close()
    assert ent and ent.tier == "pro"


def test_unlock_wrong_code():
    # Send unlock code
    r = client.post("/auth/unlock-plan", json={"email": EMAIL})
    assert r.status_code == 200
    bad_payload = {"email": EMAIL, "code": "333333", "plan_id": PLAN_ID}
    r2 = client.post("/auth/complete-unlock", json=bad_payload)
    assert r2.status_code == 400
    assert "invalid" in r2.json()["detail"].lower()


def test_unlock_rate_limit():
    for i in range(5):
        r = client.post("/auth/unlock-plan", json={"email": EMAIL})
        assert r.status_code == 200
    # 6th request should fail (rate limit)
    r = client.post("/auth/unlock-plan", json={"email": EMAIL})
    assert r.status_code == 429
    assert "rate" in r.json()["detail"].lower()
