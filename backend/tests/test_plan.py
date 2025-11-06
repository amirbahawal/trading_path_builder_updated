import pytest
from fastapi.testclient import TestClient
from ..main import app
from ..database.models import Plan, Stage, Entitlement, User
from sqlalchemy.orm import Session
import uuid

client = TestClient(app)

@pytest.fixture
def db_session(mocker):
    db = mocker.MagicMock(spec=Session)
    yield db

def test_create_plan_anonymous():
    quiz_data = {
        "experience": "I know the basics",
        "years": "1-2",
        "goal": "Consistent part time",
        "style": "Swing trading",
        "time": "1-2h",
        "learning": "Watch real examples",
        "frustration": "Inconsistent results",
        "risk": "Some risk with control",
        "tools": "Charting apps",
        "focus": "Both equally"
    }
    response = client.post("/quiz/submit", json=quiz_data)
    assert response.status_code == 200
    data = response.json()
    assert "plan_id" in data
    assert data["tier"] == "free"
    assert len(data["stages"]) == 3
    assert data["stages"][0]["is_free"] is True
    assert data["stages"][0]["locked"] is False
    assert data["stages"][1]["locked"] is True

def test_get_plan_unauthorized():
    response = client.get("/plan/invalid-plan-id")
    assert response.status_code == 404
    assert response.json() == {"error": "Not Found", "message": "Plan not found"}

def test_get_stage_unauthorized():
    response = client.get("/plan/invalid-plan-id/stage/2")
    assert response.status_code == 404
    assert response.json() == {"error": "Not Found", "message": "Stage not found"}