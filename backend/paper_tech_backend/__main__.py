"""Entry point for `python -m paper_tech_backend` (used by Aedify)."""
import uvicorn

from app.main import app  # noqa: F401

uvicorn.run(app, host="0.0.0.0", port=8000)
