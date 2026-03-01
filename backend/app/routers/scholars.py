import logging

from fastapi import APIRouter

from app.models.schemas import ScholarDetail
from app.mock_data import MOCK_SCHOLARS
from app.vectordb import list_all_scholars

log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/scholars", response_model=list[ScholarDetail])
async def get_scholars():
    """Return all scholars in the database."""
    # Try real Actian VectorAI DB
    results = list_all_scholars()

    if results:
        return [
            ScholarDetail(
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
            )
            for s in results
        ]

    # Fallback to mock data
    log.info("Using mock data for /scholars (Actian DB unavailable)")
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
