"""
SQLAlchemy connection and session utilities.
"""

import os

# Optional SQLAlchemy imports
SQLALCHEMY_AVAILABLE = False
try:
    from sqlalchemy import create_engine  # type: ignore
    from sqlalchemy.orm import sessionmaker, declarative_base  # type: ignore
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    # Mock classes for development
    class create_engine:
        def __init__(self, *args, **kwargs):
            pass
    
    class sessionmaker:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self):
            return MockSession()
    
    class MockMetaData:
        def create_all(self, bind=None):
            pass
    
    class MockBase:
        metadata = MockMetaData()
    
    def declarative_base():
        return MockBase
    
    class MockSession:
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
        def close(self):
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

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./dev.db")

# Create engine — use PostgreSQL or SQLite in mock mode
if SQLALCHEMY_AVAILABLE:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
        pool_pre_ping=True,
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    if not SQLALCHEMY_AVAILABLE:
        print("Database initialization skipped (SQLAlchemy not available)")
        return
    
    try:
        from .models import Base
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Database initialization failed: {e}")