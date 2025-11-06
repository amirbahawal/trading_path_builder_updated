"""
Debug endpoints for development only.
DO NOT USE IN PRODUCTION.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from database.connection import SessionLocal
from database.models import Plan, Stage, Entitlement
from services.entitlement_service import grant_entitlement
from core.db_helpers import get_plan_from_db
from core.config import settings

router = APIRouter()


@router.get("/plan/{plan_id}")
async def get_debug_plan(plan_id: str):
    """Get full plan data including fingerprint and all stages"""
    db = SessionLocal()
    try:
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        stages = db.query(Stage).filter(Stage.plan_id == plan.id).order_by(Stage.stage_number).all()
        
        return {
            "plan_id": str(plan.id),
            "user_id": str(plan.user_id) if plan.user_id else None,
            "fingerprint": plan.answers_fingerprint,
            "template_version": plan.template_version,
            "persona": plan.persona_label,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "stages": [
                {
                    "stage_number": s.stage_number,
                    "title": s.title,
                    "is_free": s.is_free,
                    "content_length": len(s.content_md)
                }
                for s in stages
            ]
        }
    finally:
        db.close()


@router.post("/grant-pro")
async def debug_grant_pro(plan_id: str, user_id: str):
    """Grant pro tier immediately for testing"""
    try:
        result = grant_entitlement(user_id, plan_id, "pro")
        return {
            "success": result,
            "message": f"Pro tier granted to user {user_id} for plan {plan_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entitlements")
async def get_all_entitlements():
    """List all entitlements in database"""
    db = SessionLocal()
    try:
        entitlements = db.query(Entitlement).all()
        return {
            "count": len(entitlements),
            "entitlements": [
                {
                    "id": str(e.id),
                    "user_id": str(e.user_id),
                    "plan_id": str(e.plan_id),
                    "tier": e.tier,
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in entitlements
            ]
        }
    finally:
        db.close()


@router.delete("/reset/{plan_id}")
async def debug_reset_plan(plan_id: str):
    """Delete plan and entitlements for testing"""
    db = SessionLocal()
    try:
        # Find plan
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Delete entitlements
        db.query(Entitlement).filter(Entitlement.plan_id == plan.id).delete()
        
        # Delete stages
        db.query(Stage).filter(Stage.plan_id == plan.id).delete()
        
        # Delete plan
        db.delete(plan)
        db.commit()
        
        return {"success": True, "message": f"Plan {plan_id} and all related data deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()