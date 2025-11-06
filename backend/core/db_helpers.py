"""
Database helper functions for common operations.
"""
from typing import Optional, Dict, Any
from database.connection import SessionLocal
from database.models import Plan, Stage, User
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


def save_plan_to_db(plan_data: dict) -> str:
    """
    Save plan to database.
    
    Args:
        plan_data: Dictionary containing plan fields
        
    Returns:
        Plan ID as string
    """
    db = SessionLocal()
    try:
        # Convert user_id to UUID if it's a string
        user_id_value = plan_data.get("user_id")
        if user_id_value and isinstance(user_id_value, str):
            try:
                user_id_value = uuid.UUID(user_id_value)
            except ValueError:
                # If it's not a valid UUID string, leave it as None
                user_id_value = None
        
        # Create Plan record
        plan = Plan(
            id=uuid.uuid4(),
            user_id=user_id_value,
            answers_json=plan_data.get("answers_json", {}),
            answers_fingerprint=plan_data.get("answers_fingerprint", ""),
            template_version=plan_data.get("template_version", ""),
            persona_label=plan_data.get("persona_label"),
            overview_md=plan_data.get("overview_md", ""),
            created_at=datetime.utcnow()
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        
        plan_id = str(plan.id)
        
        # Create Stage records
        for stage_data in plan_data.get("stages", []):
            stage = Stage(
                id=uuid.uuid4(),
                plan_id=plan.id,
                stage_number=stage_data.get("stage_number"),
                title=stage_data.get("title", ""),
                is_free=stage_data.get("is_free", False),
                content_md=stage_data.get("content_md", "")
            )
            db.add(stage)
        
        db.commit()
        return plan_id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving plan to database: {e}")
        raise
    finally:
        db.close()


def get_plan_from_db(plan_id: str) -> Optional[dict]:
    """
    Get plan from database by ID.
    
    Args:
        plan_id: Plan ID
        
    Returns:
        Plan dictionary or None if not found
    """
    db = SessionLocal()
    try:
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            return None
        
        # Get stages for this plan
        stages = db.query(Stage).filter(Stage.plan_id == plan.id).order_by(Stage.stage_number).all()
        
        return {
            "plan_id": str(plan.id),
            "user_id": str(plan.user_id) if plan.user_id else None,
            "answers_json": plan.answers_json,
            "answers_fingerprint": plan.answers_fingerprint,
            "template_version": plan.template_version,
            "persona_label": plan.persona_label,
            "overview_md": plan.overview_md,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "stages": [
                {
                    "stage_number": stage.stage_number,
                    "title": stage.title,
                    "is_free": stage.is_free,
                    "content_md": stage.content_md
                }
                for stage in stages
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting plan from database: {e}")
        return None
    finally:
        db.close()


def get_cached_plan_by_fingerprint(fingerprint: str) -> Optional[dict]:
    """
    Get cached plan by fingerprint.
    
    Args:
        fingerprint: Answers fingerprint
        
    Returns:
        Plan dictionary or None if not found
    """
    db = SessionLocal()
    try:
        plan = db.query(Plan).filter(Plan.answers_fingerprint == fingerprint).first()
        if not plan:
            return None
        
        # Get stages for this plan
        stages = db.query(Stage).filter(Stage.plan_id == plan.id).order_by(Stage.stage_number).all()
        
        return {
            "plan_id": str(plan.id),
            "user_id": str(plan.user_id) if plan.user_id else None,
            "answers_json": plan.answers_json,
            "answers_fingerprint": plan.answers_fingerprint,
            "template_version": plan.template_version,
            "persona_label": plan.persona_label,
            "overview_md": plan.overview_md,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "stages": [
                {
                    "stage_number": stage.stage_number,
                    "title": stage.title,
                    "is_free": stage.is_free,
                    "content_md": stage.content_md
                }
                for stage in stages
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting cached plan: {e}")
        return None
    finally:
        db.close()


def create_user_if_not_exists(email: str) -> str:
    """
    Create user if not exists.
    
    Args:
        email: User email
        
    Returns:
        User ID as string
    """
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            return str(user.id)
        
        # Create new user
        new_user = User(
            id=uuid.uuid4(),
            email=email,
            created_at=datetime.utcnow()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return str(new_user.id)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise
    finally:
        db.close()