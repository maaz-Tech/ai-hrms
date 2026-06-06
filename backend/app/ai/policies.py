"""Company HR policy knowledge base, indexed for RAG retrieval.

In a hackathon demo this stands in for an uploaded employee handbook. Each
entry is indexed into the vector store on startup so the chatbot can ground
answers and cite sources.
"""
from app.ai import vector_store

POLICIES: list[dict] = [
    {
        "title": "Leave Policy",
        "text": (
            "Every full-time employee receives 24 paid leave days per year, "
            "accrued monthly. Casual, sick and earned leave are tracked from the "
            "same balance. Apply via the Attendance page; leaves under 3 days are "
            "auto-approved, longer leaves need manager approval."
        ),
    },
    {
        "title": "Work From Home Policy",
        "text": (
            "Employees may work from home up to 2 days per week with manager "
            "consent. Mark WFH in attendance. Client-facing roles may have "
            "on-site requirements during delivery phases."
        ),
    },
    {
        "title": "Payroll Policy",
        "text": (
            "Salaries are paid on the last working day of each month. Payslips "
            "are available on the Payroll page. Salary comprises Basic, HRA, "
            "Allowances minus statutory Deductions. Annual hikes range 20-40% "
            "based on performance."
        ),
    },
    {
        "title": "Performance Review Policy",
        "text": (
            "Reviews run quarterly. Employees set goals; managers rate on a 1-5 "
            "scale. AI-assisted summaries highlight achievements and growth areas. "
            "Ratings influence the annual hike and ESOP eligibility."
        ),
    },
    {
        "title": "ESOP & Benefits",
        "text": (
            "Employees become eligible for the Employee Stock Ownership Plan "
            "after completing 1 year of service. Benefits include health "
            "insurance and certification reimbursement on completion."
        ),
    },
    {
        "title": "Code of Conduct",
        "text": (
            "Maintain professionalism, protect confidential client data, and "
            "follow the security policy: use OAuth/SSO, never share credentials, "
            "and report incidents to HR immediately."
        ),
    },
]


def index_policies() -> None:
    for i, p in enumerate(POLICIES):
        vector_store.index_document(
            point_id=1000 + i,
            text=f"{p['title']}. {p['text']}",
            payload={"title": p["title"], "text": p["text"], "kind": "policy"},
        )
