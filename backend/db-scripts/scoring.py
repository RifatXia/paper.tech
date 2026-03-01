
import json
import networkx as nx
from sentence_transformers import SentenceTransformer
from cortex import CortexClient
from cortex.filters import Filter, Field

SERVER = "127.0.0.1:50051"
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

# Weights for composite score
ALPHA = 0.2   # Jaccard (topic overlap)
BETA  = 0.6   # Cosine (semantic similarity via Actian)
GAMMA = 0.2   # BibCoupling (citation graph)

# Load co-citation graph once at startup
def load_citation_graph(path="data/co_citation_edges.json"):
    G = nx.Graph()
    try:
        edges = json.load(open(path))
        for e in edges:
            G.add_edge(e["scholar_a"], e["scholar_b"], weight=e["weight"])
    except FileNotFoundError:
        pass  # no edges yet, BibCoupling will return 0
    return G

G = load_citation_graph()


# ── 1. Jaccard ────────────────────────────────────────────────────────────────
def jaccard(topics_a: list, topics_b: list) -> float:
    if not topics_a or not topics_b:
        return 0.0
    set_a = set(t.lower() for t in topics_a)
    set_b = set(t.lower() for t in topics_b)
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


# ── 2. Cosine via Actian ANN ──────────────────────────────────────────────────
def cosine_search(query_text: str, top_k: int = 20, filters: dict = None):
    query_vector = MODEL.encode(query_text).tolist()
    with CortexClient(SERVER) as client:
        if filters:
            f = Filter()
            for key, value in filters.items():
                f = f.must(Field(key).eq(value))
            results = client.search_filtered("scholars", query_vector, f, top_k=top_k)
        else:
            results = client.search("scholars", query=query_vector, top_k=top_k)

        # deduplicate IDs first
        seen_ids = set()
        unique_results = []
        for r in results:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                unique_results.append(r)

        # fetch payloads separately
        output = []
        for r in unique_results:
            record = client.get("scholars", r.id)
            print(f"DEBUG get() returned: {type(record)} — {record}")
            if record and isinstance(record, tuple):
                payload = record[1] if len(record) > 1 else record[0]
            elif record:
                payload = record.payload
            else:
                continue
            if payload:
                output.append((payload, float(r.score)))

    print(f"DEBUG cosine_search: {len(output)} results with payloads")
    return output

# ── 3. BibCoupling ────────────────────────────────────────────────────────────
def bibcoupling(scholar_id_a: str, scholar_id_b: str) -> float:
    if G.has_edge(scholar_id_a, scholar_id_b):
        return float(G[scholar_id_a][scholar_id_b].get("weight", 0.0))
    return 0.0


# ── 4. Main match function ────────────────────────────────────────────────────
def find_matches(
    query_text: str,
    query_topics: list = [],
    top_k: int = 10,
    filters: dict = None,
) -> list:
    # Step 1: get candidates from Actian using vector similarity
    candidates = cosine_search(query_text, top_k=top_k * 2, filters=filters)

    # Step 2: compute composite score for each candidate
    scored = []
    for payload, cosine in candidates:
        if payload is None:
            continue
        j = jaccard(query_topics, payload.get("topics", []))
        b = bibcoupling("query_user", payload.get("scholar_id", ""))
        score = (ALPHA * j) + (BETA * cosine) + (GAMMA * b)

        scored.append({
            "scholar": payload,
            "score": round(score, 4),
            "breakdown": {
                "jaccard":     round(j, 4),
                "cosine":      round(cosine, 4),
                "bibcoupling": round(b, 4),
            }
        })

    # Step 3: re-rank by composite score
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


# ── 5. Quick test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    results = find_matches(
        query_text="deep learning for natural language processing",
        query_topics=["machine learning", "NLP", "transformers"],
        top_k=5,
    )
    print(f"DEBUG: {len(results)} results returned")
    for r in results:
        print(f"\n{r['scholar'].get('name')}")
        print(f"  Total : {r['score']}")
        print(f"  Cosine: {r['breakdown']['cosine']}")
        print(f"  Jaccard: {r['breakdown']['jaccard']}")