import asyncio
import io
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.ai import vector_store
from app.ai.resume_screener import screen_resume
from app.auth.deps import get_current_user, is_recruiter_staff
from app.database import get_db
from app.models import Application, ApplicationStatus, JobPosting, User
from app.schemas.recruitment import (
    ApplicationCreate,
    ApplicationOut,
    JobCreate,
    JobOut,
)

router = APIRouter(prefix="/api/recruitment", tags=["recruitment"])

# Auto-shortlist threshold for fully-autonomous screening.
SHORTLIST_THRESHOLD = 7.0


def _job_out(job: JobPosting) -> dict:
    return {
        "id": job.id,
        "title": job.title,
        "department": job.department,
        "location": job.location,
        "description": job.description,
        "requirements": job.requirements,
        "status": job.status,
        "created_at": job.created_at,
        "application_count": len(job.applications),
    }


def _app_out(app: Application) -> dict:
    return {
        "id": app.id,
        "job_id": app.job_id,
        "candidate_name": app.candidate_name,
        "candidate_email": app.candidate_email,
        "status": app.status,
        "ai_score": app.ai_score,
        "role_match_score": app.role_match_score,
        "experience_years": app.experience_years,
        "key_skills": json.loads(app.key_skills) if app.key_skills else None,
        "missing_skills": json.loads(app.missing_skills) if app.missing_skills else None,
        "recommendation": app.recommendation,
        "reasoning": app.reasoning,
        "voice_score": app.voice_score,
    }


# ── Jobs ──────────────────────────────────────────────────────────────────
@router.get("/jobs", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [_job_out(j) for j in db.query(JobPosting).order_by(JobPosting.id.desc()).all()]


@router.post("/jobs", response_model=JobOut, dependencies=[Depends(is_recruiter_staff)])
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    job = JobPosting(**payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return _job_out(job)


@router.get("/jobs/{job_id}/applications", response_model=list[ApplicationOut])
def job_applications(
    job_id: int, db: Session = Depends(get_db), _: User = Depends(is_recruiter_staff)
):
    apps = (
        db.query(Application)
        .filter(Application.job_id == job_id)
        .order_by(Application.ai_score.desc().nullslast())
        .all()
    )
    return [_app_out(a) for a in apps]


# ── Applications & autonomous screening ───────────────────────────────────
async def _screen_and_save(db: Session, app: Application, job: JobPosting) -> None:
    result = await screen_resume(app.resume_text, job.title, job.requirements)
    app.ai_score = float(result.get("overall_score", 0))
    app.role_match_score = float(result.get("role_match_score", 0))
    app.experience_years = float(result.get("experience_years", 0) or 0)
    app.key_skills = json.dumps(result.get("key_skills_found", []))
    app.missing_skills = json.dumps(result.get("missing_skills", []))
    app.recommendation = result.get("recommendation")
    app.reasoning = result.get("reasoning")
    app.screened_at = datetime.now(timezone.utc)
    # Fully autonomous decision — no human in the loop.
    app.status = (
        ApplicationStatus.SHORTLISTED
        if app.ai_score >= SHORTLIST_THRESHOLD
        else ApplicationStatus.SCREENED
    )
    vector_store.index_document(
        point_id=app.id,
        text=app.resume_text,
        payload={
            "kind": "resume",
            "application_id": app.id,
            "candidate": app.candidate_name,
            "job_id": job.id,
        },
    )


@router.post("/jobs/{job_id}/apply", response_model=ApplicationOut)
async def apply(
    job_id: int,
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    job = db.get(JobPosting, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    app = Application(
        job_id=job_id,
        candidate_name=payload.candidate_name,
        candidate_email=payload.candidate_email,
        resume_text=payload.resume_text,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    await _screen_and_save(db, app, job)
    db.commit()
    db.refresh(app)
    return _app_out(app)


@router.post(
    "/jobs/{job_id}/upload",
    response_model=ApplicationOut,
    dependencies=[Depends(is_recruiter_staff)],
)
async def upload_resume(
    job_id: int,
    candidate_name: str = Form(...),
    candidate_email: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a resume file (PDF/text); it is parsed and auto-screened."""
    job = db.get(JobPosting, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    raw = await file.read()
    resume_text = _extract_text(file.filename or "", raw)
    app = Application(
        job_id=job_id,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        resume_text=resume_text,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    await _screen_and_save(db, app, job)
    db.commit()
    db.refresh(app)
    return _app_out(app)


@router.post(
    "/jobs/{job_id}/rescreen",
    response_model=list[ApplicationOut],
    dependencies=[Depends(is_recruiter_staff)],
)
async def rescreen_all(job_id: int, db: Session = Depends(get_db)):
    """Re-run autonomous screening for every application (batch)."""
    job = db.get(JobPosting, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    apps = db.query(Application).filter(Application.job_id == job_id).all()
    # Batch with bounded concurrency to stay within API rate limits.
    for i in range(0, len(apps), 10):
        batch = apps[i : i + 10]
        await asyncio.gather(*(_screen_and_save(db, a, job) for a in batch))
    db.commit()
    apps.sort(key=lambda a: a.ai_score or 0, reverse=True)
    return [_app_out(a) for a in apps]


def _extract_text(filename: str, raw: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader  # noqa: PLC0415

            reader = PdfReader(io.BytesIO(raw))
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception:
            return ""
    try:
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""
