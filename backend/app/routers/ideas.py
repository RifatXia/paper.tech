import json
import logging

from fastapi import APIRouter

from app.models.schemas import ProjectIdeasRequest, ProjectIdeasResponse, ProjectIdea
from app.mock_data import MOCK_PROJECT_IDEAS
from app.supermemory import call_llm

log = logging.getLogger(__name__)

router = APIRouter()

IDEAS_SYSTEM_PROMPT = (
    "You are a research collaboration assistant. Given the scholars in this session, "
    "generate 3 concrete collaboration project ideas. For each idea, provide:\n"
    "- title: a concise project title\n"
    "- description: 1-2 sentences describing the project\n"
    "- suggested_venues: a list of 2-3 academic venues (e.g. NeurIPS, ICML)\n"
    "- skill_gap: who brings what expertise\n\n"
    "Respond ONLY with a JSON array of objects with those keys. No other text."
)


@router.post("/project-ideas", response_model=ProjectIdeasResponse)
async def generate_project_ideas(req: ProjectIdeasRequest):
    """Generate collaboration project ideas for a handpicked scholar group."""
    try:
        raw = await call_llm(
            messages=[
                {"role": "system", "content": IDEAS_SYSTEM_PROMPT},
                {"role": "user", "content": "Generate project ideas for the scholars in this session."},
            ],
            session_id=req.session_id,
        )
        if raw:
            # Strip markdown code fences if present
            text = raw
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            ideas_data = json.loads(text)
            ideas = [ProjectIdea(**idea) for idea in ideas_data]
            return ProjectIdeasResponse(ideas=ideas, session_id=req.session_id)
    except Exception:
        log.exception("LLM call failed for project-ideas, falling back to mock")

    return ProjectIdeasResponse(ideas=MOCK_PROJECT_IDEAS, session_id=req.session_id)
