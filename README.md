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

## Manual Setup

### Backend

```bash
cd backend
cp .env.example .env    # fill in API keys
uv sync                 # install dependencies
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Environment Variables

| Variable | Description |
|---|---|
| `SUPERMEMORY_KEY` | Supermemory API key (context/memory layer) |
| `ACTIAN_DB_URL` | Actian VectorAI DB connection string |
| `MODAL_TOKEN_ID` | Modal token ID (serverless GPU) |
| `MODAL_TOKEN_SECRET` | Modal token secret |
| `MODAL_LLM_ENDPOINT` | Modal LLM inference URL |
| `MODAL_EMBED_ENDPOINT` | Modal embedding function URL |
| `OPENALEX_EMAIL` | Email for OpenAlex API (polite pool) |

All routes currently return mock data, so the app runs without any keys set.

## API Routes

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/match` | Ranked co-author search |
| GET | `/api/scholars` | List all scholars |
| POST | `/api/handpick` | Create multi-scholar session |
| POST | `/api/chat` | Chat in a session |
| POST | `/api/ask-scholar` | Per-scholar RAG Q&A |
| GET | `/api/graph-state` | Knowledge graph data |
| POST | `/api/project-ideas` | Generate collaboration ideas |
| GET | `/api/health` | Health check |

## Branch Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes, commit, push: `git push -u origin feature/your-feature`
3. Open a PR to `main` — don't commit directly to main

## Adding Dependencies

- **Backend**: `cd backend && uv add <package>`
- **Frontend**: `cd frontend && npm install <package>`

## Sponsor Integrations

| Sponsor | Where in Codebase |
|---|---|
| **Supermemory** | `backend/app/routers/chat.py`, `handpick.py`, `graph.py` |
| **Actian VectorAI DB** | `backend/app/routers/match.py`, `scholars.py` |
| **Modal** | `backend/app/routers/match.py`, `chat.py`, `ideas.py` |
| **Aedify** | Deployment config (GitHub → auto-deploy) |
