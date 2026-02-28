# Paper.tech — Full Project Plan

> An AI-powered co-author discovery and multi-scholar collaboration platform for ~1,000 researchers. Built on Supermemory, Modal, Actian VectorAI DB, deployed via Aedify.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                                     │
│                    React + Vite (Aedify hosted)                          │
│  ┌───────────────┐  ┌─────────────────┐  ┌──────────────────────────┐  │
│  │  Scholar       │  │  Paper.tech     │  │  Multi-Scholar Chat      │  │
│  │  Search +      │  │  Match Results  │  │  (Handpicked Collab.)    │  │
│  │  Geo Filter    │  │  Scored List    │  │  Supermemory Infinite    │  │
│  └───────────────┘  └─────────────────┘  │  Chat per Session        │  │
│                                           └──────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Knowledge Graph View (Supermemory Graph — live D3 viz)          │   │
│  │  Nodes: User ↔ Topics ↔ Scholars ↔ Papers ↔ Institutions/Geo    │   │
│  │  Edges update as you search, handpick, chat, bookmark            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ REST API calls (HTTPS)
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                                   │
│                    (Python, deployed on Aedify)                          │
│                                                                          │
│  /match   /ask-scholar   /handpick   /chat   /scholars   /graph-state   │
└────┬──────────────────┬──────────────┬──────────┬──────────────────────┘
     │                  │              │          │
     ▼                  ▼              ▼          ▼
┌──────────┐    ┌───────────────────────────────────────────────────────┐
│ Actian   │    │                    Modal (Serverless GPU)              │
│ VectorAI │    │                                                        │
│ DB       │    │  ┌────────────────┐   ┌────────────────────────────┐  │
│          │    │  │ Embedding Fn   │   │ LLM Inference Fn           │  │
│ scholars │◄───┤  │ (sentence-     │   │ (Qwen3 via vLLM)           │  │
│ papers   │    │  │  transformers) │   │ - Match explanations       │  │
│ vectors  │    │  │ Batch on ingest│   │ - RAG over scholar papers  │  │
│ topics   │    │  └────────────────┘   │ - Collab project ideas     │  │
│ geo meta │    │                       │ - Multi-scholar chat        │  │
└──────────┘    │                       └────────────────────────────┘  │
                └───────────────────────────────────────────────────────┘
                                          │
                                          ▼
                        ┌─────────────────────────────────┐
                        │        Supermemory               │
                        │                                  │
                        │  - User profile memory           │
                        │  - Per-session Infinite Chat     │
                        │    (multi-scholar context)       │
                        │  - Knowledge Graph (topics ↔     │
                        │    scholars ↔ papers ↔ sessions) │
                        │  - Feedback signals (bookmark,   │
                        │    hide, connect history)        │
                        │  - Context injection per query   │
                        └─────────────────────────────────┘
                                          │
                        ┌─────────────────────────────────┐
                        │     OpenAlex / Semantic Scholar  │
                        │     (Data ingestion source)      │
                        │     250M+ papers, author graph   │
                        └─────────────────────────────────┘
```

---

## Tech Stack

| Layer | Tool | Role |
|---|---|---|
| **Frontend** | React + Vite | SPA: search, match list, geo filter, handpick, chat UI, knowledge graph |
| **Backend** | FastAPI (Python) | REST API: routing, auth, orchestration |
| **Vector DB** | Actian VectorAI DB | Scholar + paper embeddings, ANN search, geo-filtered queries |
| **Context / Memory** | Supermemory Infinite Chat | User profiles, multi-scholar chat sessions, knowledge graph, feedback memory |
| **LLM Inference** | Modal + vLLM (Qwen3) | Match explanations, RAG, project idea generation |
| **Embeddings** | Modal + sentence-transformers | `all-MiniLM-L6-v2` for fast hackathon embedding |
| **Data Source** | OpenAlex API | 250M+ papers, author metadata, affiliation + geo |
| **Graph** | NetworkX | Co-citation + co-authorship edge scoring |
| **Deployment** | Aedify | GitHub → live URL, auto-deploy on push |
| **Auth / DB** | Aedify managed Postgres | User accounts, bookmarks, session storage |

---

## Model Strategy: Qwen3 Progressive Scaling

We use **Qwen3-Instruct** across all phases, scaling up model size as development progresses.
Qwen3 was released April 2025 with Apache 2.0 licensing and full vLLM support. We use two sizes: **Qwen3-4B** (development and testing) and **Qwen3-30B-A3B** (demo and production). The 30B-A3B is a Mixture-of-Experts model that activates only 3B parameters per forward pass — giving near-32B quality at a fraction of the compute cost.

### Progressive Model Ladder

| Phase | Model | GPU on Modal | Use Case |
|---|---|---|---|
| **Dev / local testing** | `Qwen3-4B` | T4 | Rapid iteration, unit testing prompts, cheap |
| **Hackathon demo** | `Qwen3-30B-A3B` | A100 | Live demo — only 3B active params per forward pass, fast and high quality |
| **Post-hack / production** | `Qwen3-30B-A3B` | A100 | Same model, scale horizontally as user base grows |

The same Modal endpoint code works across both sizes — just change the model name string.
For embeddings, use `all-MiniLM-L6-v2` as a separate lightweight Modal function on a T4.

```python
# modal_app.py — swap model name per phase
MODEL = "Qwen/Qwen3-4B"           # dev / testing
# MODEL = "Qwen/Qwen3-30B-A3B"   # demo / production

@app.function(gpu="A10G", image=image)
@modal.web_endpoint(method="POST")
def llm_inference(payload: dict):
    from vllm import LLM
    llm = LLM(model=MODEL, enable_prefix_caching=True)
    ...
```

---

## Similarity Scoring Engine

**Composite score:**

```
S(A, B) = α · Jaccard(topics_A, topics_B)
         + β · cosine(embed_A, embed_B)         ← via Actian VectorAI DB ANN
         + γ · BibCoupling(A, B)                 ← shared citation graph weight
```

Weights (α=0.2, β=0.6, γ=0.2) are defaults — adjustable per user via Supermemory-stored preferences.

---

## Sponsor Companies & Features Used

### 1. Supermemory
**Role:** Universal memory, context management, and knowledge graph layer for all LLM interactions.

| Feature Used | How We Use It |
|---|---|
| **Infinite Chat / context proxy** | Routes every chat call between FastAPI and Modal LLM; injects relevant history without prompt stuffing |
| **Per-user memory store** | Persists each researcher's interests, preferred geo filters, past sessions, and bookmarks |
| **Per-session conversation IDs** | Each handpicked scholar group gets a unique session — conversations persist across browser reloads |
| **Knowledge graph** | Live graph of User ↔ Topics ↔ Scholars ↔ Papers ↔ Institutions; updates as user searches, handpicks, chats, and bookmarks; powers the in-app Graph View |
| **Semantic memory graph** | Associates user feedback signals (bookmarks, hides) with topics and scholars to refine future matches |
| **MCP server integration** | Exposes memory to Modal-hosted agents for agentic workflows (project idea generation, email drafting) |

### 2. Actian VectorAI DB
**Role:** Primary vector store and retrieval engine for all scholar and paper embeddings.

| Feature Used | How We Use It |
|---|---|
| **HNSW vector indexing** | Fast ANN search over 384-dim embeddings of scholar abstract corpora |
| **Hybrid queries (vector + metadata)** | Geo filters (country, state, university) applied as SQL WHERE clauses alongside vector similarity ORDER BY |
| **Structured column storage** | Stores topic arrays (for Jaccard), h-index, affiliation, geo fields alongside vectors |
| **Real-time write support** | New scholars and papers ingested from OpenAlex can be added without full re-index |
| **Multi-table join** | papers and co_citation_edges tables queried alongside scholars for RAG and BibCoupling scoring |

### 3. Modal
**Role:** Serverless GPU infrastructure for all LLM inference and embedding generation.

| Feature Used | How We Use It |
|---|---|
| **Serverless GPU functions** | All Qwen3 inference (match explanations, RAG, project ideas, chat) runs on demand |
| **`@modal.web_endpoint`** | Exposes LLM and embedding functions as stable HTTPS endpoints called by FastAPI |
| **vLLM integration** | Serves Qwen3 with OpenAI-compatible API; prefix caching enabled for repeated paper context |
| **Separate T4 embedding function** | Lightweight `all-MiniLM-L6-v2` embedding served on cheaper GPU tier |
| **Auto-scaling to zero** | No idle GPU cost; containers spin up on request during demo |

### 4. Aedify
**Role:** Cloud deployment platform for the full-stack web application.

| Feature Used | How We Use It |
|---|---|
| **GitHub auto-deploy** | Push to main → Aedify builds and serves the updated app on a live URL instantly |
| **App hosting** | Serves the React + Vite frontend and FastAPI backend as a unified deployment |
| **Managed Postgres** | Stores user accounts, session metadata, bookmarks, and feedback logs |
| **Environment variable management** | Securely injects API keys for Supermemory, Actian, and Modal at deploy time |
| **Live URL for demo** | Judges access a real, production-like URL during presentation |

---

## Complete Feature List

### Core Features

1. **Scholar Search + Match Ranking**
   - Input: free-text description of your research (e.g., "KV cache compression for multi-turn LLM inference")
   - Output: ranked list of top-k co-author candidates with composite score breakdown (Jaccard chip / Semantic chip / Citation chip)

2. **Geographic Filter**
   - Filter candidates by same university, city, state, or country
   - Affiliation + geo metadata sourced from OpenAlex author records
   - Applied as SQL metadata pre-filter on Actian VectorAI DB before ANN search
   - React UI: dropdown hierarchy (University → City → State → Country)
   ```sql
   SELECT scholar_id, name,
          vector_distance(embedding, $query_vec) AS score
   FROM scholars
   WHERE country = 'US' AND state = 'Illinois'
   ORDER BY score ASC LIMIT 10;
   ```

3. **Handpick → Multi-Scholar Research Session**
   - From match results, user handpicks 2–5 scholars to pull into a session
   - All selected scholars' paper corpora fetched from Actian VectorAI DB and RAG-injected
   - Supermemory Infinite Chat session initialized with unique session_id per group
   - Conversation persists across browser reloads; only new messages sent per turn
   - Session-scoped questions:
     - "What are the overlapping research themes across these scholars?"
     - "What gap in the literature could we fill together?"
     - "Draft an email to propose a collaboration with Scholar X"
     - "What papers should I read before reaching out?"

4. **Per-Scholar RAG Deep Dive**
   - Click any scholar → Q&A panel powered by their papers in Actian VectorAI DB
   - Qwen3 answers grounded in retrieved paper chunks
   - Supermemory remembers prior questions about this scholar in your session

5. **Project Idea Generator**
   - Given a handpicked group, Qwen3 generates:
     - 3–5 concrete collaboration project ideas
     - Suggested venues (NeurIPS, EMNLP, ICSE, CHI, etc.)
     - Skill gap analysis: "Scholar A brings X, you bring Y, Scholar B fills Z"

6. **Knowledge Graph View (Supermemory Graph)**
   - Live interactive graph rendered in D3.js / React Force Graph
   - Node types: User, Topics, Scholars, Papers, Institutions, Geo regions
   - Edges created and weighted by: searches, handpicks, chat sessions, bookmarks, shared citations
   - Updates in real-time as you interact — the graph grows with your research session
   - Click actions:
     - Scholar node → open profile card + "Ask about this scholar" RAG panel
     - Topic node → re-run match constrained to that topic
     - Edge tooltip → why connected (shared topic / shared citations / co-author path / "you asked about both")
   - Powered by Supermemory's semantic memory graph API; synced to backend via `/graph-state` endpoint

7. **Personalized Memory**
   - Supermemory stores per-user: research interests, preferred geo, bookmarked scholars, hidden scholars, session summaries
   - Every subsequent session uses memory to refine match scores and skip already-seen candidates

8. **Network Graph Visualization**
   - Interactive co-authorship + citation graph (D3.js or Pyvis)
   - Centered on the querying researcher's area
   - Highlights clusters, citation hubs, and rising researchers with no prior connections

9. **Scholar Profile Cards**
   - Name, affiliation, university, city, country, h-index, paper count
   - Top 3 research keywords, recent papers, match score breakdown
   - "Handpick" button → adds to active session sidebar

10. **Session History**
    - All past handpick groups, conversations, and generated project ideas stored via Supermemory
    - Retrievable and resumable from the dashboard

11. **Bookmark + Feedback Loop**
    - Bookmark, hide, or "connect" any scholar
    - Signals written to Supermemory; used to reweight future composite scores and add edges to the Knowledge Graph

---

## Data Schema (Actian VectorAI DB)

```sql
scholars(
  scholar_id      TEXT PRIMARY KEY,
  name            TEXT,
  affiliation     TEXT,
  university      TEXT,
  city            TEXT,
  state           TEXT,
  country         TEXT,
  topics          TEXT[],           -- for Jaccard similarity
  embedding       VECTOR(384),      -- MiniLM embedding of abstract corpus
  h_index         INT,
  paper_count     INT
)

papers(
  paper_id        TEXT PRIMARY KEY,
  scholar_id      TEXT REFERENCES scholars,
  title           TEXT,
  abstract        TEXT,
  embedding       VECTOR(384),
  year            INT,
  venue           TEXT,
  citation_count  INT
)

co_citation_edges(
  scholar_a       TEXT,
  scholar_b       TEXT,
  weight          FLOAT
)
```

---

## Supermemory Integration (Context Layer)

```python
# FastAPI /chat endpoint
from openai import OpenAI

client = OpenAI(
    base_url="https://api.supermemory.ai/v3/https://<modal-endpoint>/v1",
    default_headers={
        "x-supermemory-api-key": SUPERMEMORY_KEY,
        "x-sm-user-id": user_id,
        "x-sm-conversation-id": session_id   # unique per handpicked group
    }
)

response = client.chat.completions.create(
    model="Qwen/Qwen3-30B-A3B",
    messages=[{"role": "user", "content": user_message}]
)
```

Each handpicked scholar group → unique `session_id`. Supermemory stores the full thread, injecting only the most relevant prior context each turn. Every interaction (search, handpick, chat message, bookmark) also writes a node/edge event to Supermemory's knowledge graph, which is read back by the `/graph-state` endpoint to power the live Knowledge Graph View in the UI.

---

## Project Phases (Hackathon Weekend)

### Phase 0 — Setup (Hour 0–2)
- [ ] Create React + Vite app; scaffold FastAPI with placeholder routes
- [ ] Provision Actian VectorAI DB instance; test connection
- [ ] Set up Supermemory account; test Infinite Chat proxy with Qwen3-4B
- [ ] Configure Modal tokens; deploy stub embedding + LLM endpoints (Qwen3-4B)
- [ ] Connect repo to Aedify; verify first live deploy

### Phase 1 — Data Ingestion (Hour 2–5)
- [ ] Pull ~200 scholars from OpenAlex API (with geo fields)
- [ ] Run Modal embed function on abstract corpus; write to VectorAI DB
- [ ] Extract topic keyword sets with KeyBERT
- [ ] Build co-citation edge table (NetworkX)
- [ ] Verify ANN + geo filter query returns correct results

### Phase 2 — Scoring + Match API (Hour 5–10)
- [ ] Implement composite scorer (Jaccard + cosine + BibCoupling)
- [ ] Expose `POST /match` in FastAPI; test end-to-end
- [ ] Implement geo filter (metadata pre-filter on VectorAI DB)
- [ ] Validate explanation quality with Qwen3-4B; swap to 30B-A3B when ready for demo

### Phase 3 — Supermemory + Handpick Session (Hour 10–18)
- [ ] Implement `POST /handpick` — initializes Supermemory session for group
- [ ] Wire Supermemory proxy → Modal LLM endpoint
- [ ] Implement `POST /chat` — routes through Supermemory → Modal → response
- [ ] Implement `POST /ask-scholar` — per-scholar RAG endpoint
- [ ] Implement `POST /project-ideas` — Qwen3 generates ideas for a handpicked group
- [ ] Implement `GET /graph-state` — reads Supermemory knowledge graph for current user
- [ ] Upgrade to Qwen3-30B-A3B on Modal A100 for demo quality

### Phase 4 — Frontend (Hour 18–28)
- [ ] Scholar search bar with geo filter dropdowns
- [ ] Ranked match cards with score breakdown chips
- [ ] "Handpick" button → active session sidebar
- [ ] Chat panel for active session (multi-scholar context)
- [ ] Per-scholar RAG Q&A panel
- [ ] Network graph view (Pyvis iframe or D3)
- [ ] Knowledge Graph View (D3 Force Graph — nodes: topics, scholars, papers, sessions; live-updating)

### Phase 5 — Deploy + Demo (Hour 28–36)
- [ ] Final push → Aedify auto-deploys
- [ ] Seed 3 demo user profiles in Supermemory
- [ ] 3-minute demo flow:
  1. Type research interest → see ranked matches with geo filter active
  2. Handpick 3 scholars → enter session
  3. Ask "What project could we work on together?" → Qwen3 answers via Supermemory-managed context
  4. Open Knowledge Graph View → show graph updates after handpicking + chatting (new edges/topics appear live)
  5. Reload page → session and graph still there (Supermemory persistence demo)

---

## Sponsor Prize Map

| Prize | Feature That Qualifies |
|---|---|
| **Best Use of Supermemory** | Infinite Chat sessions per scholar group; persistent user memory; live Knowledge Graph powered by Supermemory's semantic graph API |
| **Best Use of Actian VectorAI DB** | Primary vector store: ANN search + geo metadata filtering + full relational schema |
| **Best Deployed on Aedify** | React + FastAPI full-stack, GitHub → auto-deploy, live URL for demo |
| **Modal Track** | All Qwen3 inference + embedding pipelines on serverless GPUs; scales to zero |

---

## Evaluation Metrics

- **Precision@10**: Of top-10 returned co-authors, how many are genuinely relevant?
- **Recall@50**: Of known real-world collaborations in dataset, how many appear in top-50?
- **Latency targets**: ANN retrieval < 500ms; LLM explanation < 5s; chat turn < 3s
- **Memory hit rate**: % of queries where Supermemory returns meaningful prior context

---

## Business Case

### Market Opportunity
- Academic collaboration platforms market: **$3.2B in 2024 → $9.1B by 2033 (13.4% CAGR)**
- Broader collaboration software market: on track for **$261.72B by 2035 (~9.86% CAGR)**
- US alone: **4,000+ degree-granting institutions**, ~800,000 active researchers

### Revenue Model
- **Freemium SaaS**: Free tier (5 matches/month); Pro tier ($15–25/month)
- **Institutional licensing**: $5K–50K/year per university research office
- **Corporate R&D portals**: Branded tracks for companies connecting to academic labs
- **Grant discovery add-on**: Match researchers to NSF/NIH opportunities alongside co-authors

### Competitive Moat
- Network effects: richer feedback → better Supermemory personalization over time
- Data flywheel: each bookmark/hide/connect retrains match weights and enriches the Knowledge Graph automatically
- Sticky: once labs are onboarded, switching cost is high

---

## Future Roadmap

- Expand to 10,000+ scholars via continuous OpenAlex ingestion
- Funding discovery: surface NSF/NIH grants alongside co-author suggestions
- Federated mode: on-premise deployment for private university scholar graphs
- ORCID OAuth for live profile sync and auto paper import
- Team formation optimizer: multi-party matching for triads/quads
- Conference recommender: "Who to talk to at NeurIPS 2026 in your geo"
