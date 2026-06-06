from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, is_recruiter_staff
from app.database import get_db
from app.models import Department, Employee, User, UserRole
from app.routers.common import can_view_employee, employee_for_user, employee_out
from app.schemas.hr import DepartmentOut, EmployeeCreate, EmployeeOut, EmployeeUpdate

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeOut])
def list_employees(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    q: str | None = Query(None, description="search name/email/code"),
    department_id: int | None = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
):
    query = db.query(Employee)
    # Employees only see themselves; managers see self + reports.
    if user.role == UserRole.EMPLOYEE:
        query = query.filter(Employee.user_id == user.id)
    elif user.role == UserRole.SENIOR_MANAGER:
        me = db.query(Employee).filter(Employee.user_id == user.id).first()
        ids = [me.id] if me else []
        if me:
            ids += [r.id for r in me.reports]
        query = query.filter(Employee.id.in_(ids or [-1]))

    if q:
        like = f"%{q}%"
        query = query.filter(
            (Employee.full_name.ilike(like))
            | (Employee.email.ilike(like))
            | (Employee.employee_code.ilike(like))
        )
    if department_id:
        query = query.filter(Employee.department_id == department_id)

    rows = query.order_by(Employee.full_name).offset(offset).limit(limit).all()
    return [employee_out(e) for e in rows]


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Department).order_by(Department.name).all()


@router.get("/me", response_model=EmployeeOut)
def my_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return employee_out(employee_for_user(db, user))


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not can_view_employee(user, emp, db):
        raise HTTPException(status_code=403, detail="Not allowed to view this employee")
    return employee_out(emp)


@router.post("", response_model=EmployeeOut, dependencies=[Depends(is_recruiter_staff)])
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    code = payload.employee_code or f"EMP{db.query(Employee).count() + 1001}"
    emp = Employee(
        employee_code=code,
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        job_title=payload.job_title,
        department_id=payload.department_id,
        manager_id=payload.manager_id,
        location=payload.location,
        base_salary=payload.base_salary,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return employee_out(emp)


@router.patch("/{employee_id}", response_model=EmployeeOut, dependencies=[Depends(is_recruiter_staff)])
def update_employee(employee_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(emp, field, value)
    db.commit()
    db.refresh(emp)
    return employee_out(emp)
