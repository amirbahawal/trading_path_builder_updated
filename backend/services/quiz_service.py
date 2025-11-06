# backend/services/quiz_service.py
import json
import os
from typing import List, Dict

DEFAULT_QUESTIONS = [
    {"id":"experience","label":"What is your current trading experience?","options":["Beginner","Intermediate","Advanced"]},
    {"id":"goal","label":"What is your main goal in trading?","options":["Consistency","High returns","Learning technical skills"]},
    {"id":"style","label":"Which trading style do you prefer?","options":["Scalping","Swing Trading","Long-term Investing"]},
    {"id":"risk","label":"How do you describe your risk appetite?","options":["Low","Moderate","High"]},
    {"id":"time","label":"How much time can you dedicate daily to trading?","options":["<1 hour","1–3 hours","Full-time"]},
]

def load_quiz_questions() -> List[Dict]:
    try:
        quiz_file = "./data/quiz_questions.json"
        if os.path.exists(quiz_file):
            with open(quiz_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return DEFAULT_QUESTIONS
