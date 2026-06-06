from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models import (
    Application,
    ApplicationStatus,
    AttendanceRecord,
    Department,
    Employee,
    Goal,
    JobPosting,
    LeaveRequest,
    User,
    UserRole,
)
from app.routers.common import employee_for_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/me")
def my_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Personalised activity dashboard for the logged-in user."""
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        return {"role": user.role.value, "employee": None}

    today = date.today()
    month_att = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.employee_id == emp.id,
            AttendanceRecord.date >= today.replace(day=1),
        )
        .all()
    )
    goals = db.query(Goal).filter(Goal.employee_id == emp.id).all()
    pending_leaves = (
        db.query(LeaveRequest)
        .filter(LeaveRequest.employee_id == emp.id, LeaveRequest.status == "pending")
        .count()
    )
    return {
        "role": user.role.value,
        "employee": {
            "id": emp.id,
            "name": emp.full_name,
            "job_title": emp.job_title,
            "department": emp.department.name if emp.department else None,
            "leave_balance": emp.leave_balance,
        },
        "stats": {
            "days_present_this_month": sum(
                1 for a in month_att if a.status in ("present", "wfh")
            ),
            "open_goals": sum(1 for g in goals if g.status != "completed"),
            "avg_goal_progress": round(
                sum(g.progress for g in goals) / len(goals), 1
            )
            if goals
            else 0,
            "pending_leave_requests": pending_leaves,
        },
        "goals": [
            {"title": g.title, "progress": g.progress, "status": g.status} for g in goals[:5]
        ],
        "attendance_trend": _attendance_trend(month_att),
    }


@router.get("/company")
def company_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Company-wide dashboard — admins & managers only."""
    if user.role not in (UserRole.MANAGEMENT_ADMIN, UserRole.SENIOR_MANAGER, UserRole.HR_RECRUITER):
        return {"error": "forbidden"}

    total_emp = db.query(Employee).filter(Employee.status == "active").count()
    headcount_by_dept = (
        db.query(Department.name, func.count(Employee.id))
        .join(Employee, Employee.department_id == Department.id)
        .group_by(Department.name)
        .all()
    )
    open_jobs = db.query(JobPosting).filter(JobPosting.status == "open").count()
    total_apps = db.query(Application).count()
    shortlisted = (
        db.query(Application)
        .filter(Application.status == ApplicationStatus.SHORTLISTED)
        .count()
    )
    pending_leaves = (
        db.query(LeaveRequest).filter(LeaveRequest.status == "pending").count()
    )
    today = date.today()
    present_today = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.date == today,
            AttendanceRecord.status.in_(["present", "wfh"]),
        )
        .count()
    )
    return {
        "role": user.role.value,
        "totals": {
            "active_employees": total_emp,
            "present_today": present_today,
            "open_jobs": open_jobs,
            "total_applications": total_apps,
            "shortlisted_candidates": shortlisted,
            "pending_leave_requests": pending_leaves,
        },
        "headcount_by_department": [
            {"department": name, "count": count} for name, count in headcount_by_dept
        ],
        "application_funnel": _application_funnel(db),
    }


def _attendance_trend(records) -> list[dict]:
    by_day: dict[str, float] = {}
    for r in sorted(records, key=lambda x: x.date):
        by_day[r.date.isoformat()] = r.hours_worked
    return [{"date": d, "hours": h} for d, h in by_day.items()]


def _application_funnel(db: Session) -> list[dict]:
    out = []
    for st in ApplicationStatus:
        count = db.query(Application).filter(Application.status == st).count()
        out.append({"stage": st.value, "count": count})
    return out
