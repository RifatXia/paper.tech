from fastapi import APIRouter

from app.models.schemas import ScholarDetail
from app.mock_data import MOCK_SCHOLARS

router = APIRouter()


@router.get("/scholars", response_model=list[ScholarDetail])
async def list_scholars():
    """Return all scholars in the database."""
    # TODO: Replace with Actian VectorAI DB query
    return [
        ScholarDetail(
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
        )
        for s in MOCK_SCHOLARS
    ]
