# paper.tech

AI-powered co-author discovery platform. Describe your research, get ranked collaborator matches, handpick scholars, and explore ideas through multi-scholar chat.

Built for HackIllinois 2026.

## Prerequisites

- **Node.js 18+** — [nodejs.org](https://nodejs.org)
- **Python 3.11+** — [python.org](https://python.org)
- **uv** — `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Quick Start

```bash
git clone <repo-url> && cd paper.tech
chmod +x dev.sh
./dev.sh
```

This installs all dependencies and starts both servers:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs

## Architecture

```
Frontend (React + Vite)
    │
    ▼  /api proxy
FastAPI Backend
    │
    ├── Short-term memory (in-memory sliding window)
    ├── Long-term memory (Supermemory SDK)
    └── LLM inference (Qwen3-4B on Modal GPU)
```

### Hybrid Memory Architecture

The chat system uses a two-layer memory approach:

| Layer | Storage | Purpose | Latency |
|---|---|---|---|
| **Short-term** | In-memory dict per session | Recent conversation turns (last 6 exchanges) | Instant |
| **Long-term** | Supermemory (semantic search) | Cross-session recall, scholar profiles, older context | ~1-2s |

**Flow for each chat message:**
1. Supermemory searches for relevant long-term context (scholar data, past sessions)
2. Recent history window (last 6 turns) is pulled from in-memory cache
3. Both are assembled into the prompt sent to the LLM
4. The exchange is stored in both layers (history cache + Supermemory)

This ensures the LLM always has immediate conversational context (short-term) while also being able to recall information from earlier or past sessions (long-term).

## Manual Setup

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

All config lives in a single `.env` at the project root.

| Variable | Description |
|---|---|
| `SUPERMEMORY_KEY` | Supermemory API key (long-term memory layer) |
| `ACTIAN_DB_URL` | Actian VectorAI DB connection string |
| `MODAL_LLM_ENDPOINT` | Modal Qwen3-4B inference URL |
| `MODAL_EMBED_ENDPOINT` | Modal embedding function URL |
| `GITHUB_TOKEN` | GitHub PAT for GPT-4o-mini via GitHub Models (benchmark) |
| `GOOGLE_API_KEY` | Google API key for Gemini 2.5 Flash (benchmark) |
| `GROQ_API_KEY` | Groq API key for Llama 3.3 70B judge (benchmark) |
| `OPENALEX_EMAIL` | Email for OpenAlex API (polite pool) |

All routes currently return mock data, so the app runs without any keys set.

## API Routes

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/match` | Ranked co-author search |
| GET | `/api/scholars` | List all scholars |
| POST | `/api/handpick` | Create multi-scholar session |
| POST | `/api/chat` | Chat in a session (hybrid memory) |
| POST | `/api/ask-scholar` | Per-scholar RAG Q&A |
| GET | `/api/graph-state` | Knowledge graph data |
| POST | `/api/project-ideas` | Generate collaboration ideas |
| GET | `/api/health` | Health check |

## Modal Deployment

Deploy the Qwen3-4B LLM and MiniLM embeddings to Modal:

```bash
cd backend
uv run modal deploy modal_app.py
```

Features: A10G GPU, vLLM serving, GPU memory snapshots for fast cold starts, persistent HuggingFace cache volume.

## Benchmark

Compare multi-turn context retention across 5 setups:

| Setup | Description |
|---|---|
| GPT-4o-mini | Full history, via GitHub Models |
| Gemini 2.5 Flash | Full history, via Google GenAI |
| Qwen3-4B (no memory) | Each turn independent, no context |
| Qwen3-4B (full history) | Full conversation history in prompt |
| Qwen3-4B + Supermemory | Hybrid: sliding window + Supermemory retrieval |

```bash
cd backend

# Run benchmark (warms up endpoints first, excludes cold start from results)
uv run python -m benchmark.benchmark

# Generate plots from saved results
uv run python -m benchmark.plots
```

Results and plots saved to `backend/benchmark/results/`.

## Branch Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes, commit, push: `git push -u origin feature/your-feature`
3. Open a PR to `main`

## Adding Dependencies

- **Backend**: `cd backend && uv add <package>`
- **Frontend**: `cd frontend && npm install <package>`

## Sponsor Integrations

| Sponsor | Integration | Files |
|---|---|---|
| **Supermemory** | Long-term semantic memory, document storage | `app/supermemory.py`, `routers/chat.py`, `routers/handpick.py` |
| **Actian VectorAI DB** | Scholar embeddings & vector search | `routers/match.py`, `routers/scholars.py` |
| **Modal** | Serverless GPU for Qwen3-4B & embeddings | `modal_app.py`, `app/supermemory.py` |
