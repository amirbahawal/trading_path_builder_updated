from typing import Optional
from database.connection import SessionLocal
from database.models import Entitlement
from core.config import settings
import logging

logger = logging.getLogger(__name__)


def grant_entitlement(user_id: str, plan_id: str, tier: str = "pro") -> bool:
    """
    Grant or update entitlement for a user and plan.
    
    Args:
        user_id: User ID
        plan_id: Plan ID
        tier: Tier level ("free" or "pro")
        
    Returns:
        True on success, False on error
    """
    db = SessionLocal()
    try:
        # Check if entitlement already exists
        existing = db.query(Entitlement).filter(
            Entitlement.user_id == user_id,
            Entitlement.plan_id == plan_id
        ).first()
        
        if existing:
            # Update existing entitlement
            existing.tier = tier
        else:
            # Create new entitlement
            entitlement = Entitlement(
                user_id=user_id,
                plan_id=plan_id,
                tier=tier
            )
            db.add(entitlement)
        
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error granting entitlement: {e}")
        return False
    finally:
        db.close()


def check_entitlement(user_id: Optional[str], plan_id: str) -> str:
    """
    Check user's entitlement tier for a plan.
    
    Args:
        user_id: User ID (can be None)
        plan_id: Plan ID
        
    Returns:
        Tier level: "free" or "pro"
    """
    if not user_id:
        return "free"
    
    db = SessionLocal()
    try:
        entitlement = db.query(Entitlement).filter(
            Entitlement.user_id == user_id,
            Entitlement.plan_id == plan_id
        ).first()
        
        if not entitlement:
            return "free"
        
        return entitlement.tier
        
    except Exception as e:
        logger.error(f"Error checking entitlement: {e}")
        return "free"
    finally:
        db.close()


def can_access_stage(user_id: Optional[str], plan_id: str, stage_id: int) -> bool:
    """
    Check if user can access a specific stage.
    
    Args:
        user_id: User ID
        plan_id: Plan ID
        stage_id: Stage number
        
    Returns:
        True if stage is accessible, False if locked
    """
    # Free stage is always accessible
    if stage_id == settings.FREE_STAGE_ID:
        return True
    
    # Check entitlement for other stages
    tier = check_entitlement(user_id, plan_id)
    return tier == "pro"