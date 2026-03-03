"""FastAPI web application for the CV Generator."""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from src.web.jobs import CapacityError, JobStatus, JobStore

app = FastAPI(title="CV Generator")

# CORS
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Job store
job_store = JobStore(max_jobs=int(os.getenv("MAX_CONCURRENT_JOBS", "3")))

# Background task references (prevent GC collection — F3)
_background_tasks: set[asyncio.Task] = set()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TEXT_SIZE = 500 * 1024  # 500KB
ALLOWED_SUFFIXES = {".pdf", ".html", ".htm", ".txt"}
ALLOWED_URL_SCHEMES = {"http", "https"}


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


@app.post("/api/jobs", status_code=202)
async def submit_job(
    mode: str = Form(...),
    file: UploadFile | None = File(None),
    url: str | None = Form(None),
    text: str | None = Form(None),
    search: str | None = Form(None),
    location: str | None = Form("Amsterdam"),
):
    # Validate input based on mode
    job_url = None
    job_file = None
    search_term = None
    temp_path = None

    if mode == "file":
        if file is None or file.filename == "":
            return JSONResponse(status_code=422, content={"error": "File is required for file mode."})
        # F2: Validate file suffix before reading
        suffix = Path(file.filename).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            return JSONResponse(status_code=422, content={"error": f"Unsupported file type. Accepted: {', '.join(ALLOWED_SUFFIXES)}"})
        # F13: Read in chunks to avoid loading huge files into memory
        chunks = []
        total_size = 0
        while True:
            chunk = await file.read(64 * 1024)  # 64KB chunks
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                return JSONResponse(status_code=413, content={"error": "File too large — maximum 10MB."})
            chunks.append(chunk)
        contents = b"".join(chunks)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(contents)
        tmp.close()
        temp_path = tmp.name
        job_file = temp_path

    elif mode == "url":
        if not url or not url.strip():
            return JSONResponse(status_code=422, content={"error": "URL is required for URL mode."})
        job_url = url.strip()
        # F1: Validate URL scheme to prevent SSRF
        parsed = urlparse(job_url)
        if parsed.scheme not in ALLOWED_URL_SCHEMES:
            return JSONResponse(status_code=422, content={"error": "Only http:// and https:// URLs are accepted."})

    elif mode == "text":
        if not text or not text.strip():
            return JSONResponse(status_code=422, content={"error": "Text is required for text mode."})
        if len(text.encode("utf-8")) > MAX_TEXT_SIZE:
            return JSONResponse(status_code=413, content={"error": "Text too large — maximum 500KB."})
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
        tmp.write(text)
        tmp.close()
        temp_path = tmp.name
        job_file = temp_path

    elif mode == "search":
        if not search or not search.strip():
            return JSONResponse(status_code=422, content={"error": "Search term is required for search mode."})
        if not location or not location.strip():
            return JSONResponse(status_code=422, content={"error": "Location is required for search mode."})
        search_term = search.strip()
        location = location.strip()

    else:
        return JSONResponse(status_code=422, content={"error": f"Invalid mode: {mode}"})

    # Create job
    try:
        job_id = job_store.create()
    except CapacityError:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
        return JSONResponse(status_code=503, content={"error": "Server is busy — please try again shortly."})

    # F3: Store task reference to prevent GC collection
    task = asyncio.create_task(
        asyncio.to_thread(
            _run_pipeline,
            job_id,
            job_url=job_url,
            job_file=job_file,
            search=search_term,
            location=location or "Amsterdam",
            temp_path=temp_path,
        )
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}/events")
async def job_events(job_id: str, request: Request):
    job = job_store.get(job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"error": "Job not found."})

    # F7: Safe parse of Last-Event-ID header
    try:
        last_event_id = int(request.headers.get("last-event-id", "0"))
    except (ValueError, TypeError):
        last_event_id = 0

    async def event_generator():
        idx = last_event_id
        while True:
            if await request.is_disconnected():
                break

            # F10: If job was cleaned up, terminate the stream
            current = job_store.get(job_id)
            if current is None:
                yield {
                    "event": "pipeline_error",
                    "data": json.dumps({"status": "error", "message": "Job expired."}),
                }
                break

            events = job_store.get_events_since(job_id, idx)
            for event in events:
                yield {
                    "event": event["event"],
                    "data": json.dumps(event["data"]),
                    "id": str(event["id"]),
                }
                idx = event["id"] + 1

            # Check if job is done
            if current["status"] in (JobStatus.COMPLETE, JobStatus.FAILED):
                # Yield any remaining events after status check
                remaining = job_store.get_events_since(job_id, idx)
                for event in remaining:
                    yield {
                        "event": event["event"],
                        "data": json.dumps(event["data"]),
                        "id": str(event["id"]),
                    }
                break

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@app.get("/api/jobs/{job_id}/download")
async def download_cv(job_id: str):
    job = job_store.get(job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"error": "Job not found."})
    if job["status"] != JobStatus.COMPLETE:
        return JSONResponse(status_code=409, content={"error": "Job is not yet complete."})
    if not job["result_path"] or not Path(job["result_path"]).exists():
        return JSONResponse(status_code=404, content={"error": "PDF file not found."})

    return FileResponse(
        path=str(job["result_path"]),
        media_type="application/pdf",
        filename="CV_Alessandro_van_Reusel.pdf",
    )


# F14: Sanitize error messages to avoid leaking internals
_USER_FRIENDLY_ERRORS = {
    "Could not extract enough text": "We couldn't extract enough text from the job ad — try pasting the text directly.",
    "No results found": "No matching jobs found — try different search terms.",
    "No input provided": "No input was provided. Please submit a job ad.",
}


def _sanitize_error(error: str) -> str:
    """Return a user-friendly error message, hiding internal details."""
    for key, friendly in _USER_FRIENDLY_ERRORS.items():
        if key in error:
            return friendly
    return "An error occurred during CV generation. Please try again."


def _run_pipeline(
    job_id: str,
    *,
    job_url: str | None,
    job_file: str | None,
    search: str | None,
    location: str,
    temp_path: str | None,
) -> None:
    """Run the CV pipeline in a background thread."""
    try:
        from src.config import Config
        from src.main import CvPipeline

        config = Config()
        pipeline = CvPipeline(config)

        def progress_callback(stage: str, step: int) -> None:
            job_store.update_progress(job_id, stage, step)

        result_path = pipeline.run(
            job_url=job_url,
            job_file=job_file,
            search=search,
            location=location,
            language=None,
            no_photo=False,
            output=None,
            progress_callback=progress_callback,
        )

        company = None
        title = None
        if pipeline.last_requirements is not None:
            company = pipeline.last_requirements.company
            title = pipeline.last_requirements.title

        job_store.complete(job_id, result_path, company, title)

    except Exception as e:
        job_store.fail(job_id, _sanitize_error(str(e)))

    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


def run_server() -> None:
    """Entry point for the cv-web console script."""
    import uvicorn

    uvicorn.run(
        "src.web.app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )


if __name__ == "__main__":
    run_server()
