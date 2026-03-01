# Backend — paper.tech

FastAPI backend for the paper.tech co-author discovery platform. Routes use real integrations (Actian VectorAI, Modal, Supermemory, Gemini) with automatic mock fallback when services are unavailable.

## Tech Stack

- **Python 3.11+** with FastAPI (>=0.115)
- **Uvicorn** — ASGI server (port 8000)
- **uv** — dependency management
- **Pydantic v2** — request/response models + settings
- **httpx** — async HTTP client
- **Actian VectorAI DB** — vector storage + ANN search (cortex SDK)
- **sentence-transformers** — `all-MiniLM-L6-v2` for local embeddings
- **networkx** — graph algorithms (co-citation scoring)
- **numpy** — numerical computing
- **Supermemory SDK** — long-term semantic memory
- **Modal** — serverless GPU for Qwen3-4B LLM
- **Google GenAI** — Gemini 2.5 Flash for email generation

## Dev Workflow

```bash
# from /workspaces/paper.tech (project root)
uv sync                                              # install deps
cd backend
uv run uvicorn app.main:app --reload --port 8000     # start dev server
uv add <package>                                     # add dependency (from root)
```

Or use `dev.sh` at the repo root to start both frontend and backend together.

- API docs: http://localhost:8000/docs (Swagger UI)
- ReDoc: http://localhost:8000/redoc

## Directory Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app init, CORS, router registration
│   ├── config.py            # Pydantic BaseSettings (env vars)
│   ├── vectordb.py          # Actian VectorAI DB client + composite scoring
│   ├── supermemory.py       # Hybrid memory: short-term + Supermemory
│   ├── mock_data.py         # Mock scholars, graph, ideas for dev fallback
│   ├── models/
│   │   └── schemas.py       # All Pydantic request/response models
│   ├── routers/
│   │   ├── match.py         # POST /api/match — ranked co-author search (Actian + scoring)
│   │   ├── scholars.py      # GET  /api/scholars — list all scholars (Actian)
│   │   ├── handpick.py      # POST /api/handpick — create multi-scholar session (Supermemory)
│   │   ├── chat.py          # POST /api/chat + /api/ask-scholar — chat & RAG (Modal + hybrid memory)
│   │   ├── graph.py         # GET  /api/graph-state — knowledge graph data
│   │   └── ideas.py         # POST /api/project-ideas — collaboration ideas (Modal)
│   └── routes/
│       └── email.py         # POST /api/generate_email — email drafting (Gemini 2.5 Flash)
├── db-scripts/
│   ├── schema.py            # Actian VectorAI DB collection setup
│   ├── ingest.py            # OpenAlex → embed → Actian ingestion pipeline
│   └── scoring.py           # Standalone composite scoring (Jaccard + cosine + BibCoupling)
├── benchmark/
│   ├── benchmark.py         # Multi-turn context retention benchmark (5 setups)
│   ├── plots.py             # Dark-themed visualization generator
│   └── results/             # Saved benchmark results and plots
├── modal_app.py             # Modal deployment: Qwen3-4B + MiniLM endpoints
├── Dockerfile               # Aedify deployment
└── paper_tech_backend/
    └── __main__.py           # Aedify entry point (python -m paper_tech_backend)
```

## API Endpoints

| Method | Endpoint | Purpose | Integration |
|--------|----------|---------|-------------|
| POST | `/api/match` | Ranked co-author search | Actian VectorAI + composite scoring |
| GET | `/api/scholars` | List all scholars | Actian VectorAI |
| POST | `/api/handpick` | Create multi-scholar session | Supermemory |
| POST | `/api/chat` | Send message in a session | Modal LLM + hybrid memory |
| POST | `/api/ask-scholar` | RAG Q&A for a single scholar | Modal LLM |
| GET | `/api/graph-state` | Knowledge graph nodes/edges | Mock (Supermemory graph TODO) |
| POST | `/api/project-ideas` | Generate collaboration ideas | Modal LLM |
| POST | `/api/generate_email` | Generate collaboration email | Gemini 2.5 Flash |
| GET | `/api/health` | Health check | — |

## Environment Variables

Loaded via Pydantic BaseSettings from `.env` (checks current dir, then parent). See root `.env.example`.

| Variable | Purpose |
|----------|---------|
| `SUPERMEMORY_KEY` | Supermemory API key |
| `ACTIAN_DB_URL` | Actian VectorAI DB address (default: 127.0.0.1:50051) |
| `MODAL_TOKEN_ID` | Modal token ID |
| `MODAL_TOKEN_SECRET` | Modal token secret |
| `MODAL_LLM_ENDPOINT` | Modal LLM inference endpoint |
| `MODAL_EMBED_ENDPOINT` | Modal embedding endpoint |
| `GOOGLE_API_KEY` | Google API key for Gemini email generation |
| `OPENALEX_EMAIL` | Email for OpenAlex API polite pool |
| `FRONTEND_URL` | Allowed CORS origin (default: `http://localhost:5173`) |
| `ENVIRONMENT` | Deployment environment (default: `development`) |

## Sponsor Integrations

| Sponsor | Used In | Purpose |
|---------|---------|---------|
| **Supermemory** | supermemory.py, chat, handpick | Hybrid memory: long-term semantic search + session context |
| **Actian VectorAI** | vectordb.py, match, scholars | ANN search over 384-dim embeddings + geo filter + composite scoring |
| **Modal** | modal_app.py, supermemory.py | Serverless GPU for Qwen3-4B LLM + MiniLM embeddings |
| **Aedify** | Dockerfile | Full-stack deployment from GitHub |

## Conventions

- All routes live in `app/routers/` (or `app/routes/` for standalone modules) and are registered in `main.py` with `/api` prefix
- Request/response models are defined in `app/models/schemas.py`
- Mock data is centralized in `app/mock_data.py` — routers fall back to it when services are unavailable
- CORS is configured in `main.py` to allow the frontend origin
- The `vectordb.py` module handles all Actian VectorAI DB communication and composite scoring
- The `supermemory.py` module handles all Supermemory + Modal LLM communication
