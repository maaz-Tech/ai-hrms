"""Pydantic schemas for the core HRMS domains."""
from datetime import date, datetime

from pydantic import BaseModel, EmailStr


# ── Employees ─────────────────────────────────────────────────────────────
class EmployeeBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    job_title: str
    department_id: int | None = None
    manager_id: int | None = None
    location: str | None = None
    base_salary: float = 0.0


class EmployeeCreate(EmployeeBase):
    employee_code: str | None = None


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    job_title: str | None = None
    department_id: int | None = None
    manager_id: int | None = None
    location: str | None = None
    base_salary: float | None = None
    status: str | None = None


class EmployeeOut(EmployeeBase):
    id: int
    employee_code: str
    date_joined: date
    leave_balance: float
    status: str
    department_name: str | None = None

    class Config:
        from_attributes = True


class DepartmentOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ── Attendance ────────────────────────────────────────────────────────────
class AttendanceOut(BaseModel):
    id: int
    employee_id: int
    date: date
    check_in: datetime | None
    check_out: datetime | None
    status: str
    hours_worked: float

    class Config:
        from_attributes = True


class LeaveCreate(BaseModel):
    start_date: date
    end_date: date
    leave_type: str = "casual"
    reason: str = ""


class LeaveOut(BaseModel):
    id: int
    employee_id: int
    start_date: date
    end_date: date
    leave_type: str
    reason: str
    status: str
    days: float

    class Config:
        from_attributes = True


# ── Payroll ───────────────────────────────────────────────────────────────
class PayslipOut(BaseModel):
    id: int
    employee_id: int
    month: int
    year: int
    basic: float
    hra: float
    allowances: float
    deductions: float
    net_pay: float
    status: str

    class Config:
        from_attributes = True


class GeneratePayrollIn(BaseModel):
    month: int
    year: int


# ── Performance ───────────────────────────────────────────────────────────
class GoalCreate(BaseModel):
    title: str
    description: str = ""
    due_date: date | None = None
    employee_id: int | None = None  # defaults to caller


class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    progress: int | None = None


class GoalOut(BaseModel):
    id: int
    employee_id: int
    title: str
    description: str
    status: str
    progress: int
    due_date: date | None

    class Config:
        from_attributes = True


class ReviewOut(BaseModel):
    id: int
    employee_id: int
    period: str
    rating: float
    summary: str
    ai_generated: bool
    attrition_risk: str | None

    class Config:
        from_attributes = True
