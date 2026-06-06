from datetime import date as date_cls
from datetime import datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    # not_started | in_progress | completed
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    due_date: Mapped[date_cls | None] = mapped_column(Date, nullable=True)

    employee = relationship("Employee")


class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"), index=True
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id"), nullable=True
    )
    period: Mapped[str] = mapped_column(String(40))  # e.g. "Q1 2026"
    rating: Mapped[float] = mapped_column(Float, default=0.0)  # 1-5
    summary: Mapped[str] = mapped_column(Text, default="")
    ai_generated: Mapped[bool] = mapped_column(default=False)
    attrition_risk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    employee = relationship("Employee", foreign_keys=[employee_id])
