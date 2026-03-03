"""In-memory job store for the CV Generator web UI."""
from __future__ import annotations

import threading
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any


class CapacityError(Exception):
    """Raised when the job pool is full."""


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class JobStore:
    """Thread-safe in-memory job store with TTL-based cleanup."""

    def __init__(self, max_jobs: int = 3, ttl_seconds: int = 3600):
        self.jobs: dict[str, dict[str, Any]] = {}
        self.max_jobs = max_jobs
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()

    def create(self) -> str:
        """Create a new job with PENDING status. Raises CapacityError if pool is full."""
        with self._lock:
            self._cleanup_locked()
            if self.active_count_locked() >= self.max_jobs:
                raise CapacityError("Server is busy — please try again shortly.")
            job_id = uuid.uuid4().hex
            self.jobs[job_id] = {
                "id": job_id,
                "status": JobStatus.PENDING,
                "progress_stage": "",
                "progress_step": 0,
                "result_path": None,
                "error": None,
                "company": None,
                "title": None,
                "created_at": time.time(),
                "events": [],
            }
            return job_id

    def get(self, job_id: str) -> dict[str, Any] | None:
        """Return a safe copy of job dict or None."""
        with self._lock:
            job = self.jobs.get(job_id)
            if job is None:
                return None
            # F11: Deep copy to avoid leaking mutable events list
            copy = dict(job)
            copy["events"] = list(job["events"])
            return copy

    def update_progress(self, job_id: str, stage: str, step: int) -> None:
        """Update job progress and append an event."""
        with self._lock:
            job = self.jobs.get(job_id)
            if job is None:
                return
            job["status"] = JobStatus.RUNNING
            job["progress_stage"] = stage
            job["progress_step"] = step
            event_id = len(job["events"])
            job["events"].append({
                "event": "progress",
                "data": {"stage": stage, "step": step},
                "id": event_id,
            })

    def complete(self, job_id: str, result_path: Path, company: str | None, title: str | None) -> None:
        """Mark a job as complete with result metadata."""
        with self._lock:
            job = self.jobs.get(job_id)
            if job is None:
                return
            job["status"] = JobStatus.COMPLETE
            job["result_path"] = result_path
            job["company"] = company
            job["title"] = title
            event_id = len(job["events"])
            job["events"].append({
                "event": "complete",
                "data": {
                    "status": "complete",
                    "company": company or "Unknown",
                    "title": title or "Unknown",
                    "job_id": job_id,
                },
                "id": event_id,
            })

    def fail(self, job_id: str, error: str) -> None:
        """Mark a job as failed with error message."""
        with self._lock:
            job = self.jobs.get(job_id)
            if job is None:
                return
            job["status"] = JobStatus.FAILED
            job["error"] = error
            event_id = len(job["events"])
            # F25: Use "pipeline_error" to avoid conflict with native EventSource error
            job["events"].append({
                "event": "pipeline_error",
                "data": {"status": "error", "message": error},
                "id": event_id,
            })

    def get_events_since(self, job_id: str, index: int) -> list[dict]:
        """Return events from index onwards (thread-safe copy)."""
        with self._lock:
            job = self.jobs.get(job_id)
            if job is None:
                return []
            return list(job["events"][index:])

    def active_count(self) -> int:
        """Count PENDING + RUNNING jobs."""
        with self._lock:
            return self.active_count_locked()

    def active_count_locked(self) -> int:
        """Count PENDING + RUNNING jobs (caller must hold lock)."""
        return sum(
            1 for j in self.jobs.values()
            if j["status"] in (JobStatus.PENDING, JobStatus.RUNNING)
        )

    def cleanup(self) -> None:
        """Remove jobs older than TTL."""
        with self._lock:
            self._cleanup_locked()

    def _cleanup_locked(self) -> None:
        """Remove expired finished jobs (caller must hold lock)."""
        now = time.time()
        # F6: Only clean up COMPLETE/FAILED jobs — never evict PENDING/RUNNING
        expired = [
            jid for jid, j in self.jobs.items()
            if now - j["created_at"] > self.ttl_seconds
            and j["status"] in (JobStatus.COMPLETE, JobStatus.FAILED)
        ]
        for jid in expired:
            job = self.jobs[jid]
            if job["result_path"]:
                Path(job["result_path"]).unlink(missing_ok=True)
            del self.jobs[jid]
