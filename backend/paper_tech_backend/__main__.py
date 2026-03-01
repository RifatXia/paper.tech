"""Entry point for: python -m paper_tech_backend (used by Aedify deployment)."""
import uvicorn

uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
