"""Supermemory + Modal integration:

1. `memory` (Supermemory SDK) — add/search documents, manage context
2. `call_llm()` — calls Modal LLM with Supermemory context injected
3. Helpers for scholar/session document management
"""

import logging

import httpx
from supermemory import Supermemory

from app.config import settings

log = logging.getLogger(__name__)

# ── Supermemory SDK client (documents, search, memories) ────────

memory: Supermemory | None = None

if settings.supermemory_key:
    memory = Supermemory(api_key=settings.supermemory_key)
    log.info("Supermemory SDK client initialized")
else:
    log.warning("SUPERMEMORY_KEY not set — memory features disabled, using mock data")


# ── LLM call with Supermemory context ──────────────────────────

async def call_llm(
    messages: list[dict],
    session_id: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> str | None:
    """Call Modal LLM endpoint with Supermemory context injected.

    1. Searches Supermemory for relevant memories based on the last user message
    2. Prepends retrieved context to the system prompt
    3. Calls Modal LLM directly via HTTP
    4. Stores the exchange back in Supermemory for future context

    Returns the LLM response text, or None if Modal isn't configured.
    """
    if not settings.modal_llm_endpoint:
        return None

    # Extract the user's message for context retrieval
    user_msg = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )

    # Retrieve relevant context from Supermemory
    context_chunks = []
    if memory and user_msg:
        try:
            search_kwargs = {"q": user_msg, "limit": 5}
            if session_id:
                search_kwargs["container_tags"] = [f"session-{session_id}", "scholars"]
            result = memory.search.execute(**search_kwargs)
            context_chunks = [
                r.content for r in (result.results or []) if r.content
            ]
        except Exception:
            log.exception("Supermemory search failed, proceeding without context")

    # Inject retrieved context into system message
    if context_chunks:
        context_block = (
            "Relevant context from memory:\n---\n"
            + "\n---\n".join(context_chunks)
            + "\n---\n\n"
        )
        # Prepend to existing system message or add one
        if messages and messages[0]["role"] == "system":
            messages = [
                {"role": "system", "content": context_block + messages[0]["content"]},
                *messages[1:],
            ]
        else:
            messages = [
                {"role": "system", "content": context_block},
                *messages,
            ]

    # Add instruction to suppress thinking tags
    think_instruction = "Respond directly without <think> tags. Be concise and helpful."
    if messages and messages[0]["role"] == "system":
        messages[0]["content"] += f"\n\n{think_instruction}"
    else:
        messages = [{"role": "system", "content": think_instruction}, *messages]

    # Call Modal LLM endpoint directly
    payload = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(
            settings.modal_llm_endpoint,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    reply = data["choices"][0]["message"]["content"]

    # Strip any <think>...</think> blocks the model might still produce
    if "<think>" in reply:
        import re
        reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL).strip()

    # Store the exchange in Supermemory for future context
    if memory and session_id:
        try:
            memory.documents.add(
                content=f"User: {user_msg}\nAssistant: {reply}",
                container_tag=f"session-{session_id}",
                metadata={"type": "chat", "session_id": session_id},
            )
        except Exception:
            log.exception("Failed to store chat exchange in Supermemory")

    return reply


# ── Helpers ────────────────────────────────────────────────────

async def add_scholar_to_memory(
    scholar_id: str,
    name: str,
    affiliation: str,
    topics: list[str],
    container_tag: str = "scholars",
) -> str | None:
    """Add a scholar profile as a document in Supermemory."""
    if not memory:
        return None

    content = (
        f"Scholar: {name}\n"
        f"Affiliation: {affiliation}\n"
        f"Research topics: {', '.join(topics)}"
    )
    result = memory.documents.add(
        content=content,
        container_tag=container_tag,
        custom_id=scholar_id,
        metadata={"type": "scholar", "name": name, "affiliation": affiliation},
    )
    return result.id


async def add_session_context(
    session_id: str,
    scholar_names: list[str],
    scholar_topics: list[list[str]],
) -> str | None:
    """Add session context (handpicked scholars) as a document."""
    if not memory:
        return None

    lines = [f"Research session {session_id}", "Handpicked scholars:"]
    for name, topics in zip(scholar_names, scholar_topics):
        lines.append(f"  - {name}: {', '.join(topics)}")

    result = memory.documents.add(
        content="\n".join(lines),
        container_tag=f"session-{session_id}",
        metadata={"type": "session", "session_id": session_id},
    )
    return result.id


async def search_memories(query: str, limit: int = 5) -> list[dict]:
    """Search Supermemory for relevant memories/documents."""
    if not memory:
        return []

    result = memory.search.execute(q=query, limit=limit)
    return [
        {"content": r.content or "", "score": r.score, "title": r.title}
        for r in (result.results or [])
    ]
