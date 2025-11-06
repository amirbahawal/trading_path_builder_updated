# backend/models/plan_model.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Stage(BaseModel):
    id: int  # NEW: Stage number (1, 2, or 3)
    title: str
    is_free: bool  # NEW: True for stage 1, False for stages 2-3
    content: str
    locked: bool = True
    teaser: Optional[List[str]] = None

class PlanRequest(BaseModel):
    user_id: Optional[str] = "anon"
    answers: Dict[str, Any]

class PlanResponse(BaseModel):
    plan_id: str
    tier: str = "free"  # NEW: "free" or "pro"
    persona: Optional[Dict] = None  # NEW: {"label": "Pattern-Seeker"}
    overview_md: Optional[str] = None  # NEW: Stage 1 summary
    stages: List[Stage]

class SummaryRequest(BaseModel):
    answers: Dict[str, Any]

class SummaryResponse(BaseModel):
    plan_id: str
    summary: str  # Stage 1 content
    persona: Optional[Dict] = None
    cached: bool = False  # Indicates if this came from cache