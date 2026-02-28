from fastapi import APIRouter

from app.models.schemas import GraphStateResponse
from app.mock_data import MOCK_GRAPH_NODES, MOCK_GRAPH_EDGES

router = APIRouter()


@router.get("/graph-state", response_model=GraphStateResponse)
async def get_graph_state():
    """Return the current knowledge graph state for visualization."""
    # TODO: Replace with Supermemory knowledge graph API:
    #   1. Read nodes/edges from Supermemory semantic graph for current user
    #   2. Merge with co-citation edges from NetworkX
    #   3. Return combined graph for D3 rendering
    return GraphStateResponse(nodes=MOCK_GRAPH_NODES, edges=MOCK_GRAPH_EDGES)
