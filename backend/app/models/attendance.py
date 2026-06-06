from datetime import date as date_cls
from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"), index=True
    )
    date: Mapped[date_cls] = mapped_column(Date, index=True)
    check_in: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    check_out: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # present | absent | leave | wfh | holiday
    status: Mapped[str] = mapped_column(String(20), default="present")
    hours_worked: Mapped[float] = mapped_column(default=0.0)

    employee = relationship("Employee")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"), index=True
    )
    start_date: Mapped[date_cls] = mapped_column(Date)
    end_date: Mapped[date_cls] = mapped_column(Date)
    leave_type: Mapped[str] = mapped_column(String(40), default="casual")
    reason: Mapped[str] = mapped_column(String(500), default="")
    # pending | approved | rejected
    status: Mapped[str] = mapped_column(String(20), default="pending")
    days: Mapped[float] = mapped_column(default=1.0)

    employee = relationship("Employee")
