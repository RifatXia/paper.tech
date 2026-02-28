from fastapi import APIRouter

from app.models.schemas import MatchRequest, MatchResponse
from app.mock_data import MOCK_SCHOLARS

router = APIRouter()


@router.post("/match", response_model=MatchResponse)
async def match_scholars(req: MatchRequest):
    """Return ranked co-author candidates for a research query."""
    # TODO: Replace with real pipeline:
    #   1. Embed query via Modal embed endpoint
    #   2. ANN search in Actian VectorAI DB (with geo filter)
    #   3. Compute composite score (Jaccard + semantic + citation)
    #   4. Generate match explanations via Modal LLM
    scholars = MOCK_SCHOLARS
    if req.geo_filter:
        if req.geo_filter.country:
            scholars = [s for s in scholars if s.country == req.geo_filter.country]
        if req.geo_filter.state:
            scholars = [s for s in scholars if s.state == req.geo_filter.state]
        if req.geo_filter.university:
            scholars = [s for s in scholars if s.university == req.geo_filter.university]
    return MatchResponse(scholars=scholars[: req.top_k], query=req.query)
