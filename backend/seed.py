"""Seed the HRMS with demo data: 4 role accounts, ~50 employees, departments,
attendance, goals, jobs and applicants (auto-screened).

Run from the backend dir:  python seed.py
"""
import asyncio
import json
import random
from datetime import date, datetime, timedelta, timezone

from faker import Faker

from app.ai.resume_screener import screen_resume
from app.auth.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import (
    Application,
    ApplicationStatus,
    AttendanceRecord,
    Department,
    Employee,
    Goal,
    JobPosting,
    Payslip,
    PerformanceReview,
    SalaryStructure,
    User,
    UserRole,
)

fake = Faker()
random.seed(42)
Faker.seed(42)

DEPARTMENTS = ["Engineering", "Data Science", "Human Resources", "Sales", "Finance", "Design"]
TITLES = {
    "Engineering": ["Software Engineer", "Senior Engineer", "Engineering Lead"],
    "Data Science": ["ML Engineer", "Data Scientist", "AI Researcher"],
    "Human Resources": ["HR Generalist", "Recruiter", "HR Manager"],
    "Sales": ["Sales Executive", "Account Manager", "Sales Lead"],
    "Finance": ["Accountant", "Financial Analyst", "Finance Manager"],
    "Design": ["UI Designer", "UX Designer", "Design Lead"],
}

# email -> (password, role, name)
DEMO_USERS = {
    "admin@fwc.co.in": ("admin123", UserRole.MANAGEMENT_ADMIN, "Aarav Admin"),
    "manager@fwc.co.in": ("manager123", UserRole.SENIOR_MANAGER, "Maya Manager"),
    "recruiter@fwc.co.in": ("recruiter123", UserRole.HR_RECRUITER, "Riya Recruiter"),
    "employee@fwc.co.in": ("employee123", UserRole.EMPLOYEE, "Eshan Employee"),
}

SAMPLE_RESUMES = [
    "Senior Software Engineer with 7 years building React, Node.js and Python "
    "microservices on AWS. Led teams, REST and GraphQL APIs, Docker, CI/CD.",
    "ML Engineer, 4 years. TensorFlow, PyTorch, Python, NLP and computer vision. "
    "Deployed LLM fine-tuning pipelines and RAG systems on GCP.",
    "Fresh graduate, strong in Java and SQL, internship in web development with "
    "HTML, CSS, JavaScript. Eager to learn cloud and AI.",
    "Full-stack developer, 5 years. Next.js, TypeScript, PostgreSQL, MongoDB, "
    "Tailwind. Built payment integrations and OAuth auth flows.",
    "Data analyst with Power BI, Tableau, Excel and Python pandas. 3 years "
    "experience in reporting and dashboards.",
]


def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


async def main() -> None:
    reset_db()
    db = SessionLocal()

    depts = {name: Department(name=name) for name in DEPARTMENTS}
    db.add_all(depts.values())
    db.commit()

    # Role accounts + linked employee profiles
    role_employees: dict[str, Employee] = {}
    for email, (pwd, role, name) in DEMO_USERS.items():
        user = User(
            email=email,
            hashed_password=hash_password(pwd),
            full_name=name,
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        dept = depts["Human Resources"] if role != UserRole.EMPLOYEE else depts["Engineering"]
        emp = Employee(
            user_id=user.id,
            employee_code=f"EMP{1000 + user.id}",
            full_name=name,
            email=email,
            phone=fake.phone_number()[:20],
            job_title=role.value.replace("_", " ").title(),
            department_id=dept.id,
            location="Bangalore",
            date_joined=date.today() - timedelta(days=random.randint(120, 1200)),
            base_salary=random.choice([900000, 1200000, 1500000, 2000000]),
            leave_balance=random.randint(8, 24),
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)
        role_employees[role.value] = emp

    manager_emp = role_employees[UserRole.SENIOR_MANAGER.value]

    # ~50 additional employees
    employees: list[Employee] = []
    for i in range(50):
        dept_name = random.choice(DEPARTMENTS)
        name = fake.name()
        emp = Employee(
            employee_code=f"EMP{2000 + i}",
            full_name=name,
            email=fake.unique.email(),
            phone=fake.phone_number()[:20],
            job_title=random.choice(TITLES[dept_name]),
            department_id=depts[dept_name].id,
            manager_id=manager_emp.id if i % 4 == 0 else None,
            location=random.choice(["Bangalore", "Dubai", "Singapore", "Remote"]),
            date_joined=date.today() - timedelta(days=random.randint(30, 1500)),
            base_salary=random.randint(600000, 2500000),
            leave_balance=random.randint(0, 24),
            status="active",
        )
        db.add(emp)
        employees.append(emp)
    db.commit()

    all_emps = employees + list(role_employees.values())

    # Salary structures + payslips for last 2 months
    now = datetime.now(timezone.utc)
    for emp in all_emps:
        monthly = emp.base_salary / 12
        s = SalaryStructure(
            employee_id=emp.id,
            basic=round(monthly * 0.5, 2),
            hra=round(monthly * 0.3, 2),
            allowances=round(monthly * 0.2, 2),
            deductions=round(monthly * 0.1, 2),
        )
        db.add(s)
        for back in (1, 2):
            m = ((now.month - back - 1) % 12) + 1
            y = now.year if now.month - back > 0 else now.year - 1
            net = s.basic + s.hra + s.allowances - s.deductions
            db.add(
                Payslip(
                    employee_id=emp.id, month=m, year=y, basic=s.basic, hra=s.hra,
                    allowances=s.allowances, deductions=s.deductions, net_pay=round(net, 2),
                )
            )
    db.commit()

    # Attendance for last 21 days + goals + a review
    for emp in all_emps:
        for d in range(21):
            day = date.today() - timedelta(days=d)
            if day.weekday() >= 5:
                continue
            status = random.choices(
                ["present", "wfh", "leave", "absent"], weights=[70, 18, 8, 4]
            )[0]
            hours = round(random.uniform(7, 9), 1) if status in ("present", "wfh") else 0
            db.add(
                AttendanceRecord(employee_id=emp.id, date=day, status=status, hours_worked=hours)
            )
        for _ in range(random.randint(1, 3)):
            db.add(
                Goal(
                    employee_id=emp.id,
                    title=fake.catch_phrase(),
                    description=fake.sentence(),
                    progress=random.randint(0, 100),
                    status=random.choice(["not_started", "in_progress", "completed"]),
                    due_date=date.today() + timedelta(days=random.randint(10, 90)),
                )
            )
        db.add(
            PerformanceReview(
                employee_id=emp.id,
                period="Q1 2026",
                rating=round(random.uniform(2.5, 5.0), 1),
                summary="Solid contributor this quarter.",
                ai_generated=False,
            )
        )
    db.commit()

    # Jobs + auto-screened applications
    jobs_data = [
        ("Senior Full-Stack Engineer", "Engineering",
         "React, Node.js, Python, PostgreSQL, Docker, AWS, REST, GraphQL, 5+ years"),
        ("AI/ML Engineer", "Data Science",
         "Python, TensorFlow, PyTorch, NLP, LLM, RAG, GCP, 3+ years"),
        ("HR Recruiter", "Human Resources",
         "Recruitment, ATS, communication, MS Excel, 2+ years"),
    ]
    for title, dept, reqs in jobs_data:
        job = JobPosting(
            title=title, department=dept, location="Bangalore",
            description=f"We are hiring a {title}.", requirements=reqs, status="open",
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        # One tailored strong-match candidate so autonomous shortlisting is
        # visibly demonstrated, plus several generic applicants.
        strong = (
            f"Accomplished professional with 8 years of experience. Expert in "
            f"{reqs}. Delivered production systems and mentored teams."
        )
        resumes = [strong] + [random.choice(SAMPLE_RESUMES) for _ in range(random.randint(4, 6))]
        for resume in resumes:
            app = Application(
                job_id=job.id,
                candidate_name=fake.name(),
                candidate_email=fake.unique.email(),
                resume_text=resume,
            )
            result = await screen_resume(resume, job.title, job.requirements)
            app.ai_score = float(result["overall_score"])
            app.role_match_score = float(result["role_match_score"])
            app.experience_years = float(result.get("experience_years") or 0)
            app.key_skills = json.dumps(result["key_skills_found"])
            app.missing_skills = json.dumps(result["missing_skills"])
            app.recommendation = result["recommendation"]
            app.reasoning = result["reasoning"]
            app.screened_at = now
            app.status = (
                ApplicationStatus.SHORTLISTED
                if app.ai_score >= 7
                else ApplicationStatus.SCREENED
            )
            db.add(app)
        db.commit()

    db.close()
    print("✅ Seed complete.")
    print("\nDemo logins:")
    for email, (pwd, role, _) in DEMO_USERS.items():
        print(f"  {role.value:18s}  {email:22s}  {pwd}")


if __name__ == "__main__":
    asyncio.run(main())
