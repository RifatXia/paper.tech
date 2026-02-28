import uuid

from fastapi import APIRouter

from app.models.schemas import HandpickRequest, HandpickResponse
from app.mock_data import MOCK_SCHOLARS

router = APIRouter()


@router.post("/handpick", response_model=HandpickResponse)
async def handpick_scholars(req: HandpickRequest):
    """Create a multi-scholar research session from handpicked scholars."""
    # TODO: Replace with real Supermemory session initialization:
    #   1. Fetch scholar paper corpora from Actian VectorAI DB
    #   2. Initialize Supermemory Infinite Chat session with unique session_id
    #   3. RAG-inject scholar context into session
    session_id = str(uuid.uuid4())
    picked = [s for s in MOCK_SCHOLARS if s.scholar_id in req.scholar_ids]
    return HandpickResponse(
        session_id=session_id,
        scholars=picked,
        message=f"Session created with {len(picked)} scholars. You can now chat about their research.",
    )
