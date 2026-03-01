# Backend — paper.tech

FastAPI backend for the paper.tech co-author discovery platform. Currently serves mock data for development.

## Tech Stack

- **Python 3.11+** with FastAPI (>=0.115)
- **Uvicorn** — ASGI server (port 8000)
- **uv** — dependency management
- **Pydantic v2** — request/response models + settings
- **httpx** — async HTTP client
- **psycopg 3** — PostgreSQL / Actian VectorAI driver
- **numpy** — numerical computing
- **networkx** — graph algorithms
- **openai** — LLM integration

## Dev Workflow

```bash
# from /workspaces/paper.tech/backend
uv sync                                              # install deps
uv run uvicorn app.main:app --reload --port 8000     # start dev server
uv add <package>                                     # add dependency
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
│   ├── mock_data.py         # Mock scholars, graph, ideas for dev
│   ├── models/
│   │   └── schemas.py       # All Pydantic request/response models
│   └── routers/
│       ├── match.py         # POST /api/match — ranked co-author search
│       ├── scholars.py      # GET  /api/scholars — list all scholars
│       ├── handpick.py      # POST /api/handpick — create multi-scholar session
│       ├── chat.py          # POST /api/chat + /api/ask-scholar — chat & RAG Q&A
│       ├── graph.py         # GET  /api/graph-state — knowledge graph data
│       └── ideas.py         # POST /api/project-ideas — collaboration ideas
├── pyproject.toml           # Dependencies & metadata
└── uv.lock                  # Locked versions
```

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/match` | Ranked co-author search by research query |
| GET | `/api/scholars` | List all scholars |
| POST | `/api/handpick` | Create multi-scholar session from selected IDs |
| POST | `/api/chat` | Send message in a session |
| POST | `/api/ask-scholar` | RAG Q&A for a single scholar |
| GET | `/api/graph-state` | Knowledge graph nodes/edges for D3 viz |
| POST | `/api/project-ideas` | Generate collaboration project ideas |
| GET | `/api/health` | Health check |

## Environment Variables

Loaded via Pydantic BaseSettings from `../.env` (repo root). See `.env.example`.

| Variable | Purpose |
|----------|---------|
| `SUPERMEMORY_KEY` | Supermemory API key |
| `ACTIAN_DB_URL` | Actian VectorAI DB connection string |
| `MODAL_TOKEN_ID` | Modal token ID |
| `MODAL_TOKEN_SECRET` | Modal token secret |
| `MODAL_LLM_ENDPOINT` | Modal LLM inference endpoint |
| `MODAL_EMBED_ENDPOINT` | Modal embedding endpoint |
| `OPENALEX_EMAIL` | Email for OpenAlex API polite pool |
| `FRONTEND_URL` | Allowed CORS origin (default: `http://localhost:5173`) |
| `ENVIRONMENT` | Deployment environment (default: `development`) |

## Sponsor Integrations (TODO — currently mock)

| Sponsor | Used In | Purpose |
|---------|---------|---------|
| **Supermemory** | chat, handpick, graph | Session context/memory, semantic graph |
| **Actian VectorAI** | match, scholars | Vector storage, ANN search |
| **Modal** | match, chat, ideas | Serverless GPU for embeddings & LLM (Qwen3) |
| **OpenAlex** | (data pipeline) | Scholar metadata |

## Conventions

- All routes live in `app/routers/` and are registered in `main.py` with `/api` prefix
- Request/response models are defined in `app/models/schemas.py`
- Mock data is centralized in `app/mock_data.py`
- CORS is configured in `main.py` to allow the frontend origin
