"""Realistic mock data for development — every route returns something useful."""

from app.models.schemas import (
    ScholarCard,
    ScoreBreakdown,
    GraphNode,
    GraphEdge,
    ProjectIdea,
)

MOCK_SCHOLARS: list[ScholarCard] = [
    ScholarCard(
        scholar_id="s1",
        name="Dr. Amara Osei",
        affiliation="MIT CSAIL",
        university="Massachusetts Institute of Technology",
        city="Cambridge",
        state="Massachusetts",
        country="US",
        h_index=42,
        paper_count=87,
        topics=["KV cache compression", "transformer inference", "systems for ML"],
        score=0.93,
        score_breakdown=ScoreBreakdown(jaccard=0.85, semantic=0.96, citation=0.91),
        match_explanation="Dr. Osei's work on KV cache eviction policies directly complements your interest in multi-turn LLM inference optimization.",
    ),
    ScholarCard(
        scholar_id="s2",
        name="Prof. Liang Chen",
        affiliation="Stanford NLP Group",
        university="Stanford University",
        city="Stanford",
        state="California",
        country="US",
        h_index=58,
        paper_count=134,
        topics=["efficient transformers", "long-context models", "attention mechanisms"],
        score=0.88,
        score_breakdown=ScoreBreakdown(jaccard=0.72, semantic=0.94, citation=0.87),
        match_explanation="Prof. Chen's efficient attention research shares significant methodological overlap with your transformer optimization focus.",
    ),
    ScholarCard(
        scholar_id="s3",
        name="Dr. Sofia Rodriguez",
        affiliation="CMU LTI",
        university="Carnegie Mellon University",
        city="Pittsburgh",
        state="Pennsylvania",
        country="US",
        h_index=35,
        paper_count=62,
        topics=["model compression", "quantization", "edge deployment"],
        score=0.82,
        score_breakdown=ScoreBreakdown(jaccard=0.68, semantic=0.89, citation=0.78),
        match_explanation="Dr. Rodriguez brings complementary expertise in model compression that could extend your inference optimization to resource-constrained settings.",
    ),
    ScholarCard(
        scholar_id="s4",
        name="Prof. Raj Patel",
        affiliation="UC Berkeley BAIR",
        university="University of California, Berkeley",
        city="Berkeley",
        state="California",
        country="US",
        h_index=47,
        paper_count=95,
        topics=["speculative decoding", "LLM serving", "batched inference"],
        score=0.79,
        score_breakdown=ScoreBreakdown(jaccard=0.60, semantic=0.91, citation=0.72),
        match_explanation="Prof. Patel's speculative decoding work tackles the same latency bottlenecks from a different angle — strong potential for joint systems work.",
    ),
    ScholarCard(
        scholar_id="s5",
        name="Dr. Yuki Tanaka",
        affiliation="University of Tokyo IST",
        university="University of Tokyo",
        city="Tokyo",
        state="Tokyo",
        country="JP",
        h_index=29,
        paper_count=48,
        topics=["mixture of experts", "sparse models", "distributed inference"],
        score=0.74,
        score_breakdown=ScoreBreakdown(jaccard=0.55, semantic=0.85, citation=0.65),
        match_explanation="Dr. Tanaka's MoE research connects to your work via shared interest in reducing active parameter counts during inference.",
    ),
]

MOCK_GRAPH_NODES: list[GraphNode] = [
    GraphNode(id="user", label="You", type="user"),
    GraphNode(id="t1", label="KV cache compression", type="topic"),
    GraphNode(id="t2", label="efficient transformers", type="topic"),
    GraphNode(id="t3", label="model compression", type="topic"),
    GraphNode(id="s1", label="Dr. Amara Osei", type="scholar"),
    GraphNode(id="s2", label="Prof. Liang Chen", type="scholar"),
    GraphNode(id="s3", label="Dr. Sofia Rodriguez", type="scholar"),
    GraphNode(id="p1", label="Efficient KV Cache Eviction (2024)", type="paper"),
    GraphNode(id="i1", label="MIT CSAIL", type="institution"),
]

MOCK_GRAPH_EDGES: list[GraphEdge] = [
    GraphEdge(source="user", target="t1", weight=1.0, reason="searched for this topic"),
    GraphEdge(source="t1", target="s1", weight=0.93, reason="top match on KV cache compression"),
    GraphEdge(source="t2", target="s2", weight=0.88, reason="top match on efficient transformers"),
    GraphEdge(source="t3", target="s3", weight=0.82, reason="top match on model compression"),
    GraphEdge(source="s1", target="p1", weight=1.0, reason="authored this paper"),
    GraphEdge(source="s1", target="i1", weight=1.0, reason="affiliated with MIT CSAIL"),
    GraphEdge(source="s1", target="s2", weight=0.45, reason="3 shared citations"),
]

MOCK_PROJECT_IDEAS: list[ProjectIdea] = [
    ProjectIdea(
        title="Adaptive KV Cache Compression for Multi-Turn Dialogue",
        description="Combine Dr. Osei's eviction policies with Prof. Chen's long-context attention to build a cache that adapts its compression ratio based on conversation turn depth.",
        suggested_venues=["NeurIPS", "ICML", "MLSys"],
        skill_gap="Dr. Osei brings systems-level KV cache expertise; Prof. Chen contributes attention mechanism theory; you bridge with multi-turn inference benchmarks.",
    ),
    ProjectIdea(
        title="Edge-Deployable Sparse Transformer with Dynamic MoE Routing",
        description="Merge Dr. Rodriguez's quantization techniques with Dr. Tanaka's MoE routing to create a model that runs on consumer GPUs with minimal quality loss.",
        suggested_venues=["EMNLP", "ACL", "ICLR"],
        skill_gap="Dr. Rodriguez handles compression/quantization; Dr. Tanaka designs MoE routing; you evaluate end-to-end latency and quality tradeoffs.",
    ),
    ProjectIdea(
        title="Speculative Decoding Meets KV Cache Sharing",
        description="Use Prof. Patel's speculative decoding framework with a shared KV cache pool across draft and target models, reducing memory overhead by up to 40%.",
        suggested_venues=["MLSys", "OSDI", "ASPLOS"],
        skill_gap="Prof. Patel provides speculative decoding infra; you contribute KV cache optimization; jointly develop the shared-cache protocol.",
    ),
]

MOCK_CHAT_REPLIES: dict[str, str] = {
    "default": "Based on the research profiles of the scholars in this session, I can see several promising areas of overlap. Their combined expertise spans KV cache optimization, efficient attention mechanisms, and model compression — a powerful combination for tackling inference efficiency at scale. What specific aspect would you like to explore?",
    "project": "Here are some collaboration angles I see:\n\n1. **Adaptive Cache Management** — Combining eviction policies with long-context attention\n2. **Compression-Aware Serving** — Integrating quantization into the serving stack\n3. **Hybrid Speculative Decoding** — Using sparse MoE models as draft models\n\nWould you like me to elaborate on any of these?",
    "email": "Here's a draft outreach email:\n\n---\n\nSubject: Potential Collaboration on Inference Optimization\n\nDear Dr. Osei,\n\nI've been following your recent work on KV cache eviction policies with great interest. My research focuses on [your area], and I believe there's a compelling intersection between our approaches...\n\n---\n\nWould you like me to customize this further?",
}
