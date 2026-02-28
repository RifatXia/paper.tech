import logging

from fastapi import APIRouter

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    AskScholarRequest,
    AskScholarResponse,
)
from app.mock_data import MOCK_CHAT_REPLIES, MOCK_SCHOLARS
from app.supermemory import get_chat_client

log = logging.getLogger(__name__)

router = APIRouter()

# Default user ID — will come from auth once that's wired up
DEFAULT_USER_ID = "paper-tech-user"

# System prompt injected into every chat completion
SYSTEM_PROMPT = (
    "You are a research collaboration assistant for paper.tech. "
    "You help researchers explore collaboration opportunities with the "
    "handpicked scholars in this session. You can discuss overlapping "
    "research themes, suggest project ideas, draft outreach emails, "
    "and recommend papers to read. Be specific, cite scholar names and "
    "topics, and keep responses concise."
)

SCHOLAR_SYSTEM_PROMPT = (
    "You are a research assistant for paper.tech. "
    "Answer questions about the scholar's research based on their "
    "published work and topics. Be specific and cite their work."
)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message in a multi-scholar research session.

    Routes through Supermemory Memory Router → Modal LLM when configured.
    Falls back to mock replies otherwise.
    """
    client = get_chat_client(
        user_id=DEFAULT_USER_ID,
        conversation_id=req.session_id,
    )

    if client:
        try:
            response = client.chat.completions.create(
                model="Qwen/Qwen3-4B",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": req.message},
                ],
            )
            reply = response.choices[0].message.content
            return ChatResponse(reply=reply, session_id=req.session_id)
        except Exception:
            log.exception("Supermemory/LLM call failed, falling back to mock")

    # Mock fallback
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
    """Ask a question about a specific scholar's research (RAG).

    Uses a per-scholar conversation_id so Supermemory tracks context
    separately for each scholar Q&A panel.
    """
    scholar = next((s for s in MOCK_SCHOLARS if s.scholar_id == req.scholar_id), None)
    name = scholar.name if scholar else "this scholar"

    client = get_chat_client(
        user_id=DEFAULT_USER_ID,
        conversation_id=f"scholar-{req.scholar_id}",
    )

    if client and scholar:
        try:
            context = (
                f"Scholar: {scholar.name}\n"
                f"Affiliation: {scholar.affiliation}\n"
                f"Topics: {', '.join(scholar.topics)}\n"
                f"h-index: {scholar.h_index}, papers: {scholar.paper_count}"
            )
            response = client.chat.completions.create(
                model="Qwen/Qwen3-4B",
                messages=[
                    {"role": "system", "content": f"{SCHOLAR_SYSTEM_PROMPT}\n\n{context}"},
                    {"role": "user", "content": req.question},
                ],
            )
            return AskScholarResponse(
                answer=response.choices[0].message.content,
                scholar_id=req.scholar_id,
            )
        except Exception:
            log.exception("Supermemory/LLM call failed for ask-scholar, falling back to mock")

    # Mock fallback
    return AskScholarResponse(
        answer=(
            f"Based on {name}'s published work, their research focuses on "
            f"{', '.join(scholar.topics) if scholar else 'various topics'}. "
            f"Their most cited contribution involves novel approaches to "
            f"{scholar.topics[0] if scholar and scholar.topics else 'their field'}. "
            f"Would you like to know more about a specific paper?"
        ),
        scholar_id=req.scholar_id,
    )
