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
        
        # Use provided plan_id if it exists, otherwise generate new one
        plan_id_value = plan_data.get("plan_id")
        plan_uuid = None
        
        if plan_id_value:
            # Handle plan_id - convert to UUID if it's a string, or use as-is if already UUID
            if isinstance(plan_id_value, uuid.UUID):
                # Already a UUID object - use it directly
                plan_uuid = plan_id_value
            elif isinstance(plan_id_value, str):
                # String - try to convert to UUID
                clean_plan_id = plan_id_value
                # Remove "plan-" prefix if present
                if clean_plan_id.startswith("plan-"):
                    clean_plan_id = clean_plan_id[5:]
                
                try:
                    plan_uuid = uuid.UUID(clean_plan_id)
                except ValueError:
                    # Invalid UUID format in string - generate new one
                    logger.warning(f"Invalid UUID format in plan_id: {plan_id_value}, generating new UUID")
                    plan_uuid = uuid.uuid4()
            else:
                # Invalid type - generate new UUID
                logger.warning(f"Invalid plan_id type: {type(plan_id_value)}, generating new UUID")
                plan_uuid = uuid.uuid4()
            
            # Check if plan already exists
            existing_plan = db.query(Plan).filter(Plan.id == plan_uuid).first()
            if existing_plan:
                # Plan exists - update it instead of creating new one
                existing_plan.answers_json = plan_data.get("answers_json", existing_plan.answers_json)
                existing_plan.answers_fingerprint = plan_data.get("answers_fingerprint", existing_plan.answers_fingerprint)
                existing_plan.template_version = plan_data.get("template_version", existing_plan.template_version)
                existing_plan.persona_label = plan_data.get("persona_label", existing_plan.persona_label)
                existing_plan.overview_md = plan_data.get("overview_md", existing_plan.overview_md)
                db.commit()
                db.refresh(existing_plan)
                plan = existing_plan
                plan_id = str(plan.id)
            else:
                # Plan doesn't exist - create with specified UUID
                plan = Plan(
                    id=plan_uuid,
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
        else:
            # No plan_id provided - generate new one
            plan_uuid = uuid.uuid4()
            plan = Plan(
                id=plan_uuid,
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
        # Return plan_id in consistent format (with "plan-" prefix)
        # plan_id is already a string from str(plan.id), so add prefix if needed
        if plan_id and not plan_id.startswith("plan-"):
            return f"plan-{plan_id}"
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
        # Clean plan_id: remove "plan-" prefix if present
        clean_plan_id = plan_id
        if isinstance(plan_id, str) and plan_id.startswith("plan-"):
            clean_plan_id = plan_id[5:]  # Remove "plan-" prefix
            logger.debug(f"Removed 'plan-' prefix from plan_id: {plan_id} -> {clean_plan_id}")
        
        # Try to convert plan_id to UUID
        plan_uuid = None
        try:
            plan_uuid = uuid.UUID(clean_plan_id) if isinstance(clean_plan_id, str) else clean_plan_id
        except (ValueError, AttributeError):
            # If plan_id is not a valid UUID, try to find by partial match or text search
            # Only log at debug level - invalid plan IDs are expected (user might have old/invalid ID)
            logger.debug(f"Invalid UUID format for plan_id: {plan_id}, trying text search")
            
            # Skip search if plan_id is too short (likely invalid)
            if len(clean_plan_id) < 8:
                logger.debug(f"Plan ID too short ({len(clean_plan_id)} chars), skipping search: {clean_plan_id}")
                return None
            
            # Remove dashes and try to find matching plan
            clean_id_no_dashes = clean_plan_id.replace("-", "")
            # Try to find plan where ID contains this substring
            # SQLite stores UUIDs as TEXT, so we can search directly
            from sqlalchemy import text
            try:
                # SQLite-compatible query - search in text fields
                result = db.execute(text("""
                    SELECT id FROM plans 
                    WHERE id LIKE :pattern 
                    OR id LIKE :pattern_no_dash
                    LIMIT 1
                """), {
                    "pattern": f"%{clean_plan_id}%",
                    "pattern_no_dash": f"%{clean_id_no_dashes}%"
                }).first()
                
                if result:
                    # Found a matching plan, convert the result to UUID
                    found_id = result[0]
                    if isinstance(found_id, str):
                        try:
                            plan_uuid = uuid.UUID(found_id)
                        except ValueError:
                            # If still not a UUID, use the string directly for query
                            plan = db.query(Plan).filter(Plan.id == found_id).first()
                            if plan:
                                # Convert plan.id to string for consistency
                                plan_uuid = plan.id
                    else:
                        plan_uuid = found_id
                else:
                    # No plan found - this is expected for invalid plan IDs
                    logger.debug(f"No plan found matching pattern: {clean_plan_id}")
                    return None
            except Exception as search_error:
                # Log at debug level - search errors are expected for invalid IDs
                logger.debug(f"Error searching for plan by text: {search_error}")
                return None
        
        # Query plan by UUID
        if plan_uuid:
            plan = db.query(Plan).filter(Plan.id == plan_uuid).first()
        else:
            # Fallback: try direct string match
            plan = db.query(Plan).filter(Plan.id == clean_plan_id).first()
        
        if not plan:
            # Log at debug level - plan not found is a valid 404 response
            logger.debug(f"Plan not found in database: {plan_id}")
            return None
        
        # Get stages for this plan
        stages = db.query(Stage).filter(Stage.plan_id == plan.id).order_by(Stage.stage_number).all()
        
        # Build stages list - ensure we have all 3 stages
        stages_list = []
        stages_dict = {stage.stage_number: stage for stage in stages}
        
        # Always return all 3 stages (create placeholders if missing)
        for stage_num in [1, 2, 3]:
            if stage_num in stages_dict:
                stage = stages_dict[stage_num]
                stages_list.append({
                    "stage_number": stage.stage_number,
                    "title": stage.title,
                    "is_free": stage.is_free,
                    "content_md": stage.content_md
                })
            else:
                # Create placeholder for missing stage
                logger.warning(f"Stage {stage_num} not found for plan {plan.id}, creating placeholder")
                stages_list.append({
                    "stage_number": stage_num,
                    "title": f"Stage {stage_num}",
                    "is_free": (stage_num == 1),
                    "content_md": ""
                })
        
        return {
            "plan_id": str(plan.id),
            "user_id": str(plan.user_id) if plan.user_id else None,
            "answers_json": plan.answers_json,
            "answers_fingerprint": plan.answers_fingerprint,
            "template_version": plan.template_version,
            "persona_label": plan.persona_label,
            "overview_md": plan.overview_md,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "stages": stages_list
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