from pydantic import BaseModel, Field, field_validator

class QuizInput(BaseModel):
    experience: str = Field(..., min_length=1)
    years: str = Field(..., min_length=1)
    goal: str = Field(..., min_length=1)
    style: str = Field(..., min_length=1)
    time: str = Field(..., min_length=1)
    learning: str = Field(..., min_length=1)
    frustration: str = Field(..., min_length=1)
    risk: str = Field(..., min_length=1)
    tools: str = Field(..., min_length=1)
    focus: str = Field(..., min_length=1)

    @field_validator("experience", "years", "goal", "style", "time", "learning", "frustration", "risk", "tools", "focus", mode="before")
    def _strip_and_validate(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
        if not value:
            raise ValueError("value is required")
        return value

    class Config:
        extra = "forbid"
