"""
Alert/notification API routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import User, JobAlert
from app.core.security import get_current_user
from app.schemas.schemas import AlertListResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("", response_model=AlertListResponse)
def get_alerts(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(JobAlert).filter(JobAlert.user_id == current_user.id)

    if unread_only:
        query = query.filter(JobAlert.is_read == False)

    alerts = query.order_by(JobAlert.sent_at.desc()).all()

    return {
        "alerts": [
            {
                "id": a.id,
                "type": a.alert_type,
                "title": a.title,
                "content": a.content,
                "is_read": a.is_read,
                "sent_at": a.sent_at,
            }
            for a in alerts
        ]
    }

@router.post("/{alert_id}/read")
def mark_read(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(JobAlert).filter(
        JobAlert.id == alert_id,
        JobAlert.user_id == current_user.id
    ).first()

    if alert:
        alert.is_read = True
        db.commit()

    return {"status": "updated"}
