"""
Multi-Agent Research System (Modal + Supermemory + OpenAI)
==========================================================
Architecture:
  - Modal (Mistral-7B via vLLM) → Paper parsing, revisions
  - OpenAI (GPT-4o) → Synthesis + Validation
  - Supermemory → Paper cache + user profiles

Setup:
  1. modal deploy modal_server.py
  2. Set env vars: MODAL_ENDPOINT, OPENAI_API_KEY, SUPERMEMORY_API_KEY
  3. python agents.py "your research question"
"""

import os
import json
import hashlib
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI
from supermemory import Supermemory

# ============================================================================
# CONFIG
# ============================================================================

# Modal vLLM endpoint (set after `modal deploy modal_server.py`)
MODAL_ENDPOINT = os.getenv(
    "MODAL_ENDPOINT",
    "https://rohitnanjundareddy--research-agents-llm-serve.modal.run/v1",
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
SUPERMEMORY_API_KEY = os.getenv("SUPERMEMORY_API_KEY", "sm_12MzJsM1t8aQsKeqvofSgp_JGYDROEjSAFbevoelJWTwebCgTeVbsKUnaDnGoFdiTAjaFybJwMTjAUlYWSWtRlD")

modal_client = OpenAI(base_url=MODAL_ENDPOINT, api_key="not-needed", timeout=120.0, max_retries=2)
openai_client = OpenAI(api_key=OPENAI_API_KEY)
memory = Supermemory(api_key=SUPERMEMORY_API_KEY)

_modal_available = True

# ============================================================================
# LLM HELPERS
# ============================================================================

def modal_llm(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    global _modal_available
    if not _modal_available:
        return openai_llm(system_prompt, user_prompt, temperature)
    try:
        response = modal_client.chat.completions.create(
            model="/model", temperature=temperature, max_tokens=2048,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        )
        return response.choices[0].message.content
    except KeyboardInterrupt:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if any(kw in error_msg for kw in ["timeout", "connection", "refused", "resolve", "502", "503"]):
            _modal_available = False
            print(f"  🔴 Modal unavailable — falling back to OpenAI")
        return openai_llm(system_prompt, user_prompt, temperature)


def openai_llm(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4o", temperature=temperature,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
    )
    return response.choices[0].message.content


def parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_response": text}


# ============================================================================
# DATA TYPES
# ============================================================================

@dataclass
class PaperInfo:
    title: str
    authors: list[str]
    abstract: str
    url: str
    source: str
    full_text: str = ""
    parsed_context: str = ""
    relevance_score: float = 0.0
    key_findings: list[str] = field(default_factory=list)

    @property
    def memory_id(self) -> str:
        return hashlib.md5(self.title.lower().strip().encode()).hexdigest()[:16]


@dataclass
class ResearchState:
    query: str
    topic: str
    professors: list[str]
    papers: list[PaperInfo] = field(default_factory=list)
    parsed_results: list[PaperInfo] = field(default_factory=list)
    synthesized_answer: str = ""
    validation_result: dict = field(default_factory=dict)
    final_answer: str = ""
    iteration: int = 0


# ============================================================================
# AGENT 1: GATHERER — ArXiv only (fast)
# ============================================================================

class GathererAgent:
    def __init__(self, mem: Supermemory):
        self.memory = mem

    def run(self, state: ResearchState) -> ResearchState:
        import arxiv

        topic = state.topic
        professors = state.professors
        all_papers: list[PaperInfo] = []
        arxiv_client = arxiv.Client()

        # Professor papers
        for prof in professors:
            print(f"\n📚 [Gatherer] ArXiv — Professor '{prof}'...")
            try:
                search = arxiv.Search(query=f"au:{prof} AND {topic}", max_results=3, sort_by=arxiv.SortCriterion.Relevance)
                for result in arxiv_client.results(search):
                    all_papers.append(PaperInfo(
                        title=result.title, authors=[a.name for a in result.authors],
                        abstract=result.summary, url=result.pdf_url or "", source="arxiv_professor",
                    ))
                    print(f"  ✅ [Prof] {result.title[:70]}...")
            except Exception as e:
                print(f"  ⚠️ Failed: {e}")

        # Topic papers
        print(f"\n📚 [Gatherer] ArXiv — Topic: '{topic}'")
        try:
            search = arxiv.Search(query=topic, max_results=5, sort_by=arxiv.SortCriterion.Relevance)
            for result in arxiv_client.results(search):
                all_papers.append(PaperInfo(
                    title=result.title, authors=[a.name for a in result.authors],
                    abstract=result.summary, url=result.pdf_url or "", source="arxiv",
                ))
                print(f"  ✅ {result.title[:70]}...")
        except Exception as e:
            print(f"  ⚠️ ArXiv failed: {e}")

        # Supermemory cache
        print(f"\n🧠 [Gatherer] Checking cache...")
        try:
            cached = self.memory.search.memories(q=topic, container_tag="research_papers", limit=5)
            if cached.results:
                print(f"  📦 Found {len(cached.results)} cached papers")
                for mem in cached.results:
                    try:
                        data = json.loads(mem.memory or mem.chunk or "{}")
                        if data.get("title"):
                            all_papers.append(PaperInfo(
                                title=data["title"], authors=data.get("authors", []),
                                abstract=data.get("abstract", ""), url=data.get("url", ""),
                                source="supermemory_cache", parsed_context=data.get("parsed_context", ""),
                            ))
                    except (json.JSONDecodeError, KeyError):
                        pass
        except Exception as e:
            print(f"  ⚠️ Cache failed: {e}")

        # Deduplicate
        seen = set()
        unique = []
        for p in all_papers:
            key = p.title.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(p)

        source_priority = {"arxiv_professor": 0, "arxiv": 2, "supermemory_cache": 4}
        unique.sort(key=lambda p: source_priority.get(p.source, 5))

        # Cap at 8 papers max to keep parsing fast
        unique = unique[:8]

        print(f"\n📊 [Gatherer] {len(unique)} papers to parse")
        state.papers = unique
        return state


# ============================================================================
# AGENT 2: PARSER — PARALLEL Modal LLM calls (fast!)
# ============================================================================

class ParserAgent:
    def __init__(self, mem: Supermemory):
        self.memory = mem

    def _parse_one(self, paper: PaperInfo, query: str, index: int, total: int) -> PaperInfo:
        """Parse a single paper. Runs in a thread."""
        if paper.source == "supermemory_cache" and paper.parsed_context:
            paper.relevance_score = 7
            print(f"    ⚡ [{index}/{total}] Cached: {paper.title[:50]}...")
            return paper

        content = paper.full_text or paper.abstract
        if not content:
            return paper

        raw = modal_llm(
            system_prompt="""{
  "extraction_version": "v2_detailed",
  "paper_id": "Paper N",
  "paper_metadata": {
    "title": "Not reported",
    "authors": "Not reported",
    "year": "Not reported",
    "venue": "Not reported",
    "links": {
      "pdf": "Not reported",
      "code": "Not reported",
      "project_page": "Not reported"
    }
  },
  "query_context": {
    "user_query": "<user_query>",
    "paper_relevance": {
      "score_0_to_3": 0,
      "why_relevant": [
        "Evidence-based reason tied to query, or 'Not relevant'."
      ],
      "best_for_tags": [
        "implementation",
        "theory",
        "sota",
        "survey",
        "efficiency",
        "robustness",
        "data_scarce",
        "interpretability",
        "benchmarking"
      ]
    }
  },
  "high_level_summary": {
    "one_sentence": "Query-focused one-liner.",
    "what_problem_it_solves": "Not reported",
    "main_idea": "Not reported",
    "key_takeaways": [
      {
        "takeaway": "Short takeaway relevant to query.",
        "where_in_paper": "Sec/Fig/Table (if known)",
        "evidence_snippets": ["<=25 words", "<=25 words"]
      }
    ]
  },
  "contributions": [
    {
      "contribution": "Contribution stated or clearly supported by paper.",
      "where_in_paper": "Not reported",
      "evidence_snippets": ["<=25 words"]
    }
  ],
  "problem_setup": {
    "task_definition": "Not reported",
    "setting": "e.g., offline/online, supervised/RL, centralized/decentralized (if stated)",
    "assumptions": [
      {
        "assumption": "Not reported",
        "where_in_paper": "Not reported",
        "evidence_snippets": ["<=25 words"]
      }
    ],
    "scope_and_non_goals": [
      {
        "item": "Not reported",
        "where_in_paper": "Not reported"
      }
    ],
    "definitions_and_notation": [
      {
        "term": "Not reported",
        "definition": "Not reported",
        "where_in_paper": "Not reported",
        "evidence_snippets": ["<=25 words"]
      }
    ]
  },
  "method": {
    "method_name": "Not reported",
    "method_family": "e.g., transformer, diffusion, GNN, multi-agent, retrieval, optimization (if stated)",
    "core_components": [
      {
        "name": "Component/module name",
        "role": "What it does",
        "where_in_paper": "Not reported",
        "evidence_snippets": ["<=25 words"]
      }
    ],
    "architecture": {
      "backbone": "Not reported",
      "heads_or_modules": ["Not reported"],
      "losses_objectives": [
        {
          "name": "Not reported",
          "formula_or_description": "Not reported",
          "where_in_paper": "Not reported"
        }
      ]
    },
    "training": {
      "data_used_for_training": "Not reported",
      "optimization": "optimizer/lr/schedule if stated else Not reported",
      "hyperparameters": [
        {
          "name": "Not reported",
          "value": "Not reported",
          "unit": "Not reported",
          "where_in_paper": "Not reported"
        }
      ],
      "compute": {
        "hardware": "Not reported",
        "training_time": "Not reported",
        "params_or_model_size": "Not reported"
      }
    },
    "inference": {
      "inference_steps": ["Not reported"],
      "latency_or_throughput": "Not reported",
      "memory_notes": "Not reported"
    }
  },
  "data_and_benchmarks": {
    "datasets": [
      {
        "name": "Not reported",
        "type": "Not reported",
        "size": "Not reported",
        "splits": "Not reported",
        "preprocessing": "Not reported",
        "where_in_paper": "Not reported"
      }
    ],
    "evaluation_protocol": {
      "tasks": ["Not reported"],
      "metrics": ["Not reported"],
      "baselines": [
        {
          "name": "Not reported",
          "notes": "Not reported",
          "where_in_paper": "Not reported"
        }
      ]
    }
  },
  "results": {
    "headline_results": [
      {
        "task_or_dataset": "Not reported",
        "metric": "Not reported",
        "value": "Not reported",
        "unit": "Not reported",
        "direction": "higher_is_better/lower_is_better/Not reported",
        "baseline_comparison": {
          "baseline_name": "Not reported",
          "baseline_value": "Not reported",
          "delta": "Not reported"
        },
        "conditions": "model size / prompt / setting / split if stated",
        "where_in_paper": "Table/Fig/Sec",
        "evidence_snippets": ["<=25 words"]
      }
    ],
    "ablations_and_analysis": [
      {
        "what_changed": "Not reported",
        "observed_effect": "Not reported",
        "numbers_if_any": "Not reported",
        "where_in_paper": "Not reported"
      }
    ],
    "robustness_generalization": [
      {
        "test": "OOD / adversarial / noise / domain shift (if stated)",
        "result": "Not reported",
        "where_in_paper": "Not reported"
      }
    ],
    "efficiency_cost": [
      {
        "measure": "params/FLOPs/latency/$/memory",
        "value": "Not reported",
        "where_in_paper": "Not reported"
      }
    ],
    "all_reported_numbers": [
      {
        "value": "Not reported",
        "unit": "Not reported",
        "context": "What this number refers to",
        "where_in_paper": "Not reported"
      }
    ]
  },
  "limitations_and_risks": {
    "author_stated_limitations": [
      {
        "limitation": "Not reported",
        "type": "data/method/eval/compute/scope/ethical/other",
        "where_in_paper": "Not reported",
        "evidence_snippets": ["<=25 words"]
      }
    ],
    "constraints_for_use": [
      {
        "constraint": "Not reported",
        "impact": "Not reported",
        "where_in_paper": "Not reported"
      }
    ]
  },
  "practical_takeaways": {
    "when_to_use_this_paper": [
      {
        "use_case": "Not reported",
        "why": "Not reported",
        "evidence_snippets": ["<=25 words"]
      }
    ],
    "when_not_to_use": [
      {
        "case": "Not reported",
        "why": "Not reported"
      }
    ],
    "implementation_notes": {
      "code_available": "Yes/No/Not reported",
      "reproducibility_gaps": [
        {
          "missing_detail": "Not reported",
          "why_it_matters": "Not reported",
          "where_in_paper": "Not reported"
        }
      ]
    }
  },
  "traceability": {
    "key_tables_figures": [
      {
        "id": "Table 1 / Fig 2 / etc (if known)",
        "what_it_contains": "Not reported"
      }
    ],
    "sections_covered": ["Not reported"],
    "extraction_notes": [
      "If the retrieved context is partial, say: 'Partial retrieval: results section not included' etc."
    ]
  }
}""",
            user_prompt=f"QUERY: {query}\n\nPAPER: {paper.title}\nAUTHORS: {', '.join(paper.authors[:3])}\n\nCONTENT:\n{content[:4000]}",
        )

        result = parse_json_response(raw)
        extracted = result.get("extracted_info", "")
        methods = result.get("methods", "")
        results_text = result.get("results", "")
        limitations = result.get("limitations", "")

        paper.parsed_context = f"{extracted}\nMethods: {methods}\nResults: {results_text}\nLimitations: {limitations}".strip()
        paper.key_findings = result.get("key_contributions", [])

        if "professor" in paper.source:
            paper.relevance_score = 9
        elif len(paper.parsed_context) > 200:
            paper.relevance_score = 7
        else:
            paper.relevance_score = 4

        print(f"    ✅ [{index}/{total}] {paper.title[:50]}... ({len(paper.parsed_context)} chars)")

        # Cache in background
        try:
            self.memory.add(
                content=json.dumps({
                    "title": paper.title, "authors": paper.authors[:5],
                    "abstract": paper.abstract[:500], "url": paper.url,
                    "parsed_context": paper.parsed_context[:2000],
                    "key_findings": paper.key_findings, "original_query": query,
                }),
                container_tag="research_papers",
            )
        except Exception:
            pass

        return paper

    def run(self, state: ResearchState) -> ResearchState:
        query = state.query
        papers = state.papers
        total = len(papers)

        print(f"\n🔍 [Parser] Parsing {total} papers in PARALLEL via Modal LLM...")

        # Parse all papers in parallel (vLLM handles concurrent requests well)
        parsed = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._parse_one, paper, query, i + 1, total): paper
                for i, paper in enumerate(papers)
            }
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result.parsed_context or result.relevance_score > 0:
                        parsed.append(result)
                except Exception as e:
                    print(f"    ⚠️ Parse failed: {e}")

        parsed.sort(key=lambda p: (p.relevance_score, len(p.parsed_context)), reverse=True)
        state.parsed_results = parsed
        print(f"\n📊 [Parser] Done — {len(parsed)} papers parsed")
        return state


# ============================================================================
# AGENT 3: SYNTHESIZER — OpenAI GPT-4o
# ============================================================================

class SynthesizerAgent:
    def __init__(self, mem: Supermemory):
        self.memory = mem

    def run(self, state: ResearchState) -> ResearchState:
        query = state.query
        papers = state.parsed_results

        relevant = [p for p in papers if p.relevance_score >= 6]
        if not relevant:
            relevant = [p for p in papers if p.relevance_score >= 3][:5]
        if not relevant:
            relevant = papers[:3]
        relevant = relevant[:8]

        print(f"\n🧠 [Synthesizer] GPT-4o — {len(relevant)} papers...")

        user_ctx = self._get_profile(query)

        papers_block = ""
        for i, paper in enumerate(relevant):
            papers_block += f"""
--- Paper {i+1} ---
Title: {paper.title}
Authors: {', '.join(paper.authors[:5])}
URL: {paper.url}
Extracted Info: {paper.parsed_context}
Key Contributions: {', '.join(paper.key_findings) if paper.key_findings else 'See above'}
"""

        answer = openai_llm(
            system_prompt=f"""You are a Research Paper Reading-Recommender Agent running on top of a RAG system.

GOAL
Given (a) a USER_QUERY and (b) retrieved paper excerpts labeled Paper 1..N, recommend ONLY the 2–3 most valuable papers to read for that query, explain why with evidence, give a short topic overview, and a reading plan.

HARD RULES
1) Output TEXT ONLY. Do NOT output JSON.
2) DO NOT repeat, quote, summarize, or reformat any input wrappers like "SOURCES:", "ISSUES:", grading notes, logs, or debug text. Ignore them completely.
3) Recommend ONLY 2–3 papers total (no more).
4) Every non-trivial bullet must end with citations like [Paper N]. If multiple papers support it: [Paper 2][Paper 5].
5) Use ONLY what appears in the retrieved excerpts/metadata. Do NOT invent datasets, metrics, baselines, or comparisons.
6) If a detail is missing, write exactly: "Not reported in retrieved context." (and do not guess).
7) If you cannot confidently pick 2–3 papers (because excerpts lack method/dataset/results evidence), output the “NEED MORE RETRIEVAL” block (template below) and nothing else.

SELECTION CRITERIA (evidence-based)
Pick papers that best match the query by prioritizing:
- direct relevance to the query’s goal/task
- learnability (clear explanation / framing / diagrams / ablations if mentioned)
- evidence quality (explicit evaluation setup, datasets, metrics, results)

REQUIRED OUTPUT TEMPLATE (follow exactly; no extra sections)

TOPIC OVERVIEW (max 5 - 10 bullets depending on the topic and data)
- <bullet> [Paper N]
- ...

TOP 2–3 PAPERS TO READ
1) Paper <X> — <one-line why it’s a top pick> [Paper X]
   - Best for: <implementation/theory/SOTA/survey/efficiency/robustness/benchmarking> [Paper X]
   - Key idea: <1–2 lines> [Paper X]
   - Evidence: <method name + dataset/metric/result if present; else Not reported in retrieved context.> [Paper X]
   - What to read first: <Section/Figure/Table if mentioned; else Not reported in retrieved context.> [Paper X]
   - Time budget: <10-min skim OR 45-min read> [Paper X]

2) Paper <Y> — <one-line why it complements Paper X> [Paper Y]
   - Best for: <...> [Paper Y]
   - Key idea: <...> [Paper Y]
   - Evidence: <...> [Paper Y]
   - What to read first: <...> [Paper Y]
   - Time budget: <...> [Paper Y]

3) Paper <Z> — <only include if truly necessary> [Paper Z]
   - Best for: <...> [Paper Z]
   - Key idea: <...> [Paper Z]
   - Evidence: <...> [Paper Z]
   - What to read first: <...> [Paper Z]
   - Time budget: <...> [Paper Z]

READING ORDER
Paper <X> → Paper <Y> → Paper <Z if used>

DECISION GUIDE (max 4 lines)
- If your goal is <A>, start with Paper <N> because <reason>. [Paper N]
- If your goal is <B>, start with Paper <M> because <reason>. [Paper M]

WHAT’S MISSING (max 5 bullets)
- <missing item>
- ...

NEXT RETRIEVAL QUERIES (5–8 short queries)
- <query>
- ...

NEED MORE RETRIEVAL (use this ONLY if you cannot confidently pick 2–3 papers)
NEED MORE RETRIEVAL
Why: <1–2 lines; e.g., “results section not present / method details missing”>
Queries:
- <targeted query 1>
- <targeted query 2>
- ...

{f'User context: {user_ctx}' if user_ctx else ''}""",
            user_prompt=f"QUESTION: {query}\n\nPAPERS:\n{papers_block}\n\nComprehensive answer:",
        )

        print(f"  ✅ Answer generated ({len(answer)} chars)")

        try:
            self.memory.add(content=f"Researched: {query}", container_tag="research_user")
        except Exception:
            pass

        state.synthesized_answer = answer
        return state

    def _get_profile(self, query: str) -> str:
        try:
            result = self.memory.profile(container_tag="research_user", q=query, threshold=0.5)
            parts = []
            if result.profile.static:
                parts.append(f"Background: {', '.join(result.profile.static[:3])}")
            if result.profile.dynamic:
                parts.append(f"Focus: {', '.join(result.profile.dynamic[:3])}")
            return " | ".join(parts)
        except Exception:
            return ""


# ============================================================================
# AGENT 4: VALIDATOR — OpenAI GPT-4o
# ============================================================================

class ValidatorAgent:
    def run(self, state: ResearchState) -> ResearchState:
        print(f"\n🔎 [Validator] Checking (attempt {state.iteration + 1})...")

        sources = ""
        for i, paper in enumerate(state.parsed_results):
            if paper.relevance_score >= 3:
                sources += f"\n[Paper {i+1}]: {paper.parsed_context[:500]}"

        raw = openai_llm(
            system_prompt="""Strict validation. Catch hallucinations — claims not in sources.
Respond in JSON:
{"is_valid": bool, "confidence": 0.0-1.0, "hallucinated_claims": [], "issues": [], "suggestions": [], "verdict": "PASS" or "NEEDS_REVISION"}""",
            user_prompt=f"QUERY: {state.query}\n\nANSWER:\n{state.synthesized_answer}\n\nSOURCES:\n{sources}",
            temperature=0.0,
        )

        result = parse_json_response(raw)
        if "raw_response" in result:
            result = {"is_valid": True, "confidence": 0.7, "issues": [], "suggestions": [], "verdict": "PASS"}

        print(f"  📋 {result.get('verdict')} (confidence: {result.get('confidence')})")
        state.validation_result = result
        state.iteration += 1
        return state


# ============================================================================
# AGENT 5: REVISER — Modal LLM
# ============================================================================

class ReviserAgent:
    def run(self, state: ResearchState) -> ResearchState:
        print(f"\n✏️ [Reviser] Fixing issues...")

        sources = ""
        for i, paper in enumerate(state.parsed_results):
            if paper.relevance_score >= 3:
                sources += f"\n[Paper {i+1}]: {paper.parsed_context[:500]}"

        revised = modal_llm(
            system_prompt="Fix validation issues. Only use source data. Keep citations.",
            user_prompt=f"QUERY: {state.query}\n\nORIGINAL:\n{state.synthesized_answer}\n\nISSUES: {json.dumps(state.validation_result.get('issues', []))}\n\nSOURCES:\n{sources}\n\nRevised:",
        )

        print(f"  ✅ Revised ({len(revised)} chars)")
        state.synthesized_answer = revised
        return state


# ============================================================================
# ORCHESTRATOR
# ============================================================================

class ResearchOrchestrator:
    def __init__(self):
        self.gatherer = GathererAgent(memory)
        self.parser = ParserAgent(memory)
        self.synthesizer = SynthesizerAgent(memory)
        self.validator = ValidatorAgent()
        self.reviser = ReviserAgent()

    def run(self, query: str, topic: str | None = None, professors: list[str] | None = None) -> str:
        print("=" * 60)
        print("🚀 RESEARCH AGENTS (Modal + Supermemory + OpenAI)")
        print("=" * 60)
        print(f"  Query: {query}")
        print(f"  Topic: {topic or query}")
        print(f"  Professors: {professors or 'None'}")
        print("=" * 60)

        state = ResearchState(query=query, topic=topic or query, professors=professors or [])

        state = self.gatherer.run(state)
        if not state.papers:
            return "❌ No papers found. Try broader search terms."

        state = self.parser.run(state)
        state = self.synthesizer.run(state)

        while state.iteration < 3:
            state = self.validator.run(state)
            v = state.validation_result
            if v.get("verdict") == "PASS" and v.get("confidence", 0) >= 0.7:
                break
            if state.iteration >= 3:
                break
            state = self.reviser.run(state)

        return self._finalize(state)

    def _finalize(self, state: ResearchState) -> str:
        refs = "\n\n---\n## References\n"
        for i, paper in enumerate(state.parsed_results):
            if paper.relevance_score >= 3:
                authors = ", ".join(paper.authors[:3])
                refs += f"\n[Paper {i+1}] {paper.title} — {authors}\n  URL: {paper.url}\n"

        v = state.validation_result
        return (
            f"{state.synthesized_answer}{refs}\n---\n"
            f"**Validation**: {v.get('verdict', 'N/A')} (Confidence: {v.get('confidence', 'N/A')})\n"
            f"**LLM Usage**: Parser/Reviser=Modal(Mistral-7B) | Synthesizer/Validator=OpenAI(GPT-4o)\n"
        )


# ============================================================================
# PUBLIC API + CLI
# ============================================================================

def research(query: str, topic: str | None = None, professors: list[str] | None = None) -> str:
    return ResearchOrchestrator().run(query, topic, professors)

def search_memory(query: str, limit: int = 10) -> list[dict]:
    try:
        results = memory.search.memories(q=query, container_tag="research_papers", limit=limit)
        return [json.loads(m.memory or m.chunk or "{}") for m in (results.results or []) if m.memory or m.chunk]
    except Exception as e:
        print(f"Search failed: {e}")
        return []

def check_modal() -> bool:
    print(f"🔍 Checking Modal: {MODAL_ENDPOINT}")
    try:
        r = modal_client.chat.completions.create(
            model="/model", temperature=0, max_tokens=10,
            messages=[{"role": "user", "content": "Say OK"}],
        )
        print(f"   ✅ Modal running! Response: {r.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"   ❌ Not reachable: {e}")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Research Agents")
    parser.add_argument("query", nargs="?", default=None)
    parser.add_argument("--topic", "-t")
    parser.add_argument("--professors", "-p", nargs="+")
    parser.add_argument("--search-memory", "-m", action="store_true")
    parser.add_argument("--check-modal", action="store_true")
    args = parser.parse_args()

    if args.check_modal:
        check_modal()
    elif args.search_memory and args.query:
        papers = search_memory(args.query)
        for p in papers:
            print(f"  - {p.get('title', '?')}")
    elif args.query:
        answer = research(query=args.query, topic=args.topic, professors=args.professors)
        print("\n" + "=" * 60)
        print("📝 FINAL ANSWER")
        print("=" * 60)
        print(answer)
    else:
        parser.print_help()