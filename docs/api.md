# API Reference

Interactive OpenAPI docs are auto-generated at **`http://localhost:8000/docs`**
(Swagger UI) and **`/redoc`**. This file summarises the key endpoints.

All routes except `/api/auth/login`, `/health` and `/` require a
`Authorization: Bearer <token>` header.

## Auth
| Method | Path | Roles | Description |
|---|---|---|---|
| POST | `/api/auth/login` | public | OAuth2 password login → JWT |
| GET  | `/api/auth/me` | any | current user |
| POST | `/api/auth/register` | admin | create a user |

## Employees
| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/api/employees` | scoped* | list/search employees |
| GET | `/api/employees/me` | any | own profile |
| GET | `/api/employees/{id}` | scoped* | one employee |
| POST | `/api/employees` | staff | create |
| PATCH | `/api/employees/{id}` | staff | update |
| GET | `/api/employees/departments` | any | departments |

\* Employees see only themselves; managers see self + reports; admins/recruiters see all.

## Attendance
| Method | Path | Roles | Description |
|---|---|---|---|
| POST | `/api/attendance/check-in` / `check-out` | any | clock in/out |
| GET | `/api/attendance/me` | any | own records |
| POST | `/api/attendance/leave` | any | request leave (≤3d auto-approve) |
| GET | `/api/attendance/leave/pending` | manager+ | pending approvals |
| POST | `/api/attendance/leave/{id}/decide?approve=` | manager+ | approve/reject |

## Payroll
| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/api/payroll/me` | any | own payslips |
| POST | `/api/payroll/run` | staff | generate payslips for a month |
| GET | `/api/payroll/{id}/pdf` | scoped | download payslip PDF |

## Performance
| Method | Path | Roles | Description |
|---|---|---|---|
| GET/POST/PATCH | `/api/performance/goals…` | any | manage goals |
| POST | `/api/performance/insight/{employee_id}` | manager+ | **AI** review + attrition risk |

## Recruitment
| Method | Path | Roles | Description |
|---|---|---|---|
| GET/POST | `/api/recruitment/jobs` | staff | job postings |
| GET | `/api/recruitment/jobs/{id}/applications` | staff | ranked applicants |
| POST | `/api/recruitment/jobs/{id}/apply` | any | apply (JSON) → **auto-screened** |
| POST | `/api/recruitment/jobs/{id}/upload` | staff | upload résumé file → **auto-screened** |
| POST | `/api/recruitment/jobs/{id}/rescreen` | staff | batch re-screen all |

## AI
| Method | Path | Roles | Description |
|---|---|---|---|
| POST | `/api/ai/chat` | any | RAG HR assistant |
| POST | `/api/ai/voice/turn` | staff | one voice-interview turn |
| POST | `/api/ai/screen` | staff | ad-hoc resume vs JD scoring |

## Dashboard
| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/api/dashboard/me` | any | personal activity dashboard |
| GET | `/api/dashboard/company` | staff | company-wide metrics |

## Example: login + screen a résumé
```bash
TOKEN=$(curl -s -X POST localhost:8000/api/auth/login \
  -d "username=recruiter@fwc.co.in&password=recruiter123" | jq -r .access_token)

curl -s -X POST localhost:8000/api/ai/screen \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"resume_text":"Python, React, AWS, 6 years","job_description":"Python, React, AWS"}'
```
