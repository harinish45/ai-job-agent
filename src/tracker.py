"""
Application Tracking Database and Store.
Supports SQLite database persistence, query filtering, and JSON import/export.
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.models import ApplicationRecord, ApplicationStatus

logger = logging.getLogger(__name__)


class ApplicationTrackerError(Exception):
    """Raised when application tracker encounters a database or parsing error."""
    pass


class ApplicationTracker:
    """Manages application records in a SQLite database with JSON synchronization."""

    def __init__(self, db_path: str = "applications.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema with tables and indices."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS applications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company TEXT NOT NULL,
                        role TEXT NOT NULL,
                        job_url TEXT,
                        applied_at TEXT NOT NULL,
                        status TEXT NOT NULL,
                        match_score REAL DEFAULT 0.0,
                        notes TEXT,
                        logs TEXT
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_status ON applications(status);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_company ON applications(company);
                """)
                conn.commit()
        except sqlite3.Error as exc:
            logger.error("Failed to initialize SQLite database at %s: %s", self.db_path, exc)
            raise ApplicationTrackerError(f"Database initialization failed: {exc}") from exc

    def add_application(
        self,
        company: str,
        role: str,
        job_url: str = "",
        match_score: float = 0.0,
        status: ApplicationStatus = ApplicationStatus.APPLIED,
        notes: str = ""
    ) -> ApplicationRecord:
        """Insert a new job application record."""
        if not company or not role:
            raise ApplicationTrackerError("Company and Role cannot be empty.")

        applied_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        initial_logs = json.dumps([f"Created application at {applied_at}"])

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO applications (company, role, job_url, applied_at, status, match_score, notes, logs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (company, role, job_url, applied_at, status.value, match_score, notes, initial_logs)
            )
            app_id = cursor.lastrowid
            conn.commit()

        logger.info("Recorded application #%d for %s at %s", app_id, role, company)
        return ApplicationRecord(
            id=app_id,
            company=company,
            role=role,
            job_url=job_url,
            applied_at=applied_at,
            status=status,
            match_score=match_score,
            notes=notes,
            logs=[f"Created application at {applied_at}"]
        )

    def update_status(self, app_id: int, new_status: ApplicationStatus, note: Optional[str] = None) -> bool:
        """Update lifecycle status and append audit log."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"Status updated to '{new_status.value}' at {timestamp}"
        if note:
            log_entry += f" (Note: {note})"

        record = self.get_application(app_id)
        if not record:
            return False

        updated_logs = record.logs + [log_entry]
        combined_notes = f"{record.notes}\n{note}".strip() if note else record.notes

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE applications
                SET status = ?, notes = ?, logs = ?
                WHERE id = ?
                """,
                (new_status.value, combined_notes, json.dumps(updated_logs), app_id)
            )
            conn.commit()

        logger.info("Application #%d status updated to %s", app_id, new_status.value)
        return True

    def get_application(self, app_id: int) -> Optional[ApplicationRecord]:
        """Fetch a single application record by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, company, role, job_url, applied_at, status, match_score, notes, logs FROM applications WHERE id = ?",
                (app_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_record(row)

    def list_applications(
        self,
        status: Optional[ApplicationStatus] = None,
        search: Optional[str] = None,
        limit: int = 50
    ) -> List[ApplicationRecord]:
        """Query applications with optional status filter and text search."""
        query = "SELECT id, company, role, job_url, applied_at, status, match_score, notes, logs FROM applications WHERE 1=1"
        params: List[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status.value)
        if search:
            query += " AND (company LIKE ? OR role LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_record(r) for r in rows]

    def get_statistics(self) -> Dict[str, Any]:
        """Compute aggregate application funnel metrics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
            counts = dict(cursor.fetchall())
            cursor.execute("SELECT COUNT(*), AVG(match_score) FROM applications")
            total, avg_score = cursor.fetchone()

        total = total or 0
        avg_score = round(avg_score or 0.0, 1)
        interviews = counts.get(ApplicationStatus.INTERVIEW.value, 0)
        offers = counts.get(ApplicationStatus.OFFER.value, 0)
        rejected = counts.get(ApplicationStatus.REJECTED.value, 0)

        interview_rate = round((interviews / total * 100.0), 1) if total > 0 else 0.0
        offer_rate = round((offers / total * 100.0), 1) if total > 0 else 0.0

        return {
            "total_applications": total,
            "average_match_score": avg_score,
            "status_breakdown": counts,
            "interview_rate": interview_rate,
            "offer_rate": offer_rate,
            "rejections": rejected
        }

    def export_to_json(self, json_path: str) -> None:
        """Export all application records to a formatted JSON file."""
        apps = self.list_applications(limit=10000)
        data = [
            {
                "id": a.id,
                "company": a.company,
                "role": a.role,
                "job_url": a.job_url,
                "applied_at": a.applied_at,
                "status": a.status.value,
                "match_score": a.match_score,
                "notes": a.notes,
                "logs": a.logs
            }
            for a in apps
        ]
        Path(json_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("Exported %d application records to %s", len(data), json_path)

    def import_from_json(self, json_path: str) -> int:
        """Import applications from JSON file, skipping duplicates."""
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        records = json.loads(path.read_text(encoding="utf-8"))
        count = 0
        for item in records:
            status_enum = ApplicationStatus(item.get("status", ApplicationStatus.APPLIED.value))
            self.add_application(
                company=item.get("company", "Unknown"),
                role=item.get("role", "Unknown"),
                job_url=item.get("job_url", ""),
                match_score=float(item.get("match_score", 0.0)),
                status=status_enum,
                notes=item.get("notes", "")
            )
            count += 1
        return count

    def _row_to_record(self, row: tuple) -> ApplicationRecord:
        """Convert database tuple row into ApplicationRecord dataclass."""
        logs = []
        try:
            logs = json.loads(row[8]) if row[8] else []
        except Exception:
            logs = [row[8]] if row[8] else []

        return ApplicationRecord(
            id=row[0],
            company=row[1],
            role=row[2],
            job_url=row[3],
            applied_at=row[4],
            status=ApplicationStatus(row[5]),
            match_score=float(row[6] or 0.0),
            notes=row[7] or "",
            logs=logs
        )
