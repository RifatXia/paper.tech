from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from google import genai

from app.config import settings

router = APIRouter()


class EmailRequest(BaseModel):
    scholar_name: str
    affiliation: str
    topics: list[str]
    h_index: int = 0
    paper_count: int = 0


@router.post("/generate_email")
def generate_email(request: EmailRequest) -> dict:
    if not settings.google_api_key:
        raise HTTPException(status_code=503, detail="GOOGLE_API_KEY not configured")

    client = genai.Client(api_key=settings.google_api_key)

    prompt = f"""Write a professional collaboration email to {request.scholar_name} at {request.affiliation}.
Their research topics: {", ".join(request.topics)}.
h-index: {request.h_index}, publications: {request.paper_count}.

Requirements:
- First line must be: Subject: <subject line>
- Warm but professional tone
- Reference 1-2 of their specific research topics
- Under 200 words
- End with a call to schedule a meeting

Write only the email, nothing else."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()

        lines = text.split("\n")
        subject = ""
        body = text
        if lines[0].startswith("Subject:"):
            subject = lines[0].replace("Subject:", "").strip()
            body = "\n".join(lines[2:]).strip()

        return {
            "subject": subject,
            "body": body,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
