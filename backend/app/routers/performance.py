from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai import insights
from app.auth.deps import get_current_user, is_manager_or_admin
from app.database import get_db
from app.models import (
    AttendanceRecord,
    Employee,
    Goal,
    PerformanceReview,
    User,
    UserRole,
)
from app.routers.common import can_view_employee, employee_for_user
from app.schemas.ai import InsightResponse
from app.schemas.hr import GoalCreate, GoalOut, GoalUpdate, ReviewOut

router = APIRouter(prefix="/api/performance", tags=["performance"])


# ── Goals ─────────────────────────────────────────────────────────────────
@router.get("/goals/me", response_model=list[GoalOut])
def my_goals(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    emp = employee_for_user(db, user)
    return db.query(Goal).filter(Goal.employee_id == emp.id).order_by(Goal.id.desc()).all()


@router.get("/goals/employee/{employee_id}", response_model=list[GoalOut])
def employee_goals(
    employee_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    emp = db.get(Employee, employee_id)
    if not emp or not can_view_employee(user, emp, db):
        raise HTTPException(status_code=403, detail="Not allowed")
    return db.query(Goal).filter(Goal.employee_id == employee_id).all()


@router.post("/goals", response_model=GoalOut)
def create_goal(
    payload: GoalCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    emp = employee_for_user(db, user)
    target = payload.employee_id or emp.id
    if target != emp.id and user.role == UserRole.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Cannot set goals for others")
    goal = Goal(
        employee_id=target,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.patch("/goals/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: int,
    payload: GoalUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    goal = db.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    emp = employee_for_user(db, user)
    if goal.employee_id != emp.id and user.role == UserRole.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Not allowed")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(goal, f, v)
    if goal.progress >= 100:
        goal.status = "completed"
    db.commit()
    db.refresh(goal)
    return goal


# ── Reviews & AI insight ──────────────────────────────────────────────────
@router.get("/reviews/employee/{employee_id}", response_model=list[ReviewOut])
def employee_reviews(
    employee_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    emp = db.get(Employee, employee_id)
    if not emp or not can_view_employee(user, emp, db):
        raise HTTPException(status_code=403, detail="Not allowed")
    return db.query(PerformanceReview).filter(PerformanceReview.employee_id == employee_id).all()


def _build_signals(db: Session, emp: Employee) -> dict:
    goals = db.query(Goal).filter(Goal.employee_id == emp.id).all()
    avg_progress = sum(g.progress for g in goals) / len(goals) if goals else 0
    att = db.query(AttendanceRecord).filter(AttendanceRecord.employee_id == emp.id).all()
    present = [a for a in att if a.status in ("present", "wfh")]
    attendance_rate = (len(present) / len(att)) if att else 1.0
    tenure_months = max(1, (date.today() - emp.date_joined).days // 30)
    last_review = (
        db.query(PerformanceReview)
        .filter(PerformanceReview.employee_id == emp.id)
        .order_by(PerformanceReview.id.desc())
        .first()
    )
    return {
        "name": emp.full_name,
        "job_title": emp.job_title,
        "avg_goal_progress": round(avg_progress, 1),
        "attendance_rate": round(attendance_rate, 2),
        "tenure_months": tenure_months,
        "recent_rating": last_review.rating if last_review else 3.0,
        "leave_balance": emp.leave_balance,
        "open_goals": sum(1 for g in goals if g.status != "completed"),
    }


@router.post(
    "/insight/{employee_id}",
    response_model=InsightResponse,
    dependencies=[Depends(is_manager_or_admin)],
)
async def generate_review_insight(
    employee_id: int, persist: bool = False, db: Session = Depends(get_db)
):
    """AI-generated performance summary + attrition risk for a managed employee."""
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    signals = _build_signals(db, emp)
    result = await insights.generate_insight(signals)
    if persist:
        db.add(
            PerformanceReview(
                employee_id=emp.id,
                period=f"{date.today():%b %Y}",
                rating=result["rating"],
                summary=result["summary"],
                ai_generated=True,
                attrition_risk=result["attrition_risk"],
            )
        )
        db.commit()
    return result
