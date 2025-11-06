# Optional SQLAlchemy imports
try:
    from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, JSON, UUID  # type: ignore
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Mock classes for development
    class Column:
        def __init__(self, *args, **kwargs):
            pass
    
    class String:
        pass
    
    class DateTime:
        pass
    
    class ForeignKey:
        def __init__(self, *args, **kwargs):
            pass
    
    class Integer:
        pass
    
    class Boolean:
        pass
    
    class JSON:
        pass
    
    class UUID:
        def __init__(self, *args, **kwargs):
            pass

from datetime import datetime
import uuid
from .connection import Base

# Mock model classes when SQLAlchemy is not available
if not SQLALCHEMY_AVAILABLE:
    class User:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class Plan:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class Stage:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class Entitlement:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class AuthToken:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class VerificationCode:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class RateLimitEvent:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
else:
    class User(Base):
        __tablename__ = "users"
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        email = Column(String, unique=True, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)

    class Plan(Base):
        __tablename__ = "plans"
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
        answers_json = Column(JSON, nullable=False)
        answers_fingerprint = Column(String, nullable=False)
        template_version = Column(String, nullable=False)
        persona_label = Column(String)
        overview_md = Column(String)
        created_at = Column(DateTime, default=datetime.utcnow)

    class Stage(Base):
        __tablename__ = "stages"
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
        stage_number = Column(Integer, nullable=False)
        title = Column(String, nullable=False)
        is_free = Column(Boolean, nullable=False)
        content_md = Column(String, nullable=False)

    class Entitlement(Base):
        __tablename__ = "entitlements"
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
        user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
        tier = Column(String, nullable=False)  # 'free' or 'pro'
        created_at = Column(DateTime, default=datetime.utcnow)

    class AuthToken(Base):
        __tablename__ = "auth_tokens"
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
        token = Column(String, nullable=False)
        expires_at = Column(DateTime, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)

    class VerificationCode(Base):
        __tablename__ = "verification_codes"
        id = Column(String, primary_key=True)
        email = Column(String, nullable=False)
        code = Column(String, nullable=False)
        code_type = Column(String, nullable=False)  # 'login' or 'unlock'
        expires_at = Column(DateTime, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)

    class RateLimitEvent(Base):
        __tablename__ = "rate_limits"
        id = Column(String, primary_key=True)
        email = Column(String, nullable=True)
        ip = Column(String, nullable=True)
        endpoint = Column(String, nullable=False)
        event_type = Column(String, nullable=False)
        timestamp = Column(DateTime, default=datetime.utcnow)