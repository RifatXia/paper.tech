import logging

from fastapi import APIRouter

from app.models.schemas import MatchRequest, MatchResponse, ScholarCard, ScoreBreakdown
from app.mock_data import MOCK_SCHOLARS
from app.vectordb import search_scholars

log = logging.getLogger(__name__)

router = APIRouter()


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
        return MatchResponse(scholars=scholars, query=req.query)

    # Fallback to mock data
    log.info("Using mock data for /match (Actian DB unavailable)")
    scholars = MOCK_SCHOLARS
    if req.geo_filter:
        if req.geo_filter.country:
            scholars = [s for s in scholars if s.country == req.geo_filter.country]
        if req.geo_filter.state:
            scholars = [s for s in scholars if s.state == req.geo_filter.state]
        if req.geo_filter.university:
            scholars = [s for s in scholars if s.university == req.geo_filter.university]
    return MatchResponse(scholars=scholars[: req.top_k], query=req.query)
