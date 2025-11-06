from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter()

# Define models
class QuizAnswer(BaseModel):
    question_id: str
    answer: str

class QuizSubmission(BaseModel):
    answers: List[QuizAnswer]

class QuizResponse(BaseModel):
    success: bool
    message: str
    quiz_id: Optional[str] = None

@router.post("/submit", response_model=QuizResponse)
async def submit_quiz(submission: QuizSubmission):
    """
    Handle quiz submission
    """
    try:
        # Your quiz processing logic here
        # For now, just return success
        return QuizResponse(
            success=True,
            message="Quiz submitted successfully",
            quiz_id="quiz_123"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/questions")
async def get_quiz_questions():
    """
    Get quiz questions
    """
    # Return mock questions for now
    return {
        "questions": [
            {
                "id": "experience",
                "text": "What is your current trading experience?",
                "options": ["Beginner", "Intermediate", "Advanced"]
            },
            {
                "id": "goal", 
                "text": "What is your main goal in trading?",
                "options": ["Consistency", "High returns", "Learning technical skills"]
            },
            {
                "id": "style",
                "text": "Which trading style do you prefer?",
                "options": ["Scalping", "Swing Trading", "Long-term Investing"]
            },
            {
                "id": "risk",
                "text": "How do you describe your risk appetite?",
                "options": ["Low", "Moderate", "High"]
            },
            {
                "id": "time",
                "text": "How much time can you dedicate daily to trading?",
                "options": ["<1 hour", "1–3 hours", "Full-time"]
            }
        ]
    }