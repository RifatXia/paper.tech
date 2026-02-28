import json
import logging

from fastapi import APIRouter

from app.models.schemas import ProjectIdeasRequest, ProjectIdeasResponse, ProjectIdea
from app.mock_data import MOCK_PROJECT_IDEAS
from app.supermemory import get_chat_client

log = logging.getLogger(__name__)

router = APIRouter()

DEFAULT_USER_ID = "paper-tech-user"

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
    client = get_chat_client(
        user_id=DEFAULT_USER_ID,
        conversation_id=req.session_id,
    )

    if client:
        try:
            response = client.chat.completions.create(
                model="Qwen/Qwen3-4B",
                messages=[
                    {"role": "system", "content": IDEAS_SYSTEM_PROMPT},
                    {"role": "user", "content": "Generate project ideas for the scholars in this session."},
                ],
            )
            raw = response.choices[0].message.content
            # Strip markdown code fences if present
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            ideas_data = json.loads(raw)
            ideas = [ProjectIdea(**idea) for idea in ideas_data]
            return ProjectIdeasResponse(ideas=ideas, session_id=req.session_id)
        except Exception:
            log.exception("Supermemory/LLM call failed for project-ideas, falling back to mock")

    return ProjectIdeasResponse(ideas=MOCK_PROJECT_IDEAS, session_id=req.session_id)
