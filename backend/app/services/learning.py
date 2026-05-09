"""
Learning Feedback Service
Tracks application outcomes and improves future targeting.
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.models import LearningFeedback, JobApplication, JobMatchScore
from app.config import get_settings

settings = get_settings()

class LearningService:
    """Learns from application outcomes to improve targeting."""

    def __init__(self, db: Session):
        self.db = db

    def record_feedback(
        self,
        user_id: int,
        application_id: int,
        outcome: str,  # accepted, rejected, ghosted, interview, offer
        feedback_text: Optional[str] = None,
        successful_elements: Optional[List[str]] = None,
        failed_elements: Optional[List[str]] = None
    ) -> LearningFeedback:
        """Record feedback for an application outcome."""

        # Get match score at time of application
        app = self.db.query(JobApplication).filter(
            JobApplication.id == application_id,
            JobApplication.user_id == user_id
        ).first()

        match_score = None
        if app:
            match = self.db.query(JobMatchScore).filter(
                JobMatchScore.job_id == app.job_id,
                JobMatchScore.user_id == user_id
            ).first()
            if match:
                match_score = match.overall_score

        feedback = LearningFeedback(
            user_id=user_id,
            application_id=application_id,
            outcome=outcome,
            feedback_text=feedback_text,
            successful_elements=successful_elements or [],
            failed_elements=failed_elements or [],
            match_score_at_apply=match_score,
            created_at=datetime.utcnow()
        )
        self.db.add(feedback)
        self.db.commit()
        return feedback

    def get_user_insights(self, user_id: int) -> Dict:
        """Get insights from user's application history."""
        feedbacks = self.db.query(LearningFeedback).filter(
            LearningFeedback.user_id == user_id
        ).all()

        if not feedbacks:
            return {"message": "Not enough data for insights yet"}

        total = len(feedbacks)
        interviews = sum(1 for f in feedbacks if f.outcome in ['interview', 'offer'])
        offers = sum(1 for f in feedbacks if f.outcome == 'offer')
        rejections = sum(1 for f in feedbacks if f.outcome == 'rejected')
        ghosted = sum(1 for f in feedbacks if f.outcome == 'ghosted')

        # Average match score for successful vs unsuccessful
        successful_scores = [f.match_score_at_apply for f in feedbacks
                           if f.outcome in ['interview', 'offer'] and f.match_score_at_apply]
        unsuccessful_scores = [f.match_score_at_apply for f in feedbacks
                             if f.outcome in ['rejected', 'ghosted'] and f.match_score_at_apply]

        avg_successful = sum(successful_scores) / len(successful_scores) if successful_scores else 0
        avg_unsuccessful = sum(unsuccessful_scores) / len(unsuccessful_scores) if unsuccessful_scores else 0

        # Common successful elements
        all_successful = []
        for f in feedbacks:
            all_successful.extend(f.successful_elements or [])

        from collections import Counter
        top_successful = Counter(all_successful).most_common(5)

        # Common failed elements
        all_failed = []
        for f in feedbacks:
            all_failed.extend(f.failed_elements or [])
        top_failed = Counter(all_failed).most_common(5)

        return {
            "total_applications_analyzed": total,
            "interview_rate": round(interviews / total * 100, 1) if total > 0 else 0,
            "offer_rate": round(offers / total * 100, 1) if total > 0 else 0,
            "ghosting_rate": round(ghosted / total * 100, 1) if total > 0 else 0,
            "avg_match_score_successful": round(avg_successful, 3),
            "avg_match_score_unsuccessful": round(avg_unsuccessful, 3),
            "optimal_match_threshold": round((avg_successful + avg_unsuccessful) / 2, 3) if avg_successful and avg_unsuccessful else 0.75,
            "top_successful_elements": [{"element": e, "count": c} for e, c in top_successful],
            "top_failed_elements": [{"element": e, "count": c} for e, c in top_failed],
            "recommendations": self._generate_recommendations(
                avg_successful, avg_unsuccessful, top_successful, top_failed
            )
        }

    def _generate_recommendations(
        self,
        avg_successful: float,
        avg_unsuccessful: float,
        top_successful: List,
        top_failed: List
    ) -> List[str]:
        """Generate actionable recommendations based on insights."""
        recommendations = []

        if avg_successful > avg_unsuccessful + 0.1:
            recommendations.append(
                f"Higher match scores correlate with success. Consider raising your minimum match threshold to {round((avg_successful + avg_unsuccessful) / 2, 2)}."
            )

        if top_successful:
            recommendations.append(
                f"Your strongest application elements: {', '.join(e for e, _ in top_successful[:3])}. Emphasize these more."
            )

        if top_failed:
            recommendations.append(
                f"Common weaknesses: {', '.join(e for e, _ in top_failed[:3])}. Address these in future applications."
            )

        if not recommendations:
            recommendations.append("Keep applying and recording feedback to generate personalized insights.")

        return recommendations

    def suggest_improvements(self, user_id: int) -> List[Dict]:
        """Suggest specific improvements based on patterns."""
        insights = self.get_user_insights(user_id)

        suggestions = []

        if insights.get("ghosting_rate", 0) > 50:
            suggestions.append({
                "category": "follow_up",
                "priority": "high",
                "suggestion": "High ghosting rate detected. Consider following up 7-10 days after applying.",
                "action": "Set follow-up reminders for all applications"
            })

        if insights.get("interview_rate", 0) < 10:
            suggestions.append({
                "category": "resume",
                "priority": "high",
                "suggestion": "Low interview rate. Your resume may need optimization for ATS systems.",
                "action": "Review and update resume with more quantifiable achievements"
            })

        if insights.get("avg_match_score_successful", 0) > 0:
            suggestions.append({
                "category": "targeting",
                "priority": "medium",
                "suggestion": f"Focus on roles with match scores above {insights.get('optimal_match_threshold', 0.75)}",
                "action": "Adjust auto-apply minimum match score"
            })

        return suggestions
