"""
Decider — classifies chat messages into pipeline routes.

  DEEP_ANALYSIS   → deep_analyzer.analyze_paper() (single paper breakdown)
  RESEARCH_QUERY  → agents.research() (multi-paper search + synthesize)
  GENERAL_CHAT    → existing call_llm() via Supermemory Memory Router
"""

import re
import logging
from enum import Enum

log = logging.getLogger(__name__)


class Intent(str, Enum):
    DEEP_ANALYSIS = "deep_analysis"
    RESEARCH_QUERY = "research_query"
    GENERAL_CHAT = "general_chat"


# ── Regex patterns ───────────────────────────────────────────

ARXIV_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})",
    re.IGNORECASE,
)
ARXIV_ID_RE = re.compile(r"\b(\d{4}\.\d{4,5})(?:v\d+)?\b")
ARXIV_OLD_RE = re.compile(r"\b([a-z-]+/\d{7})\b", re.IGNORECASE)

PAPER_URL_RE = re.compile(
    r"https?://(?:"
    r"(?:www\.)?semanticscholar\.org/paper/"
    r"|openreview\.net/(?:forum|pdf)\?id="
    r"|aclanthology\.org/"
    r"|papers\.nips\.cc/"
    r"|dl\.acm\.org/doi/"
    r")\S+",
    re.IGNORECASE,
)

DEEP_PHRASES_RE = re.compile(
    r"(?i)\b(?:"
    r"analyze\s+(?:this|the)\s+paper"
    r"|explain\s+(?:this|the)\s+paper"
    r"|break\s*down\s+(?:this|the)\s+paper"
    r"|deep\s+(?:dive|analysis)"
    r"|section.by.section"
    r"|summarize\s+(?:this|the)\s+paper"
    r"|what\s+does\s+(?:this|the)\s+paper\s+(?:say|do|propose)"
    r"|read\s+(?:this|the)\s+paper"
    r"|paper\s+analysis"
    r")\b"
)

RESEARCH_PHRASES_RE = re.compile(
    r"(?i)\b(?:"
    r"(?:find|search|look\s+for|get)\s+(?:papers?|research|work|studies)"
    r"|what\s+(?:are|is)\s+(?:the\s+)?(?:latest|recent|state.of.the.art|sota)"
    r"|survey\s+(?:of|on)"
    r"|literature\s+(?:review|search)"
    r"|compare\s+(?:approaches|methods|papers)"
    r"|who\s+(?:is|are)\s+working\s+on"
    r"|recommend\s+papers?"
    r")\b"
)

RESEARCH_TERMS = {
    "model", "method", "approach", "architecture", "dataset", "benchmark",
    "training", "transformer", "neural", "learning", "detection",
    "classification", "segmentation", "prediction", "generation",
    "optimization", "algorithm", "accuracy", "embedding", "attention",
    "diffusion", "reinforcement", "supervised", "self-supervised",
    "retrieval", "pretraining", "fine-tuning", "vision", "language",
    "multimodal", "medical", "imaging", "mammography",
}


def extract_arxiv_id(text: str) -> str | None:
    """Extract ArXiv ID from text if present."""
    m = ARXIV_URL_RE.search(text)
    if m:
        return m.group(1)
    m = ARXIV_ID_RE.search(text)
    if m:
        return m.group(1)
    m = ARXIV_OLD_RE.search(text)
    if m:
        return m.group(1)
    return None


def classify(
    message: str,
    recent_history: list[dict] | None = None,
) -> tuple[Intent, dict]:
    """
    Classify a chat message. Returns (intent, metadata).

    metadata keys:
      - arxiv_id: str  (for DEEP_ANALYSIS)
      - paper_url: str (for DEEP_ANALYSIS)
      - needs_url: bool (deep analysis requested but no URL found)
      - topic: str (for RESEARCH_QUERY)
      - note: str (for GENERAL_CHAT when context is missing)
    """
    text = message.strip()

    # ── 1. ArXiv URL or ID → deep analysis ──
    arxiv_id = extract_arxiv_id(text)
    if arxiv_id:
        return Intent.DEEP_ANALYSIS, {
            "arxiv_id": arxiv_id,
            "paper_url": f"https://arxiv.org/abs/{arxiv_id}",
        }

    # ── 2. Other paper URL → deep analysis ──
    m = PAPER_URL_RE.search(text)
    if m:
        return Intent.DEEP_ANALYSIS, {"paper_url": m.group(0)}

    # ── 3. Deep analysis phrases → check history for paper ──
    if DEEP_PHRASES_RE.search(text):
        # Try to find a paper URL in recent history
        if recent_history:
            for msg in reversed(recent_history):
                aid = extract_arxiv_id(msg.get("content", ""))
                if aid:
                    return Intent.DEEP_ANALYSIS, {
                        "arxiv_id": aid,
                        "paper_url": f"https://arxiv.org/abs/{aid}",
                    }
        # No paper found → ask user
        return Intent.GENERAL_CHAT, {
            "note": "ask_for_paper_url",
        }

    # ── 4. Research phrases → research query ──
    if RESEARCH_PHRASES_RE.search(text):
        return Intent.RESEARCH_QUERY, {"topic": text}

    # ── 5. Long message with research terms → research query ──
    words = text.split()
    text_lower = {w.lower().strip("?.,!") for w in words}
    overlap = text_lower & RESEARCH_TERMS
    if len(words) > 12 and len(overlap) >= 2:
        return Intent.RESEARCH_QUERY, {"topic": text}

    # ── 6. Default → general chat ──
    return Intent.GENERAL_CHAT, {}