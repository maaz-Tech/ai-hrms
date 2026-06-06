from pydantic import BaseModel


class ChatTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatTurn] = []


class ChatResponse(BaseModel):
    reply: str
    sources: list[str] = []
    ai_powered: bool = True


class VoiceTurnRequest(BaseModel):
    application_id: int | None = None
    job_title: str = "the role"
    transcript: str = ""           # what the candidate just said
    history: list[ChatTurn] = []   # prior Q&A turns


class VoiceTurnResponse(BaseModel):
    question: str               # next question to ask (TTS this on the client)
    follow_up: bool
    answer_score: float | None  # score for the answer just given
    finished: bool = False
    scorecard: dict | None = None
    ai_powered: bool = True


class ScreenRequest(BaseModel):
    """Ad-hoc screening of arbitrary resume text against a job description."""

    resume_text: str
    job_description: str


class InsightResponse(BaseModel):
    summary: str
    highlights: list[str]
    attrition_risk: str
    rating: float
    ai_powered: bool = True
