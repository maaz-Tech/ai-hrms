from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models import ApplicationStatus


class JobCreate(BaseModel):
    title: str
    department: str | None = None
    location: str | None = None
    description: str = ""
    requirements: str = ""


class JobOut(BaseModel):
    id: int
    title: str
    department: str | None
    location: str | None
    description: str
    requirements: str
    status: str
    created_at: datetime
    application_count: int = 0

    class Config:
        from_attributes = True


class ApplicationCreate(BaseModel):
    candidate_name: str
    candidate_email: EmailStr
    resume_text: str


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    candidate_name: str
    candidate_email: EmailStr
    status: ApplicationStatus
    ai_score: float | None
    role_match_score: float | None
    experience_years: float | None
    key_skills: list[str] | None
    missing_skills: list[str] | None
    recommendation: str | None
    reasoning: str | None
    voice_score: float | None

    class Config:
        from_attributes = True
