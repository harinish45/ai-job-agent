"""
Learning & Insights API routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import User
from app.core.security import get_current_user
from app.services.learning import LearningService

router = APIRouter(prefix="/insights", tags=["insights"])

@router.get("/performance")
def get_performance_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = LearningService(db)
    insights = service.get_user_insights(current_user.id)
    suggestions = service.suggest_improvements(current_user.id)
    return {"insights": insights, "suggestions": suggestions}

@router.post("/feedback")
def record_feedback(
    application_id: int,
    outcome: str,
    feedback_text: str = None,
    successful_elements: list = None,
    failed_elements: list = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = LearningService(db)
    feedback = service.record_feedback(
        user_id=current_user.id,
        application_id=application_id,
        outcome=outcome,
        feedback_text=feedback_text,
        successful_elements=successful_elements,
        failed_elements=failed_elements
    )
    return {"status": "recorded", "feedback_id": feedback.id}
