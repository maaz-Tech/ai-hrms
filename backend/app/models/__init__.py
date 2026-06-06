"""SQLAlchemy ORM models for the HRMS.

Importing this package registers every model on the shared ``Base`` so that
``Base.metadata.create_all()`` (and Alembic autogenerate) sees them all.
"""
from app.models.user import User, UserRole
from app.models.employee import Department, Employee
from app.models.attendance import AttendanceRecord, LeaveRequest
from app.models.payroll import Payslip, SalaryStructure
from app.models.performance import Goal, PerformanceReview
from app.models.recruitment import Application, ApplicationStatus, JobPosting

__all__ = [
    "User",
    "UserRole",
    "Department",
    "Employee",
    "AttendanceRecord",
    "LeaveRequest",
    "Payslip",
    "SalaryStructure",
    "Goal",
    "PerformanceReview",
    "Application",
    "ApplicationStatus",
    "JobPosting",
]
