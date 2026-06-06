import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, is_recruiter_staff
from app.database import get_db
from app.models import Employee, Payslip, SalaryStructure, User
from app.routers.common import can_view_employee, employee_for_user
from app.schemas.hr import GeneratePayrollIn, PayslipOut

router = APIRouter(prefix="/api/payroll", tags=["payroll"])


def _structure_for(db: Session, emp: Employee) -> SalaryStructure:
    s = db.query(SalaryStructure).filter(SalaryStructure.employee_id == emp.id).first()
    if not s:
        # Derive a default structure from base salary (monthly).
        monthly = emp.base_salary / 12 if emp.base_salary > 1_00_000 else emp.base_salary
        s = SalaryStructure(
            employee_id=emp.id,
            basic=round(monthly * 0.5, 2),
            hra=round(monthly * 0.3, 2),
            allowances=round(monthly * 0.2, 2),
            deductions=round(monthly * 0.1, 2),
        )
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


@router.get("/me", response_model=list[PayslipOut])
def my_payslips(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    emp = employee_for_user(db, user)
    return (
        db.query(Payslip)
        .filter(Payslip.employee_id == emp.id)
        .order_by(Payslip.year.desc(), Payslip.month.desc())
        .all()
    )


@router.get("/employee/{employee_id}", response_model=list[PayslipOut])
def employee_payslips(
    employee_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not can_view_employee(user, emp, db):
        raise HTTPException(status_code=403, detail="Not allowed")
    return db.query(Payslip).filter(Payslip.employee_id == employee_id).all()


@router.post("/run", response_model=dict, dependencies=[Depends(is_recruiter_staff)])
def run_payroll(payload: GeneratePayrollIn, db: Session = Depends(get_db)):
    """Generate payslips for all active employees for the given month/year."""
    employees = db.query(Employee).filter(Employee.status == "active").all()
    created = 0
    for emp in employees:
        exists = (
            db.query(Payslip)
            .filter(
                Payslip.employee_id == emp.id,
                Payslip.month == payload.month,
                Payslip.year == payload.year,
            )
            .first()
        )
        if exists:
            continue
        s = _structure_for(db, emp)
        net = s.basic + s.hra + s.allowances - s.deductions
        db.add(
            Payslip(
                employee_id=emp.id,
                month=payload.month,
                year=payload.year,
                basic=s.basic,
                hra=s.hra,
                allowances=s.allowances,
                deductions=s.deductions,
                net_pay=round(net, 2),
            )
        )
        created += 1
    db.commit()
    return {"generated": created, "month": payload.month, "year": payload.year}


@router.get("/{payslip_id}/pdf")
def payslip_pdf(payslip_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    slip = db.get(Payslip, payslip_id)
    if not slip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    emp = db.get(Employee, slip.employee_id)
    if not can_view_employee(user, emp, db):
        raise HTTPException(status_code=403, detail="Not allowed")

    buf = io.BytesIO()
    try:
        from reportlab.lib.pagesizes import A4  # noqa: PLC0415
        from reportlab.pdfgen import canvas  # noqa: PLC0415

        c = canvas.Canvas(buf, pagesize=A4)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, 790, "FWC HRMS — Payslip")
        c.setFont("Helvetica", 11)
        lines = [
            f"Employee: {emp.full_name} ({emp.employee_code})",
            f"Period: {slip.month:02d}/{slip.year}",
            "",
            f"Basic:       {slip.basic:>12,.2f}",
            f"HRA:         {slip.hra:>12,.2f}",
            f"Allowances:  {slip.allowances:>12,.2f}",
            f"Deductions: -{slip.deductions:>12,.2f}",
            "-" * 30,
            f"Net Pay:     {slip.net_pay:>12,.2f}",
        ]
        y = 750
        for ln in lines:
            c.drawString(50, y, ln)
            y -= 22
        c.showPage()
        c.save()
    except ImportError:
        buf.write(
            f"Payslip {emp.full_name} {slip.month}/{slip.year} Net {slip.net_pay}".encode()
        )
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=payslip_{payslip_id}.pdf"},
    )
