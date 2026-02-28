# Frontend — paper.tech

React + Vite SPA for the paper.tech co-author discovery platform.

## Tech Stack

- **React 18** with JSX (no TypeScript)
- **Vite 5** — dev server, bundler, env management
- **React Router v6** — client-side routing
- **Tailwind CSS v3** — utility-first styling
- **Axios** — HTTP client for all API calls
- **Inter** — primary font

## Dev Workflow

```bash
# from /workspaces/paper.tech/frontend
npm install
npm run dev       # starts Vite dev server (port 5173)
npm run build     # production build → dist/
npm run preview   # preview production build
```

The dev server proxies `/api/*` → `http://localhost:8000` (FastAPI backend). Both must be running for full functionality. Use `dev.sh` at the repo root to start both together.

## Directory Structure

```
src/
  api/
    client.js          # All API calls (axios instance + exported functions)
  components/
    ChatPanel.jsx      # Multi-scholar chat UI (uses sessionId)
    GeoFilter.jsx      # Country/state/city/university dropdown filter
    GraphPlaceholder.jsx  # Knowledge graph view (D3 placeholder)
    HandpickSidebar.jsx   # Right sidebar — selected scholars + start session
    Navbar.jsx         # Top nav bar
    ScholarCard.jsx    # Individual scholar result card with handpick button
    SearchBar.jsx      # Search input with submit
  pages/
    LandingPage.jsx    # "/" — hero + search entry point
    ResultsPage.jsx    # "/results?q=..." — main workspace (tabs: Results, Chat, Graph)
  App.jsx              # Router + layout wrapper
  index.css            # Tailwind directives + global styles
  main.jsx             # React entry point
```

## Routing

| Path | Component | Notes |
|---|---|---|
| `/` | `LandingPage` | Hero + search bar → navigates to `/results?q=...` |
| `/results` | `ResultsPage` | Reads `?q=` from URL; tabs: Results / Chat / Graph |

## API Client (`src/api/client.js`)

Axios instance with `baseURL` from `VITE_API_URL` env var (falls back to `""`).

| Function | Method | Endpoint | Purpose |
|---|---|---|---|
| `matchScholars(query, topK, geoFilter)` | POST | `/api/match` | Get ranked scholar matches |
| `getScholars()` | GET | `/api/scholars` | List all scholars |
| `handpickScholars(scholarIds)` | POST | `/api/handpick` | Start a Supermemory session for selected scholars |
| `chat(sessionId, message)` | POST | `/api/chat` | Send a message in a multi-scholar session |
| `askScholar(scholarId, question)` | POST | `/api/ask-scholar` | RAG Q&A for a single scholar |
| `getGraphState()` | GET | `/api/graph-state` | Fetch Supermemory knowledge graph data |
| `getProjectIdeas(sessionId)` | POST | `/api/project-ideas` | Generate collaboration project ideas |

## Styling Conventions

Custom Tailwind colors (defined in `tailwind.config.js`):

| Token | Hex | Use |
|---|---|---|
| `dark` | `#0a0f1e` | Page background |
| `dark-surface` | `#111827` | Surface / tab bar |
| `dark-card` | `#1a2235` | Cards, active tab |
| `dark-border` | `#2a3450` | Borders |
| `cyan-400` | `#22d3ee` | Primary accent (active states, highlights) |
| `cyan-500` | `#00d4db` | Hover accent |

The background also uses a `bg-grid` utility class (defined in `index.css`) for the subtle grid pattern.

## Environment Variables

Variables must be prefixed with `VITE_` to be exposed to the client.

| Variable | Purpose | Default |
|---|---|---|
| `VITE_API_URL` | Backend base URL | `""` (uses Vite proxy in dev) |

The `envDir` in `vite.config.js` is set to `..` (repo root), so `.env` files live at `/workspaces/paper.tech/.env`.

## Key State (ResultsPage)

- `scholars` — array of match results from `/api/match`
- `geoFilter` — `{ country, state, city, university }` — passed to match queries
- `handpicked` — array of scholar objects the user has selected
- `sessionId` — returned by `/api/handpick`; required for chat
- `activeTab` — `"Results" | "Chat" | "Graph"`

A session is created when the user clicks "Start Session" in the `HandpickSidebar`. Once `sessionId` is set, `ChatPanel` becomes functional.

## Component Responsibilities

- **`SearchBar`** — controlled input; calls `onSearch(query)` on submit
- **`GeoFilter`** — four dropdowns; calls `onChange(filter)` on any change; triggers re-search automatically
- **`ScholarCard`** — renders name, affiliation, h-index, topics, score breakdown; "Handpick" button calls `onHandpick(scholar)`
- **`HandpickSidebar`** — lists handpicked scholars; "Start Session" button calls `onStartSession()`; shows session ID when active
- **`ChatPanel`** — message thread UI; sends messages via `chat(sessionId, message)`; no session → shows prompt to start one
- **`GraphPlaceholder`** — placeholder for the D3 knowledge graph (to be implemented)
