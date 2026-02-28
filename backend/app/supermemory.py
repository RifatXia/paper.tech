"""Supermemory integration — two clients:

1. `memory` (Supermemory SDK)  — add/search documents and memories
2. `llm`    (OpenAI SDK proxy) — chat through Memory Router for auto context

Both are None when the required env vars are missing, and every caller
falls back to mock data in that case.
"""

import logging
from urllib.parse import quote

from openai import OpenAI
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


# ── Memory Router (OpenAI-compatible proxy for chat) ───────────

def get_chat_client(user_id: str, conversation_id: str) -> OpenAI | None:
    """Create an OpenAI client that routes through Supermemory's Memory Router.

    The Memory Router sits between us and the LLM endpoint (Modal).
    It automatically:
      - stores conversation history per conversation_id
      - retrieves relevant memories and injects them as context
      - forwards the augmented request to the LLM
      - asynchronously creates new memories from the response

    Returns None if required env vars are missing.
    """
    if not settings.supermemory_key or not settings.modal_llm_endpoint:
        return None

    # The Memory Router base_url format embeds the downstream LLM URL.
    # e.g. if modal_llm_endpoint = "https://user--app.modal.run"
    # then base_url = "https://api.supermemory.ai/v3/https://user--app.modal.run/v1"
    endpoint = settings.modal_llm_endpoint.rstrip("/")
    base_url = f"https://api.supermemory.ai/v3/{endpoint}/v1"

    return OpenAI(
        api_key="unused",  # Modal endpoints don't need an OpenAI key
        base_url=base_url,
        default_headers={
            "x-supermemory-api-key": settings.supermemory_key,
            "x-sm-user-id": user_id,
            "x-sm-conversation-id": conversation_id,
        },
    )


# ── Helpers ────────────────────────────────────────────────────

async def add_scholar_to_memory(
    scholar_id: str,
    name: str,
    affiliation: str,
    topics: list[str],
    container_tag: str = "scholars",
) -> str | None:
    """Add a scholar profile as a document in Supermemory.

    Returns the document ID, or None if the SDK isn't configured.
    """
    if not memory:
        return None

    content = (
        f"Scholar: {name}\n"
        f"Affiliation: {affiliation}\n"
        f"Research topics: {', '.join(topics)}"
    )
    result = memory.documents.create(
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
    """Add session context (handpicked scholars) as a document so the
    Memory Router can retrieve it during chat."""
    if not memory:
        return None

    lines = [f"Research session {session_id}", "Handpicked scholars:"]
    for name, topics in zip(scholar_names, scholar_topics):
        lines.append(f"  - {name}: {', '.join(topics)}")

    result = memory.documents.create(
        content="\n".join(lines),
        container_tag=f"session-{session_id}",
        metadata={"type": "session", "session_id": session_id},
    )
    return result.id


async def search_memories(query: str, limit: int = 5) -> list[dict]:
    """Search Supermemory for relevant memories/documents."""
    if not memory:
        return []

    result = memory.search.documents(q=query)
    return [
        {"content": r.content, "score": r.score}
        for r in (result.results or [])[:limit]
    ]
