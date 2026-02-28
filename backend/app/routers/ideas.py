from fastapi import APIRouter

from app.models.schemas import ProjectIdeasRequest, ProjectIdeasResponse
from app.mock_data import MOCK_PROJECT_IDEAS

router = APIRouter()


@router.post("/project-ideas", response_model=ProjectIdeasResponse)
async def generate_project_ideas(req: ProjectIdeasRequest):
    """Generate collaboration project ideas for a handpicked scholar group."""
    # TODO: Replace with Modal LLM generation:
    #   1. Fetch session context from Supermemory
    #   2. Retrieve scholar profiles and paper abstracts
    #   3. Prompt Qwen3 to generate project ideas with venues and skill gaps
    return ProjectIdeasResponse(ideas=MOCK_PROJECT_IDEAS, session_id=req.session_id)
