import asyncio
import os
import json
import requests
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from cortex import AsyncCortexClient, DistanceMetric
from schema import main as create_schema

SERVER = "127.0.0.1:50051"
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

def fetch_scholars(per_page=50, pages=10):
    scholars = []
    for page in range(1, pages + 1):
        r = requests.get("https://api.openalex.org/authors", params={
            "filter": "last_known_institutions.country_code:US,works_count:>50",
            "sort": "cited_by_count:desc",
            "per-page": per_page,
            "page": page,
        })
        results = r.json().get("results", [])
        if not results:
            break
        scholars.extend(results)
        print(f"Fetched page {page}: {len(results)} scholars")
    return scholars

def fetch_papers(author_id, max_papers=5):
    r = requests.get("https://api.openalex.org/works", params={
        "filter": f"author.id:{author_id}",
        "sort": "cited_by_count:desc",
        "per-page": max_papers,
    })
    return r.json().get("results", [])

def reconstruct_abstract(work):
    inv = work.get("abstract_inverted_index")
    if not inv:
        return ""
    words = sorted(
        [(pos, word) for word, positions in inv.items() for pos in positions]
    )
    return " ".join(w for _, w in words)

async def main():
    # ── Step 1: Create schema in Actian ───────────────────────────────
    await create_schema()

    # ── Step 2: Fetch scholars from OpenAlex ──────────────────────────
    print("\nFetching scholars from OpenAlex...")
    scholars = fetch_scholars(per_page=50, pages=10)
    print(f"Total scholars: {len(scholars)}\n")

    scholar_records = []
    paper_records = []

    for i, s in enumerate(tqdm(scholars, desc="Fetching papers")):
        author_id = s["id"].split("/")[-1]
        inst = s.get("last_known_institutions", [{}])
        inst = inst[0] if inst else {}

        papers = fetch_papers(author_id)
        abstract_corpus = " ".join(
            reconstruct_abstract(p) for p in papers if p.get("abstract_inverted_index")
        )
        topics = [t["display_name"] for t in s.get("topics", [])[:5]]

        if not abstract_corpus:
            abstract_corpus = s.get("display_name", "") + " " + " ".join(topics)

        scholar_records.append({
            "int_id": i,
            "vector_text": abstract_corpus,
            "payload": {
                "scholar_id": author_id,
                "name": s.get("display_name", ""),
                "affiliation": inst.get("display_name", ""),
                "university": inst.get("display_name", ""),
                "city": inst.get("city", ""),
                "state": inst.get("region", ""),
                "country": inst.get("country_code", ""),
                "topics": topics,
                "h_index": s.get("summary_stats", {}).get("h_index", 0),
                "paper_count": s.get("works_count", 0),
            }
        })

        for j, paper in enumerate(papers):
            abstract = reconstruct_abstract(paper)
            if not abstract:
                continue
            paper_records.append({
                "int_id": i * 100 + j,
                "vector_text": abstract,
                "payload": {
                    "paper_id": paper["id"].split("/")[-1],
                    "scholar_id": author_id,
                    "title": paper.get("title", ""),
                    "abstract": abstract,
                    "year": paper.get("publication_year"),
                    "venue": ((paper.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
                    "citation_count": paper.get("cited_by_count", 0),
                }
            })

    if not scholar_records:
        print("❌ No scholars fetched. Check OpenAlex API.")
        return

    # ── Step 3: Embed ─────────────────────────────────────────────────
    print(f"\nEmbedding {len(scholar_records)} scholars...")
    scholar_vectors = MODEL.encode(
        [r["vector_text"] for r in scholar_records],
        batch_size=32, show_progress_bar=True
    )

    print(f"Embedding {len(paper_records)} papers...")
    paper_vectors = MODEL.encode(
        [r["vector_text"] for r in paper_records],
        batch_size=32, show_progress_bar=True
    )

    # ── Step 4: Write to Actian ───────────────────────────────────────
    async with AsyncCortexClient(SERVER) as client:
        print("\nWriting scholars to Actian...")
        await client.batch_upsert(
            "scholars",
            ids=[r["int_id"] for r in scholar_records],
            vectors=[v.tolist() for v in scholar_vectors],
            payloads=[r["payload"] for r in scholar_records],
        )
        print(f"✅ {len(scholar_records)} scholars written")

        print("Writing papers to Actian...")
        await client.batch_upsert(
            "papers",
            ids=[r["int_id"] for r in paper_records],
            vectors=[v.tolist() for v in paper_vectors],
            payloads=[r["payload"] for r in paper_records],
        )
        print(f"✅ {len(paper_records)} papers written")

        count = await client.count("scholars")
        print(f"\n✅ Total scholars in DB: {count}")

if __name__ == "__main__":
    asyncio.run(main())