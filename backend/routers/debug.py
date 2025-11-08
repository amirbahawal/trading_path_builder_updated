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


@router.get("/cache/list")
async def list_cached_plans():
    """List all cached plans with their fingerprints"""
    db = SessionLocal()
    try:
        plans = db.query(Plan).order_by(Plan.created_at.desc()).all()
        
        cached_plans = []
        for plan in plans:
            # Count stages for this plan
            stages_count = db.query(Stage).filter(Stage.plan_id == plan.id).count()
            
            # Get answers summary
            answers_json = plan.answers_json
            answers_summary = {}
            if isinstance(answers_json, dict):
                answers_summary = {
                    "experience": answers_json.get("experience", "N/A"),
                    "timeframe": answers_json.get("timeframe", "N/A"),
                    "riskTolerance": answers_json.get("riskTolerance", "N/A"),
                    "goal": answers_json.get("goal", "N/A")
                }
            
            cached_plans.append({
                "plan_id": str(plan.id),
                "user_id": str(plan.user_id) if plan.user_id else None,
                "fingerprint": plan.answers_fingerprint,
                "fingerprint_short": plan.answers_fingerprint[:16] + "..." if plan.answers_fingerprint else None,
                "template_version": plan.template_version,
                "persona": plan.persona_label,
                "stages_count": stages_count,
                "answers": answers_summary,
                "created_at": plan.created_at.isoformat() if plan.created_at else None
            })
        
        # Group by fingerprint to show cache hits
        fingerprint_counts = {}
        for plan in cached_plans:
            fp = plan["fingerprint"]
            if fp not in fingerprint_counts:
                fingerprint_counts[fp] = []
            fingerprint_counts[fp].append(plan["plan_id"])
        
        unique_fingerprints = len(fingerprint_counts)
        total_plans = len(cached_plans)
        
        return {
            "total_plans": total_plans,
            "unique_fingerprints": unique_fingerprints,
            "cache_efficiency": f"{(unique_fingerprints / total_plans * 100):.1f}%" if total_plans > 0 else "0%",
            "fingerprint_groups": {
                fp: {
                    "count": len(plan_ids),
                    "plan_ids": plan_ids
                }
                for fp, plan_ids in fingerprint_counts.items()
            },
            "cached_plans": cached_plans
        }
    finally:
        db.close()


@router.get("/cache/fingerprint/{fingerprint}")
async def get_plans_by_fingerprint(fingerprint: str):
    """Get all plans with a specific fingerprint (cache lookup test)"""
    db = SessionLocal()
    try:
        plans = db.query(Plan).filter(Plan.answers_fingerprint == fingerprint).all()
        
        if not plans:
            return {
                "found": False,
                "message": f"No plans found with fingerprint: {fingerprint[:16]}...",
                "fingerprint": fingerprint
            }
        
        result = {
            "found": True,
            "count": len(plans),
            "fingerprint": fingerprint,
            "fingerprint_short": fingerprint[:16] + "...",
            "plans": []
        }
        
        for plan in plans:
            stages = db.query(Stage).filter(Stage.plan_id == plan.id).order_by(Stage.stage_number).all()
            
            result["plans"].append({
                "plan_id": str(plan.id),
                "user_id": str(plan.user_id) if plan.user_id else None,
                "template_version": plan.template_version,
                "persona": plan.persona_label,
                "answers": plan.answers_json,
                "stages": [
                    {
                        "stage_number": s.stage_number,
                        "title": s.title,
                        "is_free": s.is_free,
                        "content_length": len(s.content_md)
                    }
                    for s in stages
                ],
                "created_at": plan.created_at.isoformat() if plan.created_at else None
            })
        
        return result
    finally:
        db.close()