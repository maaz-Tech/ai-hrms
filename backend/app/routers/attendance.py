from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, is_manager_or_admin
from app.database import get_db
from app.models import AttendanceRecord, Employee, LeaveRequest, User
from app.routers.common import can_view_employee, employee_for_user
from app.schemas.hr import AttendanceOut, LeaveCreate, LeaveOut

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.post("/check-in", response_model=AttendanceOut)
def check_in(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    emp = employee_for_user(db, user)
    today = date.today()
    rec = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.employee_id == emp.id, AttendanceRecord.date == today)
        .first()
    )
    if rec and rec.check_in:
        raise HTTPException(status_code=400, detail="Already checked in today")
    if not rec:
        rec = AttendanceRecord(employee_id=emp.id, date=today, status="present")
        db.add(rec)
    rec.check_in = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rec)
    return rec


@router.post("/check-out", response_model=AttendanceOut)
def check_out(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    emp = employee_for_user(db, user)
    today = date.today()
    rec = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.employee_id == emp.id, AttendanceRecord.date == today)
        .first()
    )
    if not rec or not rec.check_in:
        raise HTTPException(status_code=400, detail="Check in first")
    rec.check_out = datetime.now(timezone.utc)
    delta = rec.check_out - rec.check_in
    rec.hours_worked = round(delta.total_seconds() / 3600, 2)
    db.commit()
    db.refresh(rec)
    return rec


@router.get("/me", response_model=list[AttendanceOut])
def my_attendance(
    month: int | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = employee_for_user(db, user)
    return _records(db, emp.id, month, year)


@router.get("/employee/{employee_id}", response_model=list[AttendanceOut])
def employee_attendance(
    employee_id: int,
    month: int | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not can_view_employee(user, emp, db):
        raise HTTPException(status_code=403, detail="Not allowed")
    return _records(db, employee_id, month, year)


def _records(db: Session, employee_id: int, month: int | None, year: int | None):
    q = db.query(AttendanceRecord).filter(AttendanceRecord.employee_id == employee_id)
    rows = q.order_by(AttendanceRecord.date.desc()).limit(120).all()
    if month and year:
        rows = [r for r in rows if r.date.month == month and r.date.year == year]
    return rows


# ── Leave requests ────────────────────────────────────────────────────────
@router.post("/leave", response_model=LeaveOut)
def request_leave(
    payload: LeaveCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = employee_for_user(db, user)
    days = (payload.end_date - payload.start_date).days + 1
    if days < 1:
        raise HTTPException(status_code=400, detail="Invalid date range")
    # Auto-approve short leaves (per policy), else pending for manager.
    status = "approved" if days <= 3 else "pending"
    leave = LeaveRequest(
        employee_id=emp.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        leave_type=payload.leave_type,
        reason=payload.reason,
        days=days,
        status=status,
    )
    if status == "approved":
        emp.leave_balance = max(0, emp.leave_balance - days)
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave


@router.get("/leave/me", response_model=list[LeaveOut])
def my_leaves(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    emp = employee_for_user(db, user)
    return (
        db.query(LeaveRequest)
        .filter(LeaveRequest.employee_id == emp.id)
        .order_by(LeaveRequest.id.desc())
        .all()
    )


@router.get("/leave/pending", response_model=list[LeaveOut], dependencies=[Depends(is_manager_or_admin)])
def pending_leaves(db: Session = Depends(get_db)):
    return db.query(LeaveRequest).filter(LeaveRequest.status == "pending").all()


@router.post("/leave/{leave_id}/decide", response_model=LeaveOut, dependencies=[Depends(is_manager_or_admin)])
def decide_leave(leave_id: int, approve: bool, db: Session = Depends(get_db)):
    leave = db.get(LeaveRequest, leave_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    if leave.status != "pending":
        raise HTTPException(status_code=400, detail="Already decided")
    leave.status = "approved" if approve else "rejected"
    if approve:
        emp = db.get(Employee, leave.employee_id)
        emp.leave_balance = max(0, emp.leave_balance - leave.days)
    db.commit()
    db.refresh(leave)
    return leave
