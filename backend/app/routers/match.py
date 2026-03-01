import logging
import random

from fastapi import APIRouter

from app.models.schemas import MatchRequest, MatchResponse, ScholarCard, ScoreBreakdown
from app.mock_data import MOCK_SCHOLARS, FIELD_KEYWORDS, SCHOLAR_BY_ID, SCHOLAR_CACHE
from app.vectordb import search_scholars

log = logging.getLogger(__name__)

router = APIRouter()


def _keyword_match(query: str, top_k: int, geo_filter: dict | None) -> list[ScholarCard]:
    """Smart keyword matching against 200 scholars — used as mock fallback."""
    query_lower = query.lower()

    # Collect candidate IDs from keyword matches
    candidate_ids: set[str] = set()
    for keyword, ids in FIELD_KEYWORDS.items():
        if keyword.lower() in query_lower:
            candidate_ids.update(ids)

    # Also do a fuzzy topic-word match across all scholars
    # Filter out short/common words to avoid false matches
    _STOP = {"for", "and", "the", "of", "in", "on", "to", "a", "an", "with", "from", "based"}
    query_words = {w for w in query_lower.split() if len(w) > 3 and w not in _STOP}
    for s in MOCK_SCHOLARS:
        for topic in s.topics:
            topic_words = {w for w in topic.lower().split() if len(w) > 3 and w not in _STOP}
            if query_words & topic_words:
                candidate_ids.add(s.scholar_id)

    # If nothing matched, return top scholars by score
    if not candidate_ids:
        candidates = list(MOCK_SCHOLARS)
    else:
        candidates = [SCHOLAR_BY_ID[sid] for sid in candidate_ids if sid in SCHOLAR_BY_ID]

    # Apply geo filter
    if geo_filter:
        if geo_filter.get("country"):
            candidates = [s for s in candidates if s.country == geo_filter["country"]]
        if geo_filter.get("state"):
            candidates = [s for s in candidates if s.state == geo_filter["state"]]
        if geo_filter.get("university"):
            candidates = [s for s in candidates if s.university == geo_filter["university"]]

    # Re-score: field-keyword matches get a big boost, word-only matches less
    scored = []
    rng = random.Random(hash(query))
    for s in candidates:
        topic_text = " ".join(s.topics).lower()
        topic_words_set = {w for w in topic_text.split() if len(w) > 3 and w not in _STOP}
        overlap = len(query_words & topic_words_set)
        # Check if this scholar was from a FIELD_KEYWORDS match (higher priority)
        field_boost = 0.15 if s.scholar_id in candidate_ids else 0.0
        boosted = min(s.score + field_boost + overlap * 0.04 + rng.uniform(0, 0.02), 1.0)
        scored.append((boosted, s))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Rebuild with updated scores
    results = []
    for boosted_score, s in scored[:top_k]:
        results.append(ScholarCard(
            scholar_id=s.scholar_id,
            name=s.name,
            affiliation=s.affiliation,
            university=s.university,
            city=s.city,
            state=s.state,
            country=s.country,
            h_index=s.h_index,
            paper_count=s.paper_count,
            topics=s.topics,
            score=round(boosted_score, 2),
            score_breakdown=s.score_breakdown,
            match_explanation=s.match_explanation,
        ))
    return results


@router.post("/match", response_model=MatchResponse)
async def match_scholars(req: MatchRequest):
    """Return ranked co-author candidates for a research query."""
    # Build geo filter dict from request
    geo = None
    if req.geo_filter:
        geo = {}
        if req.geo_filter.country:
            geo["country"] = req.geo_filter.country
        if req.geo_filter.state:
            geo["state"] = req.geo_filter.state
        if req.geo_filter.university:
            geo["university"] = req.geo_filter.university

    # Try real Actian VectorAI DB search
    results = search_scholars(
        query_text=req.query,
        top_k=req.top_k,
        geo_filter=geo,
    )

    if results:
        scholars = []
        for r in results:
            s = r["scholar"]
            bd = r["breakdown"]
            scholars.append(ScholarCard(
                scholar_id=s.get("scholar_id", ""),
                name=s.get("name", ""),
                affiliation=s.get("affiliation", ""),
                university=s.get("university", ""),
                city=s.get("city", ""),
                state=s.get("state", ""),
                country=s.get("country", ""),
                h_index=s.get("h_index", 0),
                paper_count=s.get("paper_count", 0),
                topics=s.get("topics", []),
                score=r["score"],
                score_breakdown=ScoreBreakdown(
                    jaccard=bd["jaccard"],
                    semantic=bd["cosine"],
                    citation=bd["bibcoupling"],
                ),
                match_explanation=f"Composite match: {bd['cosine']:.0%} semantic similarity, "
                    f"{bd['jaccard']:.0%} topic overlap.",
            ))
        for s in scholars:
            SCHOLAR_CACHE[s.scholar_id] = s
        return MatchResponse(scholars=scholars, query=req.query)

    # Fallback: smart keyword matching across 200 scholars
    log.info("Using keyword matching for /match (Actian DB unavailable)")
    scholars = _keyword_match(req.query, req.top_k, geo)
    for s in scholars:
        SCHOLAR_CACHE[s.scholar_id] = s
    return MatchResponse(scholars=scholars, query=req.query)
