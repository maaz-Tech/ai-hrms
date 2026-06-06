"""Helpers shared across routers."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Employee, User, UserRole


def employee_for_user(db: Session, user: User) -> Employee:
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if emp is None:
        raise HTTPException(status_code=404, detail="No employee profile linked to this user")
    return emp


def can_view_employee(user: User, emp: Employee, db: Session) -> bool:
    """Access rule: admins see all; managers see their reports; everyone sees self."""
    if user.role in (UserRole.MANAGEMENT_ADMIN, UserRole.HR_RECRUITER):
        return True
    if emp.user_id == user.id:
        return True
    if user.role == UserRole.SENIOR_MANAGER:
        me = db.query(Employee).filter(Employee.user_id == user.id).first()
        if me and emp.manager_id == me.id:
            return True
    return False


def employee_out(emp: Employee) -> dict:
    return {
        "id": emp.id,
        "employee_code": emp.employee_code,
        "full_name": emp.full_name,
        "email": emp.email,
        "phone": emp.phone,
        "job_title": emp.job_title,
        "department_id": emp.department_id,
        "manager_id": emp.manager_id,
        "location": emp.location,
        "base_salary": emp.base_salary,
        "date_joined": emp.date_joined,
        "leave_balance": emp.leave_balance,
        "status": emp.status,
        "department_name": emp.department.name if emp.department else None,
    }
