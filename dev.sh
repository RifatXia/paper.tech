#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo -e "${CYAN}paper.tech${NC} — starting development servers..."
echo ""

# ── Prerequisites ──────────────────────────────────────────────
check() {
  if ! command -v "$1" &>/dev/null; then
    echo -e "${RED}Error:${NC} $1 is not installed. $2"
    exit 1
  fi
}

check node   "Install from https://nodejs.org (v18+)"
check python3 "Install Python 3.11+ from https://python.org"
check uv     "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"

# ── Env file ───────────────────────────────────────────────────
if [ ! -f "$ROOT/.env" ]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo -e "${GREEN}Created${NC} .env from .env.example"
fi

# ── Backend setup ──────────────────────────────────────────────
cd "$ROOT/backend"

if [ ! -d .venv ] || [ pyproject.toml -nt .venv ]; then
  echo "Installing backend dependencies..."
  uv sync
fi

# ── Frontend setup ─────────────────────────────────────────────
cd "$ROOT/frontend"

if [ ! -d node_modules ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

# ── Start both servers ─────────────────────────────────────────
echo ""
echo -e "${CYAN}Starting backend${NC} on http://localhost:8000"
echo -e "${CYAN}Starting frontend${NC} on http://localhost:5173"
echo -e "Press Ctrl+C to stop both servers."
echo ""

cleanup() {
  echo ""
  echo -e "${CYAN}Shutting down...${NC}"
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

cd "$ROOT/backend"
uv run uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

wait $BACKEND_PID $FRONTEND_PID
