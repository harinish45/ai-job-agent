"""
Notification service for alerts, emails, and summaries.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.models import JobAlert, User, JobListing, JobMatchScore
from app.config import get_settings

settings = get_settings()

class NotificationService:
    """Handles all user notifications."""

    def __init__(self, db: Session):
        self.db = db

    def create_instant_alert(
        self,
        user_id: int,
        title: str,
        content: str,
        job_ids: Optional[List[int]] = None
    ) -> JobAlert:
        """Create an instant alert for high-match jobs."""
        alert = JobAlert(
            user_id=user_id,
            alert_type="instant",
            title=title,
            content=content,
            jobs_referenced=job_ids or [],
            is_read=False,
            sent_at=datetime.utcnow()
        )
        self.db.add(alert)
        self.db.commit()
        return alert

    def create_daily_summary(
        self,
        user_id: int,
        new_jobs_count: int,
        strong_matches: List[dict]
    ) -> JobAlert:
        """Create daily summary of new openings."""
        content = f"""
        ## Daily Job Summary - {datetime.utcnow().strftime('%Y-%m-%d')}

        **{new_jobs_count}** new jobs found today.

        ### Top Matches:
        """

        for job in strong_matches[:5]:
            content += f"\n- **{job['title']}** at {job['company']} ({job['score']}% match)"

        alert = JobAlert(
            user_id=user_id,
            alert_type="daily_summary",
            title=f"Daily Summary: {new_jobs_count} new jobs",
            content=content,
            jobs_referenced=[j['id'] for j in strong_matches],
            is_read=False,
            sent_at=datetime.utcnow()
        )
        self.db.add(alert)
        self.db.commit()
        return alert

    def create_weekly_report(
        self,
        user_id: int,
        stats: dict
    ) -> JobAlert:
        """Create weekly performance report."""
        content = f"""
        ## Weekly Performance Report

        | Metric | Value |
        |--------|-------|
        | Applications Sent | {stats.get('total_applied', 0)} |
        | Interviews | {stats.get('interviews', 0)} |
        | Offers | {stats.get('offers', 0)} |
        | Rejections | {stats.get('rejections', 0)} |
        | Ghosted | {stats.get('ghosted', 0)} |
        | Interview Rate | {stats.get('interview_rate', 0)}% |
        | Offer Rate | {stats.get('offer_rate', 0)}% |

        ### Best Performing Platforms:
        """

        for platform in stats.get('platform_breakdown', []):
            content += f"\n- {platform['platform']}: {platform['count']} applications"

        alert = JobAlert(
            user_id=user_id,
            alert_type="weekly_report",
            title="Weekly Performance Report",
            content=content,
            is_read=False,
            sent_at=datetime.utcnow()
        )
        self.db.add(alert)
        self.db.commit()
        return alert

    def notify_captcha_detected(
        self,
        user_id: int,
        job_title: str,
        company: str
    ) -> JobAlert:
        """Alert user when CAPTCHA blocks auto-apply."""
        alert = JobAlert(
            user_id=user_id,
            alert_type="captcha_detected",
            title=f"CAPTCHA detected: {job_title} at {company}",
            content=f"""
            The auto-apply engine encountered a CAPTCHA while applying to **{job_title}** at **{company}**.

            Please complete this application manually.
            """,
            is_read=False,
            sent_at=datetime.utcnow()
        )
        self.db.add(alert)
        self.db.commit()
        return alert

    def notify_application_error(
        self,
        user_id: int,
        job_title: str,
        company: str,
        error: str
    ) -> JobAlert:
        """Alert user when auto-apply fails."""
        alert = JobAlert(
            user_id=user_id,
            alert_type="application_error",
            title=f"Application failed: {job_title}",
            content=f"""
            Failed to apply to **{job_title}** at **{company}**.

            Error: {error}

            Please review and apply manually if desired.
            """,
            is_read=False,
            sent_at=datetime.utcnow()
        )
        self.db.add(alert)
        self.db.commit()
        return alert

    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread alerts."""
        return self.db.query(JobAlert).filter(
            JobAlert.user_id == user_id,
            JobAlert.is_read == False
        ).count()

    def mark_all_read(self, user_id: int):
        """Mark all alerts as read."""
        self.db.query(JobAlert).filter(
            JobAlert.user_id == user_id,
            JobAlert.is_read == False
        ).update({"is_read": True})
        self.db.commit()
