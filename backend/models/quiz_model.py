# backend/models/quiz_model.py
from pydantic import BaseModel
from typing import List, Dict, Any

class QuizQuestion(BaseModel):
    id: str
    label: str
    options: List[str]

class QuizResponse(BaseModel):
    questions: List[QuizQuestion]
