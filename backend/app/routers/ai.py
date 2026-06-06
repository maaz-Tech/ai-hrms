from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai import chatbot, voice_agent
from app.ai.resume_screener import screen_resume
from app.auth.deps import get_current_user, is_recruiter_staff
from app.database import get_db
from app.models import Application, Employee, Payslip, User
from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    ScreenRequest,
    VoiceTurnRequest,
    VoiceTurnResponse,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """RAG HR assistant grounded in policies + the caller's live data."""
    personal = ""
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if emp:
        latest = (
            db.query(Payslip)
            .filter(Payslip.employee_id == emp.id)
            .order_by(Payslip.year.desc(), Payslip.month.desc())
            .first()
        )
        personal = (
            f"Name: {emp.full_name}; Leave balance: {emp.leave_balance} days; "
            f"Department: {emp.department.name if emp.department else 'N/A'}; "
            f"Latest net pay: {latest.net_pay if latest else 'N/A'}."
        )
    history = [t.model_dump() for t in payload.history]
    result = await chatbot.answer(payload.message, personal_context=personal, history=history)
    return ChatResponse(**result)


@router.post("/voice/turn", response_model=VoiceTurnResponse)
async def voice_turn(
    payload: VoiceTurnRequest,
    db: Session = Depends(get_db),
    _: User = Depends(is_recruiter_staff),
):
    """One turn of the AI voice screening interview."""
    history = [t.model_dump() for t in payload.history]
    result = await voice_agent.next_turn(payload.job_title, payload.transcript, history)

    # Persist final scorecard to the application if linked.
    if result.get("finished") and payload.application_id:
        app = db.get(Application, payload.application_id)
        if app:
            transcript = "\n".join(f"{h['role']}: {h['content']}" for h in history)
            app.voice_transcript = transcript
            sc = result.get("scorecard") or {}
            app.voice_score = sc.get("overall_score")
            db.commit()
    return VoiceTurnResponse(
        question=result.get("question", ""),
        follow_up=result.get("follow_up", False),
        answer_score=result.get("answer_score"),
        finished=result.get("finished", False),
        scorecard=result.get("scorecard"),
        ai_powered=result.get("ai_powered", False),
    )


@router.post("/screen", dependencies=[Depends(is_recruiter_staff)])
async def adhoc_screen(payload: ScreenRequest):
    """Score arbitrary resume text against a job description (no DB write)."""
    result = await screen_resume(payload.resume_text, "Role", payload.job_description)
    return result
