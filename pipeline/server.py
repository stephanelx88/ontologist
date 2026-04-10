from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from pipeline.extract import extract_package
from pipeline.graph import save_graph
from pipeline.models import FraudAssessment
from pipeline.report import generate_json_report, generate_markdown_report
from pipeline.rules import evaluate_all_rules
from pipeline.score import compute_score
from pipeline.vision import ClaudeVision, GeminiVision

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RESULTS_DIR = Path("./web-results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATES_DIR = Path(__file__).parent / "templates"

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

jobs: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Neo Fraud Detection")


# ---------------------------------------------------------------------------
# Background processing
# ---------------------------------------------------------------------------


async def _process_job(job_id: str, pdf_path: Path) -> None:
    """Run the full fraud pipeline for a single PDF and update jobs state."""

    def _append_progress(message: str) -> None:
        jobs[job_id]["progress"].append(message)

    try:
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")

        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

        primary = GeminiVision(api_key=gemini_key)
        fallback = ClaudeVision(api_key=anthropic_key) if anthropic_key else None

        _append_progress("Starting extraction...")

        package = await extract_package(
            pdf_path=pdf_path,
            primary=primary,
            fallback=fallback,
            on_progress=_append_progress,
        )

        _append_progress("Evaluating fraud rules...")
        findings = evaluate_all_rules(package)

        _append_progress("Computing risk score...")
        risk_score, verdict = compute_score(findings)

        timestamp = datetime.now(timezone.utc).isoformat()
        extraction_provider = "gemini+claude" if fallback else "gemini"

        assessment = FraudAssessment(
            loan_reference=package.loan_reference,
            risk_score=risk_score,
            verdict=verdict,
            package=package,
            findings=findings,
            extraction_provider=extraction_provider,
            timestamp=timestamp,
        )

        result_dir = RESULTS_DIR / job_id
        result_dir.mkdir(parents=True, exist_ok=True)

        _append_progress("Saving assessment JSON...")
        json_text = generate_json_report(assessment)
        (result_dir / "assessment.json").write_text(json_text, encoding="utf-8")

        _append_progress("Saving markdown report...")
        md_text = generate_markdown_report(assessment)
        (result_dir / "assessment.md").write_text(md_text, encoding="utf-8")

        _append_progress("Building knowledge graph...")
        save_graph(assessment, result_dir)

        _append_progress("Done.")

        jobs[job_id]["status"] = "complete"
        jobs[job_id]["result"] = json.loads(json_text)

    except Exception as exc:
        error_message = f"Error: {exc}"
        _append_progress(error_message)
        jobs[job_id]["status"] = "error"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
async def serve_index() -> FileResponse:
    """Serve the main single-page application."""
    index_path = TEMPLATES_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(str(index_path), media_type="text/html")


@app.post("/api/analyze")
async def analyze(file: UploadFile) -> JSONResponse:
    """Accept a PDF upload and launch background processing."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are accepted.")

    job_id = str(uuid.uuid4())[:8]

    pdf_dest = RESULTS_DIR / f"{job_id}.pdf"
    content = await file.read()
    pdf_dest.write_bytes(content)

    jobs[job_id] = {
        "status": "processing",
        "progress": [],
        "result": None,
    }

    asyncio.create_task(_process_job(job_id, pdf_dest))

    return JSONResponse({"job_id": job_id})


@app.get("/api/status/{job_id}")
async def stream_status(job_id: str) -> StreamingResponse:
    """Stream job progress as Server-Sent Events."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found.")

    async def _event_generator():
        sent_count = 0

        while True:
            job = jobs[job_id]
            progress_list: list[str] = job["progress"]

            # Emit any unsent progress messages
            while sent_count < len(progress_list):
                message = progress_list[sent_count]
                payload = json.dumps({"type": "progress", "message": message})
                yield f"data: {payload}\n\n"
                sent_count += 1

            status = job["status"]
            if status in ("complete", "error"):
                done_payload = json.dumps(
                    {
                        "type": "done",
                        "status": status,
                        "result": job.get("result"),
                    }
                )
                yield f"data: {done_payload}\n\n"
                return

            await asyncio.sleep(0.5)

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/results/{job_id}")
async def get_results(job_id: str) -> JSONResponse:
    """Return completed assessment JSON for a job."""
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["status"] != "complete":
        raise HTTPException(status_code=409, detail=f"Job status: {job['status']}")
    return JSONResponse(job["result"])


@app.get("/api/graph/{job_id}")
async def get_graph(job_id: str) -> FileResponse:
    """Serve the graph.html file for a completed job."""
    graph_html = RESULTS_DIR / job_id / "graph.html"
    if not graph_html.exists():
        raise HTTPException(status_code=404, detail="Graph not found for this job.")
    return FileResponse(str(graph_html), media_type="text/html")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> None:
    """Web server entry point."""
    parser = argparse.ArgumentParser(
        prog="neo-fraud-server",
        description="Neo Fraud Detection — FastAPI web server",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)",
    )

    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
