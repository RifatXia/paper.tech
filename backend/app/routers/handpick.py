import uuid

from fastapi import APIRouter

from app.models.schemas import HandpickRequest, HandpickResponse
from app.mock_data import MOCK_SCHOLARS
from app.supermemory import add_session_context

router = APIRouter()


@router.post("/handpick", response_model=HandpickResponse)
async def handpick_scholars(req: HandpickRequest):
    """Create a multi-scholar research session from handpicked scholars."""
    session_id = str(uuid.uuid4())
    picked = [s for s in MOCK_SCHOLARS if s.scholar_id in req.scholar_ids]

    # Store session context in Supermemory so the Memory Router can
    # retrieve it during chat. Falls back silently if not configured.
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
