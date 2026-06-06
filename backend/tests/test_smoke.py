"""Smoke tests: auth, RBAC and autonomous resume screening.

Run from the backend dir:  pytest -q
Uses a throwaway SQLite file and FastAPI's TestClient.
"""
import asyncio
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_hrms.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.ai.resume_screener import screen_resume  # noqa: E402
from app.auth.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User, UserRole  # noqa: E402

client = TestClient(app)


def setup_module(_):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(
        User(
            email="admin@test.com",
            hashed_password=hash_password("pw"),
            full_name="Admin",
            role=UserRole.MANAGEMENT_ADMIN,
        )
    )
    db.add(
        User(
            email="emp@test.com",
            hashed_password=hash_password("pw"),
            full_name="Emp",
            role=UserRole.EMPLOYEE,
        )
    )
    db.commit()
    db.close()


def _token(email):
    r = client.post("/api/auth/login", data={"username": email, "password": "pw"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_login_returns_role():
    r = client.post("/api/auth/login", data={"username": "admin@test.com", "password": "pw"})
    assert r.json()["role"] == "management_admin"


def test_bad_password_rejected():
    r = client.post("/api/auth/login", data={"username": "admin@test.com", "password": "nope"})
    assert r.status_code == 401


def test_employee_blocked_from_recruiter_route():
    tok = _token("emp@test.com")
    r = client.get(
        "/api/recruitment/jobs/1/applications", headers={"Authorization": f"Bearer {tok}"}
    )
    assert r.status_code == 403


def test_unauthenticated_blocked():
    assert client.get("/api/employees").status_code == 401


def test_screening_scores_strong_match_higher():
    job_req = "Python, React, Node.js, PostgreSQL, Docker, AWS"
    strong = "Expert in Python, React, Node.js, PostgreSQL, Docker and AWS with 8 years."
    weak = "I enjoy painting and gardening with no technical background."
    s_strong = asyncio.run(screen_resume(strong, "Engineer", job_req))
    s_weak = asyncio.run(screen_resume(weak, "Engineer", job_req))
    assert s_strong["overall_score"] > s_weak["overall_score"]
    assert 1 <= s_strong["overall_score"] <= 10
