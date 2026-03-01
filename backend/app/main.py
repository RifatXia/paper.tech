from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import match, scholars, handpick, chat, graph, ideas
from app.routes.email import router as email_router

app = FastAPI(
    title="paper.tech API",
    description="AI-powered co-author discovery and multi-scholar collaboration",
    version="0.1.0",
)

app.include_router(email_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
for r in [match, scholars, handpick, chat, graph, ideas]:
    app.include_router(r.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "environment": settings.environment}
