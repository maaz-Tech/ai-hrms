# Architecture

## System overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              CLIENT (Browser)                              │
│   React 18 + Vite + TailwindCSS + Recharts + React Router                  │
│   • Role-aware routing & nav (4 roles)                                     │
│   • Dashboards · Employees · Attendance · Payroll · Performance            │
│   • Recruitment (AI screening) · Voice Screening (Web Speech API)          │
│   • HR Assistant chatbot                                                    │
└───────────────────────────────┬────────────────────────────────────────────┘
                                 │  HTTPS · JWT Bearer token
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          API  (FastAPI · Python)                           │
│                                                                            │
│  Routers:  /api/auth   /api/employees   /api/attendance   /api/payroll     │
│            /api/performance   /api/recruitment   /api/dashboard   /api/ai   │
│                                                                            │
│  Auth:   OAuth2 password flow → JWT (python-jose) · bcrypt hashing         │
│  RBAC:   require_roles() dependency guards per route                       │
│                                                                            │
│  AI layer (app/ai):                                                        │
│    • gemini_client   async Gemini wrapper (JSON + text), key-safe          │
│    • resume_screener autonomous scoring  ← AI feature #1                   │
│    • voice_agent     turn-by-turn interview  ← AI feature #2               │
│    • chatbot         RAG over policies      ← AI feature #3                │
│    • insights        perf summary + attrition ← AI feature #4              │
│    • vector_store    embeddings + cosine search                            │
│    • policies        HR knowledge base (indexed at startup)                │
└──────────────┬─────────────────────────┬──────────────────┬────────────────┘
               │                         │                  │
               ▼                         ▼                  ▼
       ┌───────────────┐        ┌────────────────┐   ┌──────────────┐
       │  PostgreSQL   │        │  Vector store  │   │  Gemini API  │
       │ (SQLAlchemy)  │        │  embeddings +  │   │  (optional)  │
       │  SQLite in    │        │  cosine index  │   │  free tier   │
       │  dev          │        │  (Qdrant-ready)│   │              │
       └───────────────┘        └────────────────┘   └──────────────┘
```

## Graceful degradation

Every AI feature has a deterministic fallback so the system runs end-to-end
**with zero API keys**:

| Capability        | With `GEMINI_API_KEY`        | Without (default)                    |
|-------------------|------------------------------|--------------------------------------|
| Resume screening  | Gemini structured JSON score | keyword coverage + semantic similarity |
| Voice agent       | adaptive Gemini questions    | scripted competency question bank    |
| HR chatbot        | Gemini grounded in RAG       | extractive answer from top policy    |
| Perf insights     | Gemini narrative review      | rules-based summary + risk model     |
| Embeddings        | sentence-transformers        | deterministic hashing embedder       |

## Data model (core tables)

`users` ─1:1─ `employees` ─*─ `departments`
`employees` ─1:*─ `attendance_records`, `leave_requests`, `goals`,
`performance_reviews`, `payslips`, `salary_structures`
`job_postings` ─1:*─ `applications` (carries AI screening output)

## Scalability notes (5,000+ employees)

- **Stateless JWT auth** → API scales horizontally behind a load balancer.
- **Indexed columns** on `org`/`employee_id`/`role`/foreign keys.
- **Pagination** (`limit`/`offset`) on all list endpoints.
- **Async** FastAPI endpoints + `pool_pre_ping` connection pooling.
- **Batch AI** screening with bounded concurrency (`asyncio.gather`, size 10).
- Vector search abstracted behind `vector_store` → swap the in-memory index
  for **Qdrant Cloud** by pointing `QDRANT_URL`/`QDRANT_API_KEY` at it.
