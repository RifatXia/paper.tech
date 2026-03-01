"""Supermemory + Modal integration — hybrid memory architecture:

Short-term: In-memory sliding window of recent chat history per session
Long-term:  Supermemory semantic search for cross-session & older context

Flow:
  1. User sends message via /api/chat with session_id
  2. call_llm() retrieves long-term context from Supermemory
  3. Combines with short-term history window (last N turns)
  4. Sends full context to Modal Qwen3-4B
  5. Stores exchange in both short-term cache and Supermemory
"""

import logging
import re
from collections import defaultdict

import httpx
from supermemory import Supermemory

from app.config import settings

log = logging.getLogger(__name__)

# ── Supermemory SDK client ────────────────────────────────────

memory: Supermemory | None = None

if settings.supermemory_key:
    memory = Supermemory(api_key=settings.supermemory_key)
    log.info("Supermemory SDK client initialized")
else:
    log.warning("SUPERMEMORY_KEY not set — memory features disabled, using mock data")


# ── Short-term session history (in-memory) ────────────────────

# session_id -> list of {"role": "user"|"assistant", "content": str}
_session_history: dict[str, list[dict]] = defaultdict(list)

# How many recent exchanges (user+assistant pairs) to keep in the sliding window.
# 6 exchanges = 12 messages. This covers ~6 turns of immediate context.
HISTORY_WINDOW_EXCHANGES = 6
HISTORY_WINDOW_MESSAGES = HISTORY_WINDOW_EXCHANGES * 2


def get_session_history(session_id: str) -> list[dict]:
    """Get the recent history window for a session."""
    return _session_history[session_id][-HISTORY_WINDOW_MESSAGES:]


def append_to_history(session_id: str, user_msg: str, assistant_msg: str):
    """Append a user+assistant exchange to session history."""
    _session_history[session_id].append({"role": "user", "content": user_msg})
    _session_history[session_id].append({"role": "assistant", "content": assistant_msg})
    # Trim to prevent unbounded growth (keep 2x window for safety)
    max_keep = HISTORY_WINDOW_MESSAGES * 2
    if len(_session_history[session_id]) > max_keep:
        _session_history[session_id] = _session_history[session_id][-max_keep:]


def clear_session_history(session_id: str):
    """Clear history for a session (e.g. when session ends)."""
    _session_history.pop(session_id, None)


def _strip_think_tags(text: str) -> str:
    """Strip both complete <think>...</think> and incomplete <think>... blocks."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"<think>.*", "", text, flags=re.DOTALL)
    return text.strip()


# ── LLM call with hybrid memory ──────────────────────────────

async def call_llm(
    messages: list[dict],
    session_id: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> str | None:
    """Call Modal LLM with hybrid context: short-term history + Supermemory retrieval.

    1. Searches Supermemory for long-term relevant context
    2. Prepends retrieved context to the system prompt
    3. Inserts recent conversation history (sliding window)
    4. Calls Modal LLM directly via HTTP
    5. Stores the exchange in both short-term cache and Supermemory
    """
    if not settings.modal_llm_endpoint:
        return None

    # Extract the user's message and system prompt
    user_msg = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )
    system_msg = next(
        (m["content"] for m in messages if m["role"] == "system"),
        "You are a helpful assistant."
    )

    # ── 1. Long-term: Retrieve relevant context from Supermemory ──
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
            log.exception("Supermemory search failed, proceeding without long-term context")

    # ── 2. Build system prompt with long-term context ──
    if context_chunks:
        system_msg = (
            "Relevant context from long-term memory:\n---\n"
            + "\n---\n".join(context_chunks)
            + "\n---\n\n" + system_msg
        )

    system_msg += "\n\nRespond directly without <think> tags. Be concise and helpful."

    # ── 3. Assemble messages: system + short-term history + current turn ──
    assembled = [{"role": "system", "content": system_msg}]

    if session_id:
        history = get_session_history(session_id)
        if history:
            assembled.extend(history)

    assembled.append({"role": "user", "content": user_msg})

    # ── 4. Call Modal LLM ──
    payload = {
        "messages": assembled,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
        resp = await client.post(settings.modal_llm_endpoint, json=payload)
        resp.raise_for_status()
        data = resp.json()

    reply = data["choices"][0]["message"]["content"]
    reply = _strip_think_tags(reply)

    # ── 5. Store exchange in both memory layers ──
    if session_id:
        # Short-term: in-memory history
        append_to_history(session_id, user_msg, reply)

        # Long-term: Supermemory (async indexing, available for future sessions)
        if memory:
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
    """Add session context (handpicked scholars) as a document and init history."""
    # Clear any stale history for this session
    clear_session_history(session_id)

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
