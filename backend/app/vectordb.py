"""Actian VectorAI DB client — shared across routers.

Uses the cortex SDK to query the vectoraidb container (docker-compose.yml).
Falls back gracefully when the DB is unavailable (returns None so routers
can fall back to mock data).
"""

import json
import logging
from pathlib import Path

import networkx as nx
from sentence_transformers import SentenceTransformer

from app.config import settings

log = logging.getLogger(__name__)

# ── Lazy globals ─────────────────────────────────────────────────
_model: SentenceTransformer | None = None
_citation_graph: nx.Graph | None = None

SERVER = settings.actian_db_url or "127.0.0.1:50051"

# Composite score weights
ALPHA = 0.2  # Jaccard (topic overlap)
BETA = 0.6   # Cosine (semantic similarity)
GAMMA = 0.2  # BibCoupling (citation graph)


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_citation_graph() -> nx.Graph:
    global _citation_graph
    if _citation_graph is None:
        _citation_graph = nx.Graph()
        edges_path = Path(__file__).parent.parent / "db-scripts" / "data" / "co_citation_edges.json"
        try:
            edges = json.loads(edges_path.read_text())
            for e in edges:
                _citation_graph.add_edge(e["scholar_a"], e["scholar_b"], weight=e["weight"])
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    return _citation_graph


def _jaccard(topics_a: list[str], topics_b: list[str]) -> float:
    if not topics_a or not topics_b:
        return 0.0
    set_a = {t.lower() for t in topics_a}
    set_b = {t.lower() for t in topics_b}
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def _bibcoupling(scholar_a: str, scholar_b: str) -> float:
    G = _get_citation_graph()
    if G.has_edge(scholar_a, scholar_b):
        return float(G[scholar_a][scholar_b].get("weight", 0.0))
    return 0.0


def search_scholars(
    query_text: str,
    top_k: int = 10,
    query_topics: list[str] | None = None,
    geo_filter: dict | None = None,
) -> list[dict] | None:
    """Search Actian VectorAI DB for matching scholars.

    Returns a list of dicts with 'scholar' (payload), 'score', and 'breakdown',
    or None if the DB is unavailable (so callers fall back to mock).
    """
    try:
        from cortex import CortexClient
        from cortex.filters import Filter, Field
    except ImportError:
        log.warning("cortex SDK not installed, falling back to mock data")
        return None

    try:
        model = _get_model()
        query_vector = model.encode(query_text).tolist()

        with CortexClient(SERVER) as client:
            # Build filter if geo constraints provided
            if geo_filter:
                f = Filter()
                for key, value in geo_filter.items():
                    if value:
                        f = f.must(Field(key).eq(value))
                results = client.search_filtered("scholars", query_vector, f, top_k=top_k * 2)
            else:
                results = client.search("scholars", query=query_vector, top_k=top_k * 2)

            # Deduplicate and fetch payloads
            seen = set()
            candidates = []
            for r in results:
                if r.id in seen:
                    continue
                seen.add(r.id)
                record = client.get("scholars", r.id)
                if record and isinstance(record, tuple):
                    payload = record[1] if len(record) > 1 else record[0]
                elif record:
                    payload = record.payload if hasattr(record, "payload") else record
                else:
                    continue
                if payload:
                    candidates.append((payload, float(r.score)))

        # Composite scoring
        scored = []
        for payload, cosine in candidates:
            j = _jaccard(query_topics or [], payload.get("topics", []))
            b = _bibcoupling("query_user", payload.get("scholar_id", ""))
            score = (ALPHA * j) + (BETA * cosine) + (GAMMA * b)
            scored.append({
                "scholar": payload,
                "score": round(score, 4),
                "breakdown": {
                    "jaccard": round(j, 4),
                    "cosine": round(cosine, 4),
                    "bibcoupling": round(b, 4),
                },
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    except Exception:
        log.exception("Actian VectorAI DB query failed")
        return None


def list_all_scholars(limit: int = 100) -> list[dict] | None:
    """Retrieve all scholars from Actian VectorAI DB.

    Returns list of payload dicts, or None if DB unavailable.
    """
    try:
        from cortex import CortexClient
    except ImportError:
        return None

    try:
        with CortexClient(SERVER) as client:
            # Scroll through all scholars
            count = client.count("scholars")
            if count == 0:
                return None

            # Use a zero-vector search with high top_k to retrieve all
            dummy_vector = [0.0] * 384
            results = client.search("scholars", query=dummy_vector, top_k=min(count, limit))

            scholars = []
            seen = set()
            for r in results:
                if r.id in seen:
                    continue
                seen.add(r.id)
                record = client.get("scholars", r.id)
                if record and isinstance(record, tuple):
                    payload = record[1] if len(record) > 1 else record[0]
                elif record:
                    payload = record.payload if hasattr(record, "payload") else record
                else:
                    continue
                if payload:
                    scholars.append(payload)
            return scholars if scholars else None

    except Exception:
        log.exception("Actian VectorAI DB list_all failed")
        return None
