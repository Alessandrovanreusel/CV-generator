"""Tests for the web UI endpoints."""

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.web.app import app, job_store
from src.web.jobs import CapacityError, JobStatus, JobStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_job_store():
    """Reset the job store before each test."""
    job_store.jobs.clear()
    job_store.max_jobs = 3
    yield
    job_store.jobs.clear()


@pytest.fixture
def client():
    return TestClient(app)


def _noop_pipeline(*args, **kwargs):
    """No-op replacement for _run_pipeline in tests."""
    pass


# ---------------------------------------------------------------------------
# Submit endpoint tests
# ---------------------------------------------------------------------------

class TestSubmitJob:

    def test_submit_url_job(self, client):
        with patch("src.web.app._run_pipeline", _noop_pipeline):
            response = client.post(
                "/api/jobs",
                data={"mode": "url", "url": "https://example.com/job"},
            )
        assert response.status_code == 202
        assert "job_id" in response.json()

    def test_submit_file_upload(self, client, tmp_path):
        test_file = tmp_path / "job.txt"
        test_file.write_text("Senior Engineer at TestCorp - " * 10, encoding="utf-8")

        with patch("src.web.app._run_pipeline", _noop_pipeline):
            with open(test_file, "rb") as f:
                response = client.post(
                    "/api/jobs",
                    data={"mode": "file"},
                    files={"file": ("job.txt", f, "text/plain")},
                )
        assert response.status_code == 202
        assert "job_id" in response.json()

    def test_submit_text_paste(self, client):
        with patch("src.web.app._run_pipeline", _noop_pipeline):
            response = client.post(
                "/api/jobs",
                data={"mode": "text", "text": "Senior Engineer at TestCorp " * 10},
            )
        assert response.status_code == 202
        assert "job_id" in response.json()

    def test_submit_search(self, client):
        with patch("src.web.app._run_pipeline", _noop_pipeline):
            response = client.post(
                "/api/jobs",
                data={"mode": "search", "search": "data engineer", "location": "Amsterdam"},
            )
        assert response.status_code == 202
        assert "job_id" in response.json()

    def test_submit_no_input(self, client):
        response = client.post(
            "/api/jobs",
            data={"mode": "url"},
        )
        assert response.status_code == 422

    def test_submit_when_pool_full(self, client):
        job_store.max_jobs = 0
        response = client.post(
            "/api/jobs",
            data={"mode": "text", "text": "Engineer job posting " * 10},
        )
        assert response.status_code == 503
        assert "busy" in response.json()["error"].lower()

    def test_submit_url_rejects_non_http_scheme(self, client):
        """F1: SSRF prevention — reject file:// and other non-http schemes."""
        response = client.post(
            "/api/jobs",
            data={"mode": "url", "url": "file:///etc/passwd"},
        )
        assert response.status_code == 422
        assert "http" in response.json()["error"].lower()

    def test_submit_file_rejects_unsupported_extension(self, client, tmp_path):
        """F2: Reject file uploads with unsupported extensions."""
        test_file = tmp_path / "script.py"
        test_file.write_text("import os", encoding="utf-8")
        with open(test_file, "rb") as f:
            response = client.post(
                "/api/jobs",
                data={"mode": "file"},
                files={"file": ("script.py", f, "text/plain")},
            )
        assert response.status_code == 422
        assert "unsupported" in response.json()["error"].lower()

    def test_submit_text_rejects_oversized(self, client):
        """F24: Reject pasted text exceeding MAX_TEXT_SIZE."""
        huge_text = "x" * (500 * 1024 + 1)
        response = client.post(
            "/api/jobs",
            data={"mode": "text", "text": huge_text},
        )
        assert response.status_code == 413


# ---------------------------------------------------------------------------
# Download endpoint tests
# ---------------------------------------------------------------------------

class TestDownloadJob:

    def test_download_completed_job(self, client, tmp_path):
        pdf_file = tmp_path / "test_cv.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")

        job_id = job_store.create()
        job_store.complete(job_id, pdf_file, "TestCorp", "Engineer")

        response = client.get(f"/api/jobs/{job_id}/download")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_download_unknown_job(self, client):
        response = client.get("/api/jobs/nonexistent/download")
        assert response.status_code == 404

    def test_download_incomplete_job(self, client):
        job_id = job_store.create()
        response = client.get(f"/api/jobs/{job_id}/download")
        assert response.status_code == 409


# ---------------------------------------------------------------------------
# SSE endpoint tests
# ---------------------------------------------------------------------------

class TestSSEEvents:

    def test_sse_events(self, client):
        """Test that SSE endpoint replays pre-populated events."""
        job_id = job_store.create()
        # Pre-populate events as if the pipeline ran
        job_store.update_progress(job_id, "Scraping job ad", 1)
        job_store.update_progress(job_id, "Detecting language", 2)
        job_store.update_progress(job_id, "Analyzing job requirements", 3)
        job_store.complete(job_id, Path("/tmp/fake.pdf"), "TestCorp", "Engineer")

        with client.stream("GET", f"/api/jobs/{job_id}/events") as response:
            assert response.status_code == 200
            events = []
            for line in response.iter_lines():
                if line.startswith("data:"):
                    events.append(line)
                # Stop after getting enough events
                if len(events) >= 4:
                    break

        # Should have received progress + complete events
        assert len(events) >= 4

    def test_sse_unknown_job(self, client):
        response = client.get("/api/jobs/nonexistent/events")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# JobStore unit tests
# ---------------------------------------------------------------------------

class TestJobStore:

    def test_create_and_get(self):
        store = JobStore(max_jobs=3)
        job_id = store.create()
        job = store.get(job_id)
        assert job is not None
        assert job["status"] == JobStatus.PENDING

    def test_capacity_error(self):
        store = JobStore(max_jobs=1)
        store.create()
        with pytest.raises(CapacityError):
            store.create()

    def test_update_progress(self):
        store = JobStore()
        job_id = store.create()
        store.update_progress(job_id, "Scraping", 1)
        job = store.get(job_id)
        assert job["status"] == JobStatus.RUNNING
        assert job["progress_step"] == 1

    def test_complete(self):
        store = JobStore()
        job_id = store.create()
        store.complete(job_id, Path("/tmp/cv.pdf"), "TestCorp", "Engineer")
        job = store.get(job_id)
        assert job["status"] == JobStatus.COMPLETE

    def test_fail(self):
        store = JobStore()
        job_id = store.create()
        store.fail(job_id, "Something went wrong")
        job = store.get(job_id)
        assert job["status"] == JobStatus.FAILED
        assert job["error"] == "Something went wrong"

    def test_get_events_since(self):
        store = JobStore()
        job_id = store.create()
        store.update_progress(job_id, "Step 1", 1)
        store.update_progress(job_id, "Step 2", 2)
        events = store.get_events_since(job_id, 0)
        assert len(events) == 2
        events_from_1 = store.get_events_since(job_id, 1)
        assert len(events_from_1) == 1

    def test_cleanup_expired_jobs(self, tmp_path):
        store = JobStore(ttl_seconds=0)
        job_id = store.create()
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"fake")
        store.complete(job_id, pdf, "Corp", "Title")
        time.sleep(0.01)
        store.cleanup()
        assert store.get(job_id) is None
        assert not pdf.exists()

    def test_get_nonexistent(self):
        store = JobStore()
        assert store.get("nonexistent") is None

    def test_cleanup_skips_running_jobs(self):
        """F6: Running jobs must not be evicted by TTL cleanup."""
        store = JobStore(ttl_seconds=0)
        job_id = store.create()
        store.update_progress(job_id, "Analyzing", 3)
        time.sleep(0.01)
        store.cleanup()
        assert store.get(job_id) is not None
        assert store.get(job_id)["status"] == JobStatus.RUNNING

    def test_get_returns_independent_copy(self):
        """F11: get() must return an independent copy with its own events list."""
        store = JobStore()
        job_id = store.create()
        store.update_progress(job_id, "Step 1", 1)
        copy = store.get(job_id)
        # Mutating the copy's events should not affect the store
        copy["events"].append({"fake": True})
        original_events = store.get_events_since(job_id, 0)
        assert len(original_events) == 1  # Still just the one real event
