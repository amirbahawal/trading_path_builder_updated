# backend/models/user_model.py
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    email: str
    user_id: Optional[str] = None
