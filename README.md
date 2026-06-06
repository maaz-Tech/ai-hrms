# 🤖 FWC AI-Powered HRMS

> **Hackathon theme:** *Build the Future of HR Management with AI-Powered Solutions.*
> A next-generation Human Resource Management System that uses AI to streamline and
> automate HR operations — from **autonomous résumé screening** to **AI voice
> interviews**, an **RAG HR assistant**, and **AI performance & attrition insights**.

Built with **React + FastAPI + Google Gemini**. Runs end-to-end on free / open-source
tooling — and even **with no API keys at all** (every AI feature degrades to a
deterministic fallback so reviewers can run it instantly).

---

## ✨ The 4 AI features

| # | Feature | What it does | Where |
|---|---------|--------------|-------|
| 1 | **Autonomous résumé screening** | Scores & ranks every applicant against the job with **no human intervention**; auto-shortlists above a threshold. Gemini structured-JSON scoring blended with semantic similarity. | `backend/app/ai/resume_screener.py`, Recruitment page |
| 2 | **AI voice screening agent** | Conducts a spoken interview: asks questions aloud (TTS), listens (STT via Web Speech API), scores answers, produces a scorecard. | `backend/app/ai/voice_agent.py`, Voice Screening page |
| 3 | **RAG HR assistant** | Chatbot answering policy + personal questions ("how many leaves do I have?"), grounded in an indexed HR knowledge base with cited sources. | `backend/app/ai/chatbot.py`, HR Assistant page |
| 4 | **AI performance insights** | Generates a review summary, highlights and an **attrition-risk** flag from each employee's goals/attendance/tenure. | `backend/app/ai/insights.py`, Performance page |

## 🏛️ Core HRMS (the brief's requirements)

- **Employee data management** — directory, departments, manager hierarchy, CRUD
- **Attendance** — check in/out, monthly records, leave requests + approvals
- **Payroll** — salary structures, monthly payslip generation, **PDF download**
- **Performance** — goals with progress tracking, quarterly reviews
- **Multi-role login** with tailored access: **Management Admin · Senior Manager · HR Recruiter · Employee**
- **Personalized dashboards** — each user sees their own activity; staff also see **company-wide** dashboards
- **Responsive** web + mobile UI, clean UX
- **Scalability** — stateless JWT, indexed/paginated queries, async API (see `docs/architecture.md`)

---

## 🚀 Quick start

### Prerequisites
- Python 3.10+ and Node 18+

### 1. Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-core.txt      # or requirements.txt for full ML stack
cp .env.example .env                       # optional: add GEMINI_API_KEY for real AI
python seed.py                             # creates demo data + 4 role accounts
uvicorn app.main:app --reload              # → http://localhost:8000  (docs at /docs)
```

### 2. Frontend (new terminal)
```bash
cd frontend
npm install
npm run dev                                # → http://localhost:5173
```

Open **http://localhost:5173** and sign in with a demo account below
(the login page has one-click buttons for each role).

### 🔑 Demo logins
| Role | Email | Password |
|------|-------|----------|
| Management Admin | `admin@fwc.co.in` | `admin123` |
| Senior Manager | `manager@fwc.co.in` | `manager123` |
| HR Recruiter | `recruiter@fwc.co.in` | `recruiter123` |
| Employee | `employee@fwc.co.in` | `employee123` |

### Enabling full Gemini AI (optional)
Get a free key at <https://aistudio.google.com/apikey>, put it in `backend/.env`:
```
GEMINI_API_KEY=your_key_here
```
Restart the backend. `GET /health` reports `"ai_enabled": true`, and the UI shows a
**✨ AI (Gemini)** badge instead of **⚙ Heuristic mode**. Without a key, everything
still works via heuristics.

---

## 🧪 Tests
```bash
cd backend && source .venv/bin/activate && pytest -q
```
Covers login, RBAC enforcement (403 for an employee on a recruiter route) and that
résumé screening ranks a strong match above a weak one.

## 🛠️ Tech stack
**Frontend:** React 18, Vite, TailwindCSS, React Router, Recharts, Axios, Web Speech API
**Backend:** FastAPI, SQLAlchemy 2, Pydantic v2, python-jose (JWT), passlib/bcrypt, ReportLab (PDF), pypdf
**AI:** Google Gemini (`google-genai`), sentence-transformers embeddings, cosine vector search (Qdrant-ready)
**DB:** SQLite (dev) / PostgreSQL (prod via `DATABASE_URL`)

## 📦 Deployment (free tiers)
- **Frontend** → Vercel / Netlify (`npm run build` → `dist/`)
- **Backend** → Render / Railway (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`)
- **DB** → Neon / Supabase Postgres — set `DATABASE_URL`
- **Vectors** → Qdrant Cloud free tier — set `QDRANT_URL` / `QDRANT_API_KEY`
- Set `CORS_ORIGINS` to your deployed frontend URL.

## 📁 Project structure
```
hrms-ai/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app, routers, lifespan
│   │   ├── config.py          env settings
│   │   ├── database.py        SQLAlchemy engine/session
│   │   ├── models/            ORM models
│   │   ├── schemas/           Pydantic schemas
│   │   ├── auth/              JWT security + RBAC dependencies
│   │   ├── routers/           API endpoints per domain
│   │   └── ai/                Gemini client + the 4 AI features
│   ├── seed.py                demo data generator
│   └── tests/                 pytest smoke suite
├── frontend/
│   └── src/
│       ├── api/ auth/ components/ pages/
│       └── App.jsx            role-aware routing
└── docs/
    ├── architecture.md        system diagram + design notes
    └── api.md                 endpoint reference
```

## 📋 Hackathon checklist
- [x] Core HRMS (employee, attendance, payroll, performance)
- [x] AI résumé screening with **no human intervention**
- [x] AI conversation **and voice** interaction for screening
- [x] 4 tailored-access roles + personalized & company-wide dashboards
- [x] ≥ 4 AI features · open-source/free tiers only · mobile responsive
- [x] Documented code · README · architecture diagram · API docs
