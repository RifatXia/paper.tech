import asyncio
import sys
import uuid
import numpy as np
from cortex import AsyncCortexClient, DistanceMetric

# Configuration
SERVER = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:50051"
DIMENSION = 384

# Collection configurations for Actian Vector DB
COLLECTIONS_CONFIG = {
    "scholars": {
        "dimension": DIMENSION,
        "distance_metric": DistanceMetric.COSINE,
        "hnsw_m": 32,
        "hnsw_ef_construct": 256,
        "hnsw_ef_search": 100,
        "description": "Scholar profiles with embedded abstract corpus",
        # Payload structure:
        # {
        #   "scholar_id": str (primary key),
        #   "name": str,
        #   "affiliation": str,
        #   "university": str,
        #   "city": str,
        #   "state": str,
        #   "country": str,
        #   "topics": list[str],  # for Jaccard similarity
        #   "h_index": int,
        #   "paper_count": int
        # }
    },
    "papers": {
        "dimension": DIMENSION,
        "distance_metric": DistanceMetric.COSINE,
        "hnsw_m": 16,
        "hnsw_ef_construct": 200,
        "hnsw_ef_search": 50,
        "description": "Research papers with semantic embeddings",
        # Payload structure:
        # {
        #   "paper_id": str (primary key),
        #   "scholar_id": str (references scholars),
        #   "title": str,
        #   "abstract": str,
        #   "year": int,
        #   "venue": str,
        #   "citation_count": int
        # }
    },
    # "co_citation_edges": {
    #     "dimension": 1,  # No embedding, just metadata
    #     "distance_metric": DistanceMetric.EUCLIDEAN,
    #     "hnsw_m": 8,
    #     "hnsw_ef_construct": 100,
    #     "hnsw_ef_search": 20,
    #     "description": "Co-citation edges representing scholar relationships",
    #     # Payload structure:
    #     # {
    #     #   "scholar_a": str,
    #     #   "scholar_b": str,
    #     #   "weight": float
    #     # }
    # }
}


async def main():
    """Initialize Actian Vector DB collections for the paper analysis system."""
    async with AsyncCortexClient(SERVER) as client:
        # Health check
        version, uptime = await client.health_check()
        print(f"\n✓ Connected to {version}")
        print(f"  Uptime: {uptime}")
        
        # Create collections
        print("\n📋 Creating collections...")
        
        for name, config in COLLECTIONS_CONFIG.items():
            if await client.collection_exists(name):
                print(f"⚠️  '{name}' already exists, skipping")
                continue
            await client.create_collection(
                name=name,
                dimension=config["dimension"],
                distance_metric=config["distance_metric"],
                hnsw_m=config["hnsw_m"],
                hnsw_ef_construct=config["hnsw_ef_construct"],
                hnsw_ef_search=config["hnsw_ef_search"],
            )
            print(f"✅ '{name}' collection created")
        
        import os, json
        os.makedirs("data", exist_ok=True)
        edges_path = "data/co_citation_edges.json"
        if not os.path.exists(edges_path):
            with open(edges_path, "w") as f:
                json.dump([], f)
            print("✅ co_citation_edges.json initialized")

        print("\n✅ Schema ready")




if __name__ == "__main__":
    asyncio.run(main())



