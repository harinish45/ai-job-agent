"""
Structured logging service for application tracking.
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import ApplicationLog

class ApplicationLogger:
    """Logs every action during the application process."""

    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        application_id: int,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        screenshot_path: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> ApplicationLog:
        """Log an application action."""
        log = ApplicationLog(
            application_id=application_id,
            action=action,
            details=details or {},
            screenshot_path=screenshot_path,
            success=success,
            error_message=error_message,
            timestamp=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()
        return log

    def log_form_fill(
        self,
        application_id: int,
        field_name: str,
        field_type: str,
        value_filled: bool,
        error: Optional[str] = None
    ):
        """Log form field fill attempt."""
        return self.log_action(
            application_id=application_id,
            action="form_fill",
            details={
                "field_name": field_name,
                "field_type": field_type,
                "value_filled": value_filled
            },
            success=value_filled,
            error_message=error
        )

    def log_page_navigation(
        self,
        application_id: int,
        url: str,
        page_title: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        """Log page navigation."""
        return self.log_action(
            application_id=application_id,
            action="page_navigation",
            details={
                "url": url,
                "page_title": page_title,
                "status_code": status_code
            }
        )

    def log_captcha_detected(
        self,
        application_id: int,
        captcha_type: str,
        screenshot_path: Optional[str] = None
    ):
        """Log CAPTCHA detection."""
        return self.log_action(
            application_id=application_id,
            action="captcha_detected",
            details={"captcha_type": captcha_type},
            screenshot_path=screenshot_path,
            success=False
        )

    def log_submit_attempt(
        self,
        application_id: int,
        success: bool,
        response_data: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """Log submit attempt."""
        return self.log_action(
            application_id=application_id,
            action="submit",
            details=response_data,
            success=success,
            error_message=error
        )

    def get_logs_for_application(
        self,
        application_id: int,
        limit: int = 100
    ) -> list:
        """Get all logs for an application."""
        return self.db.query(ApplicationLog).filter(
            ApplicationLog.application_id == application_id
        ).order_by(ApplicationLog.timestamp.desc()).limit(limit).all()
