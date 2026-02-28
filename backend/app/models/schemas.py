from pydantic import BaseModel


# --- Match ---

class GeoFilter(BaseModel):
    country: str | None = None
    state: str | None = None
    city: str | None = None
    university: str | None = None


class MatchRequest(BaseModel):
    query: str
    top_k: int = 10
    geo_filter: GeoFilter | None = None


class ScoreBreakdown(BaseModel):
    jaccard: float
    semantic: float
    citation: float


class ScholarCard(BaseModel):
    scholar_id: str
    name: str
    affiliation: str
    university: str
    city: str
    state: str
    country: str
    h_index: int
    paper_count: int
    topics: list[str]
    score: float
    score_breakdown: ScoreBreakdown
    match_explanation: str


class MatchResponse(BaseModel):
    scholars: list[ScholarCard]
    query: str


# --- Scholars ---

class ScholarDetail(BaseModel):
    scholar_id: str
    name: str
    affiliation: str
    university: str
    city: str
    state: str
    country: str
    h_index: int
    paper_count: int
    topics: list[str]


# --- Handpick ---

class HandpickRequest(BaseModel):
    scholar_ids: list[str]


class HandpickResponse(BaseModel):
    session_id: str
    scholars: list[ScholarCard]
    message: str


# --- Chat ---

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    session_id: str


class AskScholarRequest(BaseModel):
    scholar_id: str
    question: str


class AskScholarResponse(BaseModel):
    answer: str
    scholar_id: str


# --- Graph ---

class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # "user" | "topic" | "scholar" | "paper" | "institution"


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float
    reason: str


class GraphStateResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


# --- Ideas ---

class ProjectIdea(BaseModel):
    title: str
    description: str
    suggested_venues: list[str]
    skill_gap: str


class ProjectIdeasRequest(BaseModel):
    session_id: str


class ProjectIdeasResponse(BaseModel):
    ideas: list[ProjectIdea]
    session_id: str
