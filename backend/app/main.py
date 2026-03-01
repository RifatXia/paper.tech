from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
    allow_origins=[settings.frontend_url, "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
for r in [match, scholars, handpick, chat, graph, ideas]:
    app.include_router(r.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "environment": settings.environment}


# Serve frontend static files in production
# The built frontend lives at /app/static (copied by Dockerfile)
STATIC_DIR = Path(__file__).parent.parent / "static"

if STATIC_DIR.is_dir():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    # Catch-all: serve index.html for any non-API route (SPA client-side routing)
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # Don't intercept /api or /docs routes
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi"):
            return
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
