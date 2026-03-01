import asyncio
import logging
import random

from fastapi import APIRouter

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    AskScholarRequest,
    AskScholarResponse,
)
from app.mock_data import MOCK_SCHOLARS, SCHOLAR_BY_ID
from app.supermemory import call_llm

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

# ---------------------------------------------------------------------------
# Session-aware scholar storage for smart chat
# ---------------------------------------------------------------------------
_session_scholars: dict[str, list[str]] = {}  # session_id → scholar_ids


def register_session(session_id: str, scholar_ids: list[str]):
    """Called from handpick router to register scholars for a session."""
    _session_scholars[session_id] = scholar_ids


def _get_session_scholars(session_id: str):
    """Get ScholarCard objects for a session."""
    ids = _session_scholars.get(session_id, [])
    return [SCHOLAR_BY_ID[sid] for sid in ids if sid in SCHOLAR_BY_ID]


def _smart_reply(message: str, session_id: str) -> str:
    """Generate an intelligent mock reply based on the question and session scholars."""
    scholars = _get_session_scholars(session_id)
    msg = message.lower()

    if not scholars:
        return (
            "I don't have any scholars loaded in this session yet. "
            "Please go back and handpick some scholars first, then start a new session."
        )

    names = [s.name for s in scholars]
    names_str = ", ".join(names[:-1]) + f" and {names[-1]}" if len(names) > 1 else names[0]

    # --- "What specialties / expertise / fields" ---
    if any(kw in msg for kw in ["specialt", "expertise", "field", "focus", "work on", "research area", "what do they", "what does"]):
        lines = [f"Great question! Here's a breakdown of each scholar's specialization:\n"]
        for s in scholars:
            topics_str = ", ".join(s.topics[:3])
            lines.append(
                f"- **{s.name}** ({s.affiliation}): Specializes in **{s.topics[0]}**, "
                f"with additional expertise in {topics_str}. "
                f"h-index: {s.h_index}, {s.paper_count} publications."
            )
        lines.append(f"\nTogether, this group covers a complementary range of expertise. Would you like me to identify specific collaboration opportunities between them?")
        return "\n".join(lines)

    # --- "Who is more specialized / better / stronger" ---
    if any(kw in msg for kw in ["who is more", "who would be better", "who is the best", "who is stronger", "most specialized", "most experienced", "who should i", "who has more"]):
        # Find what topic they're asking about
        topic_match = None
        for s in scholars:
            for t in s.topics:
                if t.lower() in msg:
                    topic_match = t
                    break

        if topic_match:
            relevant = [(s, s.h_index) for s in scholars if any(topic_match.lower() in t.lower() for t in s.topics)]
            relevant.sort(key=lambda x: x[1], reverse=True)
            if relevant:
                best = relevant[0][0]
                return (
                    f"For **{topic_match}**, I'd recommend **{best.name}** ({best.affiliation}). "
                    f"They have an h-index of {best.h_index} with {best.paper_count} publications, "
                    f"and their primary research topics include {', '.join(best.topics[:3])}.\n\n"
                    f"{'Among the other scholars, ' + relevant[1][0].name + ' also has relevant experience in this area.' if len(relevant) > 1 else ''}"
                )

        # General "who is best" — rank by h-index
        ranked = sorted(scholars, key=lambda s: s.h_index, reverse=True)
        top = ranked[0]
        return (
            f"Based on overall research impact, **{top.name}** has the highest h-index ({top.h_index}) "
            f"with {top.paper_count} publications from {top.affiliation}. Their core expertise is in "
            f"{', '.join(top.topics[:2])}.\n\n"
            f"However, the 'best' choice depends on your specific research question. "
            f"For example:\n"
            + "\n".join(f"- **{s.name}**: Best for {s.topics[0]}" for s in ranked[:4])
            + "\n\nWhat specific topic are you most interested in collaborating on?"
        )

    # --- "Good choice / recommend / suggest" ---
    if any(kw in msg for kw in ["good choice", "recommend", "suggest", "pick", "which one", "who do you"]):
        # Find topic keywords in the message
        found_topics = []
        for s in scholars:
            for t in s.topics:
                if any(word in msg for word in t.lower().split() if len(word) > 3):
                    found_topics.append((s, t))

        if found_topics:
            s, t = found_topics[0]
            others = [x for x in found_topics[1:] if x[0].scholar_id != s.scholar_id]
            reply = (
                f"I'd strongly recommend **{s.name}** for this direction. Their work on "
                f"**{t}** at {s.affiliation} is directly relevant, and with an h-index of {s.h_index}, "
                f"they have significant influence in the field."
            )
            if others:
                reply += f"\n\n**{others[0][0].name}** would also be a great complementary collaborator — they bring expertise in {others[0][1]}."
            return reply

        # General recommendation
        top2 = sorted(scholars, key=lambda s: s.score, reverse=True)[:2]
        return (
            f"Based on the match scores, I'd recommend starting with:\n\n"
            f"1. **{top2[0].name}** (score: {top2[0].score:.0%}) — Expert in {', '.join(top2[0].topics[:2])}\n"
            + (f"2. **{top2[1].name}** (score: {top2[1].score:.0%}) — Expert in {', '.join(top2[1].topics[:2])}\n" if len(top2) > 1 else "")
            + f"\nThey have complementary skills that could lead to impactful research. Shall I suggest specific project ideas?"
        )

    # --- "Compare" ---
    if any(kw in msg for kw in ["compare", "difference", "versus", "vs", "how do they differ"]):
        if len(scholars) >= 2:
            s1, s2 = scholars[0], scholars[1]
            return (
                f"Here's a comparison between **{s1.name}** and **{s2.name}**:\n\n"
                f"| | {s1.name} | {s2.name} |\n"
                f"|---|---|---|\n"
                f"| **Affiliation** | {s1.affiliation} | {s2.affiliation} |\n"
                f"| **h-index** | {s1.h_index} | {s2.h_index} |\n"
                f"| **Papers** | {s1.paper_count} | {s2.paper_count} |\n"
                f"| **Focus** | {', '.join(s1.topics[:2])} | {', '.join(s2.topics[:2])} |\n"
                f"| **Match Score** | {s1.score:.0%} | {s2.score:.0%} |\n\n"
                f"**{s1.name}** brings deeper expertise in {s1.topics[0]}, while "
                f"**{s2.name}** complements with {s2.topics[0]}. "
                f"Together, they cover both {s1.topics[0]} and {s2.topics[0]}."
            )

    # --- "Project idea / collaborate / work together" ---
    if any(kw in msg for kw in ["project", "idea", "collaborate", "work together", "research direction", "paper together"]):
        if len(scholars) >= 2:
            all_topics = []
            for s in scholars:
                all_topics.extend(s.topics[:2])
            return (
                f"Based on the combined expertise of {names_str}, here are promising collaboration directions:\n\n"
                f"1. **Cross-domain {scholars[0].topics[0]} + {scholars[1].topics[0]}** — "
                f"Combine {scholars[0].name}'s work on {scholars[0].topics[0]} with "
                f"{scholars[1].name}'s expertise in {scholars[1].topics[0]} to create a novel approach "
                f"that bridges both areas.\n\n"
                f"2. **Benchmark & Evaluation** — Jointly develop a comprehensive benchmark that "
                f"covers {', '.join(set(all_topics[:4]))}. This would be a high-impact contribution "
                f"suitable for venues like NeurIPS or ICML.\n\n"
                f"3. **Survey Paper** — A systematic review covering {', '.join(set(all_topics[:3]))} "
                f"could be valuable given the rapid progress in these areas.\n\n"
                f"Would you like me to elaborate on any of these ideas?"
            )

    # --- "Email / reach out / contact" ---
    if any(kw in msg for kw in ["email", "reach out", "draft", "contact", "message"]):
        s = scholars[0]
        return (
            f"Here's a draft outreach email for **{s.name}**:\n\n"
            f"---\n\n"
            f"**Subject:** Potential Collaboration on {s.topics[0].title()}\n\n"
            f"Dear {s.name},\n\n"
            f"I've been following your recent work on {s.topics[0]} at {s.affiliation} with great interest. "
            f"Your research on {s.topics[1]} particularly caught my attention, and I believe there's a "
            f"compelling intersection with my own work in this area.\n\n"
            f"I'm exploring collaboration opportunities and would love to discuss potential synergies. "
            f"Would you be available for a brief call in the coming weeks?\n\n"
            f"Best regards,\n[Your Name]\n\n"
            f"---\n\n"
            f"Would you like me to customize this further or draft one for another scholar?"
        )

    # --- "Tell me about [scholar name]" ---
    for s in scholars:
        if s.name.lower().split(".")[-1].strip().split()[-1].lower() in msg:
            return (
                f"**{s.name}** is based at **{s.affiliation}** ({s.university}, {s.city}, {s.country}).\n\n"
                f"**Research Focus:** {', '.join(s.topics)}\n\n"
                f"**Impact:** h-index of {s.h_index} with {s.paper_count} published papers.\n\n"
                f"**Match Score:** {s.score:.0%} overall — "
                f"{s.score_breakdown.jaccard:.0%} topic overlap, "
                f"{s.score_breakdown.semantic:.0%} semantic similarity, "
                f"{s.score_breakdown.citation:.0%} citation graph analysis.\n\n"
                f"Their most impactful work centers on **{s.topics[0]}**, with recent contributions "
                f"to {s.topics[1]} and {s.topics[2] if len(s.topics) > 2 else s.topics[0]}. "
                f"Would you like to know more about specific aspects of their research?"
            )

    # --- Default: overview of session scholars ---
    lines = [f"In this session, you have {len(scholars)} scholars: {names_str}.\n"]
    lines.append("Here's a quick overview of their combined expertise:\n")
    all_topics = set()
    for s in scholars:
        all_topics.update(s.topics[:2])
        lines.append(f"- **{s.name}**: {', '.join(s.topics[:2])}")
    lines.append(f"\nOverlapping themes include: {', '.join(list(all_topics)[:5])}.")
    lines.append("\nYou can ask me:")
    lines.append("- *What are their specialties?*")
    lines.append("- *Who is most specialized in [topic]?*")
    lines.append("- *Suggest project ideas for collaboration*")
    lines.append("- *Draft an outreach email*")
    lines.append("- *Compare their profiles*")
    return "\n".join(lines)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message in a multi-scholar research session."""
    # Try real LLM first
    try:
        reply = await call_llm(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": req.message},
            ],
            session_id=req.session_id,
        )
        if reply:
            return ChatResponse(reply=reply, session_id=req.session_id)
    except Exception:
        log.exception("LLM call failed, falling back to smart mock")

    # Simulate thinking delay (1.5-3s) for realistic demo
    await asyncio.sleep(random.uniform(1.5, 3.0))

    reply = _smart_reply(req.message, req.session_id)
    return ChatResponse(reply=reply, session_id=req.session_id)


@router.post("/ask-scholar", response_model=AskScholarResponse)
async def ask_scholar(req: AskScholarRequest):
    """Ask a question about a specific scholar's research (RAG)."""
    scholar = SCHOLAR_BY_ID.get(req.scholar_id)
    name = scholar.name if scholar else "this scholar"

    if scholar:
        try:
            context = (
                f"Scholar: {scholar.name}\n"
                f"Affiliation: {scholar.affiliation}\n"
                f"Topics: {', '.join(scholar.topics)}\n"
                f"h-index: {scholar.h_index}, papers: {scholar.paper_count}"
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
            log.exception("LLM call failed for ask-scholar, falling back to mock")

    # Simulate delay
    await asyncio.sleep(random.uniform(1.0, 2.0))

    if scholar:
        answer = (
            f"**{scholar.name}** ({scholar.affiliation}) is a leading researcher in "
            f"**{scholar.topics[0]}**.\n\n"
            f"Their work spans {', '.join(scholar.topics)}, with {scholar.paper_count} publications "
            f"and an h-index of {scholar.h_index}. Their most cited contributions focus on novel "
            f"approaches to {scholar.topics[0]} and {scholar.topics[1]}.\n\n"
            f"Based at {scholar.university} in {scholar.city}, {scholar.country}, "
            f"they are well-positioned for collaborations in these areas."
        )
    else:
        answer = "I couldn't find information about this scholar. Please check the scholar ID."

    return AskScholarResponse(answer=answer, scholar_id=req.scholar_id)
