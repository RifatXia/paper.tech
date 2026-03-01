import logging
import uuid

from fastapi import APIRouter

from app.models.schemas import HandpickRequest, HandpickResponse, ScholarCard, ScoreBreakdown
from app.mock_data import MOCK_SCHOLARS
from app.supermemory import add_session_context
from app.vectordb import list_all_scholars

log = logging.getLogger(__name__)

router = APIRouter()


@router.post("/handpick", response_model=HandpickResponse)
async def handpick_scholars(req: HandpickRequest):
    """Create a multi-scholar research session from handpicked scholars."""
    session_id = str(uuid.uuid4())

    # Try finding scholars in Actian VectorAI DB first
    picked: list[ScholarCard] = []
    db_scholars = list_all_scholars(limit=500)
    if db_scholars:
        for s in db_scholars:
            if s.get("scholar_id") in req.scholar_ids:
                picked.append(ScholarCard(
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
                    score=0.0,
                    score_breakdown=ScoreBreakdown(jaccard=0.0, semantic=0.0, citation=0.0),
                    match_explanation="Handpicked for this session.",
                ))

    # Fallback to mock data
    if not picked:
        picked = [s for s in MOCK_SCHOLARS if s.scholar_id in req.scholar_ids]

    # Store session context in Supermemory
    await add_session_context(
        session_id=session_id,
        scholar_names=[s.name for s in picked],
        scholar_topics=[s.topics for s in picked],
    )

    return HandpickResponse(
        session_id=session_id,
        scholars=picked,
        message=f"Session created with {len(picked)} scholars. You can now chat about their research.",
    )
