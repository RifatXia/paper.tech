"""
Chat router — auto-routes messages through the Decider.

Flow:
  1. User sends POST /api/chat
  2. Decider classifies → DEEP_ANALYSIS / RESEARCH_QUERY / GENERAL_CHAT
  3. Route to pipeline
  4. History is stored via existing supermemory.py (short-term + long-term)
  5. Return response with intent metadata
"""

import logging

from fastapi import APIRouter

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    AskScholarRequest,
    AskScholarResponse,
)
from app.mock_data import MOCK_CHAT_REPLIES, MOCK_SCHOLARS
<<<<<<< Updated upstream
from app.supermemory import call_llm
from app.vectordb import list_all_scholars
=======
from app.supermemory import (
    call_llm,
    get_session_history,
    append_to_history,
)
from app.services.decider import Intent, classify, extract_arxiv_id
from app.services.research_runner import run_deep_analysis, run_research_query
>>>>>>> Stashed changes

log = logging.getLogger(__name__)
router = APIRouter()

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


def _find_scholar(scholar_id: str):
    """Look up a scholar by ID — try Actian DB first, then mock data."""
    db_scholars = list_all_scholars(limit=500)
    if db_scholars:
        for s in db_scholars:
            if s.get("scholar_id") == scholar_id:
                return s
    # Fallback to mock
    for s in MOCK_SCHOLARS:
        if s.scholar_id == scholar_id:
            return {"name": s.name, "affiliation": s.affiliation,
                    "topics": s.topics, "h_index": s.h_index,
                    "paper_count": s.paper_count}
    return None


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Smart chat — auto-detects ArXiv URLs, research queries, or general chat."""

    # Get recent history for context-aware classification
    recent = get_session_history(req.session_id)
    intent, meta = classify(req.message, recent)

    log.info(f"Chat intent={intent.value} session={req.session_id} meta={meta}")

    try:
        if intent == Intent.DEEP_ANALYSIS:
            reply = await _handle_deep_analysis(req, meta)

        elif intent == Intent.RESEARCH_QUERY:
            reply = await _handle_research_query(req, meta)

        else:
            reply = await _handle_general_chat(req, meta)

    except Exception:
        log.exception(f"Pipeline failed: intent={intent.value}")
        reply = (
            f"⚠️ Something went wrong during {intent.value.replace('_', ' ')}. "
            "Please try again or rephrase your request."
        )

    # Store the exchange in history (short-term + Supermemory long-term)
    # For general chat this is already done inside call_llm(),
    # but for deep_analysis/research_query we store manually.
    if intent != Intent.GENERAL_CHAT:
        append_to_history(req.session_id, req.message, reply[:2000])

    return ChatResponse(
        reply=reply,
        session_id=req.session_id,
        intent=intent.value,
        arxiv_id=meta.get("arxiv_id"),
    )


# ── Pipeline handlers ──────────────────────────────────────────

async def _handle_deep_analysis(req: ChatRequest, meta: dict) -> str:
    """Deep paper analysis for an ArXiv paper."""

    arxiv_id = meta.get("arxiv_id")
    if not arxiv_id:
        return (
            "🔍 I'd love to do a deep paper analysis! Please share an ArXiv link or ID.\n\n"
            "Examples:\n"
            "• `https://arxiv.org/abs/2010.11929`\n"
            "• `2010.11929`\n"
            "• `Analyze this paper: https://arxiv.org/abs/2312.12345`"
        )

    try:
        analysis = await run_deep_analysis(arxiv_id)
        return (
            f"📄 **Deep Analysis** of [`{arxiv_id}`](https://arxiv.org/abs/{arxiv_id})\n\n"
            f"---\n\n{analysis}"
        )
    except Exception as e:
        log.exception(f"Deep analysis failed: {arxiv_id}")
        return (
            f"❌ Deep analysis failed for `{arxiv_id}`: {str(e)[:200]}\n\n"
            "Check that the ArXiv ID is valid and that Modal + OpenAI are configured."
        )


async def _handle_research_query(req: ChatRequest, meta: dict) -> str:
    """Multi-agent research pipeline."""

    try:
        result = await run_research_query(
            query=req.message,
            topic=meta.get("topic", req.message),
        )
        return f"🔬 **Research Results**\n\n---\n\n{result}"
    except Exception as e:
        log.exception("Research query failed")
        return f"❌ Research query failed: {str(e)[:200]}\n\nTry rephrasing or narrowing your question."


async def _handle_general_chat(req: ChatRequest, meta: dict) -> str:
    """General chat via existing Supermemory + Modal LLM flow."""

    # If decider flagged "ask for paper URL", give a helpful prompt
    if meta.get("note") == "ask_for_paper_url":
        return (
            "I can do a deep section-by-section analysis of any paper! "
            "Just paste an ArXiv link or ID, like:\n\n"
            "• `https://arxiv.org/abs/2010.11929`\n"
            "• `2312.12345`"
        )

    try:
        reply = await call_llm(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": req.message},
            ],
            session_id=req.session_id,
        )
        if reply:
            return reply
    except Exception:
        log.exception("LLM call failed, falling back to mock")

    # Mock fallback
    msg_lower = req.message.lower()
    if "project" in msg_lower or "idea" in msg_lower or "collaborate" in msg_lower:
        return MOCK_CHAT_REPLIES["project"]
    elif "email" in msg_lower or "reach out" in msg_lower or "draft" in msg_lower:
        return MOCK_CHAT_REPLIES["email"]
    else:
        return MOCK_CHAT_REPLIES["default"]


# ── Scholar Q&A (unchanged) ────────────────────────────────────

@router.post("/ask-scholar", response_model=AskScholarResponse)
async def ask_scholar(req: AskScholarRequest):
    """Ask a question about a specific scholar's research (RAG)."""
    scholar = _find_scholar(req.scholar_id)
    name = scholar.get("name", "this scholar") if scholar else "this scholar"
    topics = scholar.get("topics", []) if scholar else []

    if scholar:
        try:
            context = (
                f"Scholar: {name}\n"
                f"Affiliation: {scholar.get('affiliation', '')}\n"
                f"Topics: {', '.join(topics)}\n"
                f"h-index: {scholar.get('h_index', 0)}, papers: {scholar.get('paper_count', 0)}"
            )
            reply = await call_llm(
                messages=[
                    {"role": "system", "content": f"{SCHOLAR_SYSTEM_PROMPT}\n\n{context}"},
                    {"role": "user", "content": req.question},
                ],
                session_id=f"scholar-{req.scholar_id}",
            )
            if reply:
                return AskScholarResponse(answer=reply, scholar_id=req.scholar_id)
        except Exception:
            log.exception("LLM call failed for ask-scholar")

    return AskScholarResponse(
        answer=(
            f"Based on {name}'s published work, their research focuses on "
            f"{', '.join(topics) if topics else 'various topics'}. "
            f"Their most cited contribution involves novel approaches to "
            f"{topics[0] if topics else 'their field'}. "
            f"Would you like to know more about a specific paper?"
        ),
        scholar_id=req.scholar_id,
    )