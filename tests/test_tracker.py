"""
Unit tests for Application Tracker and Persistence Store.
"""

import tempfile
from pathlib import Path
import pytest
from src.models import ApplicationStatus
from src.tracker import ApplicationTracker, ApplicationTrackerError


@pytest.fixture
def temp_tracker():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_path = tf.name
    tracker = ApplicationTracker(db_path=temp_path)
    yield tracker
    # Clean up
    try:
        Path(temp_path).unlink(missing_ok=True)
    except Exception:
        pass


def test_add_and_get_application(temp_tracker):
    app = temp_tracker.add_application(
        company="Anthropic",
        role="Research Engineer",
        job_url="https://jobs.lever.co/anthropic/123",
        match_score=92.5,
        status=ApplicationStatus.APPLIED,
        notes="Applied via agent"
    )

    assert app.id is not None
    assert app.company == "Anthropic"
    assert app.role == "Research Engineer"
    assert app.match_score == 92.5
    assert app.status == ApplicationStatus.APPLIED

    fetched = temp_tracker.get_application(app.id)
    assert fetched is not None
    assert fetched.company == "Anthropic"


def test_update_status(temp_tracker):
    app = temp_tracker.add_application(
        company="OpenAI",
        role="Platform Engineer",
        status=ApplicationStatus.APPLIED
    )

    success = temp_tracker.update_status(
        app_id=app.id,
        new_status=ApplicationStatus.INTERVIEW,
        note="Recruiter reached out for screen"
    )
    assert success is True

    updated = temp_tracker.get_application(app.id)
    assert updated.status == ApplicationStatus.INTERVIEW
    assert len(updated.logs) >= 2


def test_list_and_filter(temp_tracker):
    temp_tracker.add_application(company="Google", role="SWE", status=ApplicationStatus.APPLIED)
    temp_tracker.add_application(company="Meta", role="ML SWE", status=ApplicationStatus.INTERVIEW)
    temp_tracker.add_application(company="Amazon", role="DevOps", status=ApplicationStatus.REJECTED)

    all_apps = temp_tracker.list_applications()
    assert len(all_apps) == 3

    interviews = temp_tracker.list_applications(status=ApplicationStatus.INTERVIEW)
    assert len(interviews) == 1
    assert interviews[0].company == "Meta"

    searched = temp_tracker.list_applications(search="Google")
    assert len(searched) == 1
    assert searched[0].company == "Google"


def test_get_statistics(temp_tracker):
    temp_tracker.add_application(company="A", role="Eng", match_score=80.0, status=ApplicationStatus.APPLIED)
    temp_tracker.add_application(company="B", role="Eng", match_score=90.0, status=ApplicationStatus.INTERVIEW)
    temp_tracker.add_application(company="C", role="Eng", match_score=70.0, status=ApplicationStatus.REJECTED)

    stats = temp_tracker.get_statistics()
    assert stats["total_applications"] == 3
    assert stats["average_match_score"] == 80.0
    assert stats["interview_rate"] == 33.3
    assert stats["rejections"] == 1


def test_json_export_and_import(temp_tracker, tmp_path):
    temp_tracker.add_application(company="Stripe", role="Staff Eng", match_score=95.0)
    export_file = str(tmp_path / "apps.json")
    temp_tracker.export_to_json(export_file)

    assert Path(export_file).exists()

    new_db = str(tmp_path / "new_apps.db")
    tracker2 = ApplicationTracker(db_path=new_db)
    imported_count = tracker2.import_from_json(export_file)

    assert imported_count == 1
    imported_apps = tracker2.list_applications()
    assert len(imported_apps) == 1
    assert imported_apps[0].company == "Stripe"


def test_add_empty_company_raises(temp_tracker):
    with pytest.raises(ApplicationTrackerError):
        temp_tracker.add_application(company="", role="Developer")
