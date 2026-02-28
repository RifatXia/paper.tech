from fastapi import APIRouter

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    AskScholarRequest,
    AskScholarResponse,
)
from app.mock_data import MOCK_CHAT_REPLIES, MOCK_SCHOLARS

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message in a multi-scholar research session."""
    # TODO: Replace with Supermemory proxy → Modal LLM pipeline:
    #   1. Route through Supermemory with session_id for context injection
    #   2. Supermemory proxies to Modal LLM endpoint
    #   3. Return LLM response
    msg_lower = req.message.lower()
    if "project" in msg_lower or "idea" in msg_lower or "collaborate" in msg_lower:
        reply = MOCK_CHAT_REPLIES["project"]
    elif "email" in msg_lower or "reach out" in msg_lower or "draft" in msg_lower:
        reply = MOCK_CHAT_REPLIES["email"]
    else:
        reply = MOCK_CHAT_REPLIES["default"]
    return ChatResponse(reply=reply, session_id=req.session_id)


@router.post("/ask-scholar", response_model=AskScholarResponse)
async def ask_scholar(req: AskScholarRequest):
    """Ask a question about a specific scholar's research (RAG)."""
    # TODO: Replace with per-scholar RAG:
    #   1. Retrieve scholar's papers from Actian VectorAI DB
    #   2. Embed question, find relevant chunks
    #   3. Generate answer via Modal LLM with retrieved context
    scholar = next((s for s in MOCK_SCHOLARS if s.scholar_id == req.scholar_id), None)
    name = scholar.name if scholar else "this scholar"
    return AskScholarResponse(
        answer=f"Based on {name}'s published work, their research focuses on {', '.join(scholar.topics) if scholar else 'various topics'}. Their most cited contribution involves novel approaches to {scholar.topics[0] if scholar and scholar.topics else 'their field'}. Would you like to know more about a specific paper?",
        scholar_id=req.scholar_id,
    )
