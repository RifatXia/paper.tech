

"""
Deep Paper Analyzer v2 — Evidence-Anchored, Section-by-Section
===============================================================
Key improvements over v1:
  - Deterministic citation extraction (regex, not LLM guessing)
  - Evidence-anchored claims (every claim needs a verbatim quote)
  - Verifier pass drops unsupported claims
  - Smart content packing (tables/figures captured)
  - Full-text header detection for chunking
  - Real Level-2 refs via Semantic Scholar API
  - Anti-filler prompt rules ("would typically" → banned)

Usage:
  python deep_analyzer.py "https://arxiv.org/abs/2010.11929"
  python deep_analyzer.py 2312.xxxxx --output report.md
"""

import os
import re
import json
import time
import tempfile
import argparse
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from openai import OpenAI

# ============================================================================
# CONFIG
# ============================================================================

MODAL_ENDPOINT = os.getenv(
    "MODAL_ENDPOINT",
    "https://rohitnanjundareddy--research-agents-llm-serve.modal.run/v1",
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

modal_client = OpenAI(base_url=MODAL_ENDPOINT, api_key="not-needed", timeout=120.0, max_retries=2)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

_modal_available = True

# ============================================================================
# LLM HELPERS
# ============================================================================

def modal_llm(system: str, user: str, temp: float = 0.0, max_tok: int = 4096) -> str:
    global _modal_available
    if not _modal_available:
        return openai_llm(system, user, temp, max_tok)
    try:
        r = modal_client.chat.completions.create(
            model="/model", temperature=temp, max_tokens=max_tok,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        return r.choices[0].message.content
    except KeyboardInterrupt:
        raise
    except Exception as e:
        if any(k in str(e).lower() for k in ["timeout", "connection", "refused", "502", "503"]):
            _modal_available = False
            print("  🔴 Modal unavailable — using OpenAI")
        return openai_llm(system, user, temp, max_tok)


def openai_llm(system: str, user: str, temp: float = 0.0, max_tok: int = 4096) -> str:
    r = openai_client.chat.completions.create(
        model="gpt-4o", temperature=temp, max_tokens=max_tok,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return r.choices[0].message.content


def safe_json(text: str) -> dict | list:
    text = text.strip()
    if "```" in text:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if m:
            text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find a JSON object or array
        for pattern in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
            m = re.search(pattern, text)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
        return {"raw": text}


# ============================================================================
# DATA TYPES
# ============================================================================

@dataclass
class Reference:
    ref_id: str
    title: str
    authors: list[str] = field(default_factory=list)
    abstract: str = ""
    arxiv_id: str = ""
    url: str = ""
    level: int = 1
    key_contribution: str = ""
    bib_text: str = ""  # raw bibliography entry


@dataclass
class Claim:
    claim: str
    evidence_snippet: str  # verbatim <=25 words from section
    status: str = "PENDING"  # SUPPORTED / UNSUPPORTED


@dataclass
class NumberFact:
    value: str
    unit: str
    refers_to: str
    evidence_snippet: str


@dataclass
class Section:
    heading: str
    content: str
    start_idx: int = 0
    # Deterministically extracted
    cited_ref_ids: list[str] = field(default_factory=list)
    table_captions: list[str] = field(default_factory=list)
    figure_captions: list[str] = field(default_factory=list)
    # LLM-produced (evidence-anchored)
    summary: str = ""
    claims: list[Claim] = field(default_factory=list)
    numbers: list[NumberFact] = field(default_factory=list)
    ref_rationales: dict = field(default_factory=dict)  # ref_id -> why cited
    open_questions: list[str] = field(default_factory=list)
    key_takeaway: str = ""


@dataclass
class PaperAnalysis:
    title: str
    authors: list[str]
    abstract: str
    arxiv_id: str
    full_text: str
    sections: list[Section] = field(default_factory=list)
    references: dict = field(default_factory=dict)
    level2_references: dict = field(default_factory=dict)


# ============================================================================
# STEP 1: FETCHER
# ============================================================================

class PaperFetcher:
    def fetch(self, arxiv_input: str) -> PaperAnalysis:
        import arxiv as arxiv_lib

        arxiv_id = re.search(r"(\d{4}\.\d{4,5})", arxiv_input)
        if not arxiv_id:
            arxiv_id = re.search(r"([\w-]+/\d{7})", arxiv_input)
        arxiv_id = arxiv_id.group(1) if arxiv_id else arxiv_input.strip()

        print(f"\n📥 [Fetcher] Downloading: {arxiv_id}")
        client = arxiv_lib.Client()
        results = list(client.results(arxiv_lib.Search(id_list=[arxiv_id])))
        if not results:
            raise ValueError(f"Paper not found: {arxiv_id}")

        paper = results[0]
        print(f"  📄 {paper.title}")

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "paper.pdf")
            paper.download_pdf(dirpath=tmpdir, filename="paper.pdf")

            import fitz
            doc = fitz.open(pdf_path)
            text = "\n".join(page.get_text() for page in doc)
            doc.close()

        print(f"  📝 {len(text)} chars extracted")
        return PaperAnalysis(
            title=paper.title,
            authors=[a.name for a in paper.authors],
            abstract=paper.summary,
            arxiv_id=arxiv_id,
            full_text=text,
        )


# ============================================================================
# STEP 2: REFERENCE FINDER — Deterministic + Semantic Scholar Level-2
# ============================================================================

class ReferenceFinder:
    def find_references(self, analysis: PaperAnalysis) -> PaperAnalysis:
        print(f"\n🔗 [RefFinder] Extracting references...")

        # 1. Find raw bibliography section
        ref_section = self._get_bib_section(analysis.full_text)
        print(f"  📚 Bibliography section: {len(ref_section)} chars")

        # 2. Use LLM to parse bib into structured entries
        raw = modal_llm(
            system="""Parse the bibliography into a JSON array. For EACH entry extract:
- ref_id: the label (e.g. "[1]", "[Doe2020]")
- title: paper title
- authors: list of last names
- arxiv_id: if visible (e.g. "2010.11929"), else ""
- bib_text: the full raw entry text

Return ONLY a JSON array. No commentary.""",
            user=f"BIBLIOGRAPHY:\n{ref_section[:8000]}",
        )

        refs_list = safe_json(raw)
        if isinstance(refs_list, dict):
            refs_list = refs_list.get("references", refs_list.get("raw", []))
        if not isinstance(refs_list, list):
            refs_list = []

        for rd in refs_list:
            rid = rd.get("ref_id", "")
            if rid:
                analysis.references[rid] = Reference(
                    ref_id=rid, title=rd.get("title", "?"),
                    authors=rd.get("authors", []),
                    arxiv_id=rd.get("arxiv_id", ""),
                    bib_text=rd.get("bib_text", ""),
                    level=1,
                )

        print(f"  📖 Parsed {len(analysis.references)} references")

        # 3. Level 1: fetch abstracts (parallel via ArXiv)
        print(f"  🔍 Level 1: Fetching abstracts...")
        self._fetch_abstracts(analysis.references)
        found = sum(1 for r in analysis.references.values() if r.abstract)
        print(f"  ✅ L1: {found}/{len(analysis.references)} abstracts found")

        # 4. Level 2: use Semantic Scholar to get refs OF refs
        print(f"  🔍 Level 2: Following citations via Semantic Scholar...")
        self._fetch_level2(analysis)
        print(f"  ✅ L2: {len(analysis.level2_references)} deeper references")

        # 5. Get key contributions for all refs that have abstracts
        print(f"  🧠 Summarizing reference contributions...")
        self._summarize_refs(analysis)

        return analysis

    def _get_bib_section(self, text: str) -> str:
        for pattern in [r"\n\s*References\s*\n", r"\n\s*REFERENCES\s*\n", r"\n\s*Bibliography\s*\n"]:
            m = re.search(pattern, text)
            if m:
                return text[m.start():]
        return text[int(len(text) * 0.8):]

    def _fetch_abstracts(self, refs: dict, workers: int = 6):
        import arxiv as arxiv_lib

        def fetch_one(ref: Reference) -> Reference:
            client = arxiv_lib.Client()
            # Try by ID
            if ref.arxiv_id:
                try:
                    results = list(client.results(arxiv_lib.Search(id_list=[ref.arxiv_id])))
                    if results:
                        r = results[0]
                        ref.abstract = r.summary
                        ref.url = r.pdf_url or ""
                        ref.title = r.title
                        ref.authors = [a.name for a in r.authors]
                        return ref
                except Exception:
                    pass
            # Try by title
            if ref.title and ref.title != "?":
                try:
                    results = list(client.results(arxiv_lib.Search(
                        query=ref.title, max_results=1,
                        sort_by=arxiv_lib.SortCriterion.Relevance,
                    )))
                    if results and self._title_similar(ref.title, results[0].title):
                        r = results[0]
                        ref.abstract = r.summary
                        ref.url = r.pdf_url or ""
                        ref.authors = [a.name for a in r.authors]
                        return ref
                except Exception:
                    pass
            return ref

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(fetch_one, r): rid for rid, r in refs.items()}
            for f in as_completed(futs):
                try:
                    f.result()
                except Exception:
                    pass

    def _title_similar(self, a: str, b: str) -> bool:
        wa = set(re.sub(r"[^a-z0-9 ]", "", a.lower()).split())
        wb = set(re.sub(r"[^a-z0-9 ]", "", b.lower()).split())
        return len(wa & wb) / max(len(wa), len(wb), 1) > 0.5

    def _fetch_level2(self, analysis: PaperAnalysis):
        """Use Semantic Scholar API to get references OF cited papers."""
        key_refs = [r for r in analysis.references.values() if r.abstract][:7]

        for ref in key_refs:
            try:
                # Search Semantic Scholar by title
                resp = requests.get(
                    "https://api.semanticscholar.org/graph/v1/paper/search",
                    params={"query": ref.title, "limit": 1, "fields": "paperId,title"},
                    timeout=8,
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                papers = data.get("data", [])
                if not papers:
                    continue

                paper_id = papers[0]["paperId"]

                # Get that paper's references
                resp2 = requests.get(
                    f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references",
                    params={"fields": "title,abstract,externalIds,authors", "limit": 5},
                    timeout=8,
                )
                if resp2.status_code != 200:
                    continue

                for item in resp2.json().get("data", []):
                    cited = item.get("citedPaper", {})
                    if not cited or not cited.get("title"):
                        continue
                    l2_id = f"L2:{ref.ref_id}→{cited['title'][:25]}"
                    arxid = ""
                    ext = cited.get("externalIds", {})
                    if ext:
                        arxid = ext.get("ArXiv", "")
                    analysis.level2_references[l2_id] = Reference(
                        ref_id=l2_id, title=cited["title"],
                        authors=[a.get("name", "") for a in (cited.get("authors") or [])[:3]],
                        abstract=(cited.get("abstract") or "")[:500],
                        arxiv_id=arxid,
                        level=2,
                    )

                time.sleep(0.3)  # Rate limit
            except Exception:
                continue

    def _summarize_refs(self, analysis: PaperAnalysis):
        """Batch summarize key contributions for refs with abstracts."""
        all_refs = list(analysis.references.values()) + list(analysis.level2_references.values())
        refs_with_abs = [r for r in all_refs if r.abstract and not r.key_contribution]

        # Batch: send up to 8 refs at a time to LLM
        for i in range(0, len(refs_with_abs), 8):
            batch = refs_with_abs[i:i + 8]
            batch_input = ""
            for r in batch:
                batch_input += f"\n---\nID: {r.ref_id}\nTitle: {r.title}\nAbstract: {r.abstract[:400]}\n"

            raw = modal_llm(
                system="""For each paper, write its key contribution in exactly 1-2 sentences.
Return JSON: {"ref_id": "contribution sentence", ...}""",
                user=batch_input,
            )
            result = safe_json(raw)
            if isinstance(result, dict):
                for r in batch:
                    if r.ref_id in result:
                        r.key_contribution = result[r.ref_id]


# ============================================================================
# STEP 3: CHUNKER — Full-text deterministic header detection
# ============================================================================

class PaperChunker:
    # Common section header patterns
    HEADER_PATTERNS = [
        # "1 Introduction", "2.1 Related Work", "A. Appendix"
        r"^(\d+(?:\.\d+)*)\s+([A-Z][A-Za-z\s:&-]{2,60})\s*$",
        # "Introduction", "RELATED WORK"
        r"^(Abstract|Introduction|Related Work|Background|Methodology|Method|Methods|"
        r"Approach|Model|Architecture|Experiments?|Results?|Evaluation|Analysis|"
        r"Discussion|Conclusion|Conclusions|Limitations|Future Work|Acknowledgments?|"
        r"Appendix|Supplementary|Training|Implementation|Datasets?|Setup|Ablation)\s*$",
    ]

    def chunk(self, analysis: PaperAnalysis) -> PaperAnalysis:
        print(f"\n✂️ [Chunker] Detecting section boundaries...")
        text = analysis.full_text
        lines = text.split("\n")

        # Find all potential headers across ENTIRE text
        headers = []
        char_pos = 0
        for line_num, line in enumerate(lines):
            stripped = line.strip()
            for pat in self.HEADER_PATTERNS:
                if re.match(pat, stripped, re.IGNORECASE):
                    headers.append({"heading": stripped, "line": line_num, "pos": char_pos})
                    break
            char_pos += len(line) + 1

        # Deduplicate nearby headers (within 3 lines)
        deduped = []
        for h in headers:
            if not deduped or h["line"] - deduped[-1]["line"] > 3:
                deduped.append(h)
        headers = deduped

        if len(headers) < 3:
            print(f"  ⚠️ Only {len(headers)} headers found, using LLM fallback")
            headers = self._llm_fallback(text)

        print(f"  📑 Found {len(headers)} sections: {[h['heading'][:30] for h in headers]}")

        # Extract content between headers
        sections = []
        for i, h in enumerate(headers):
            start = h["pos"]
            end = headers[i + 1]["pos"] if i + 1 < len(headers) else len(text)
            content = text[start:end].strip()

            # Smart content packing for long sections
            content = self._smart_pack(content)

            section = Section(heading=h["heading"], content=content, start_idx=start)

            # Deterministically extract citations from this section
            section.cited_ref_ids = self._extract_citations(content)

            # Extract table/figure captions
            section.table_captions = re.findall(r"(?i)(Table\s+\d+[.:].{10,100})", content)
            section.figure_captions = re.findall(r"(?i)(Fig(?:ure)?\.?\s+\d+[.:].{10,100})", content)

            sections.append(section)

        analysis.sections = sections
        return analysis

    def _smart_pack(self, content: str, max_chars: int = 6000) -> str:
        """Keep beginning + table/figure regions + end instead of blind truncation."""
        if len(content) <= max_chars:
            return content

        # Always keep first 1500 chars
        parts = [content[:1500]]

        # Find and keep table/figure regions (±200 chars around each)
        for m in re.finditer(r"(?i)(Table|Figure|Fig\.)\s+\d+", content):
            start = max(0, m.start() - 200)
            end = min(len(content), m.end() + 500)
            parts.append(f"\n[...table/figure region...]\n{content[start:end]}")

        # Always keep last 1500 chars
        parts.append(f"\n[...]\n{content[-1500:]}")

        packed = "\n".join(parts)
        return packed[:max_chars]

    def _extract_citations(self, text: str) -> list[str]:
        """Deterministic regex extraction of citation IDs."""
        cites = set()
        # Numeric: [1], [2,3], [1-5]
        for m in re.finditer(r"\[(\d+(?:[,\s-]+\d+)*)\]", text):
            for num in re.findall(r"\d+", m.group(1)):
                cites.add(f"[{num}]")
        # Author-year: (Dosovitskiy et al., 2020)
        for m in re.finditer(r"\(([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s*\d{4})\)", text):
            cites.add(f"({m.group(1)})")
        return sorted(cites)

    def _llm_fallback(self, text: str) -> list[dict]:
        """LLM fallback for papers with non-standard formatting."""
        # Send first 2000 + middle 2000 + last 2000 chars to find headers
        sample = text[:2000] + "\n...\n" + text[len(text)//2:len(text)//2+2000] + "\n...\n" + text[-2000:]
        raw = modal_llm(
            system="""Find ALL section headings in this paper. Return JSON array:
[{"heading": "Introduction", "pos": approximate_character_position}]
Look at the ENTIRE text sample. Include Abstract, Introduction, all the way to Conclusion.""",
            user=f"PAPER TEXT SAMPLES:\n{sample}",
        )
        result = safe_json(raw)
        if isinstance(result, dict):
            result = result.get("sections", [])
        if isinstance(result, list):
            return [{"heading": h.get("heading", "?"), "pos": h.get("pos", 0), "line": 0} for h in result]
        return [{"heading": "Full Paper", "pos": 0, "line": 0}]


# ============================================================================
# STEP 4: DEEP PARSER — Evidence-anchored claims (parallel)
# ============================================================================

class DeepParser:
    def parse(self, analysis: PaperAnalysis) -> PaperAnalysis:
        print(f"\n🔬 [DeepParser] Analyzing {len(analysis.sections)} sections (evidence-anchored)...")

        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = {}
            for i, sec in enumerate(analysis.sections):
                # Build per-section reference context (only cited refs)
                ref_ctx = self._refs_for_section(sec, analysis)
                futs[ex.submit(self._analyze, sec, analysis.title, ref_ctx, i+1, len(analysis.sections))] = i

            for f in as_completed(futs):
                idx = futs[f]
                try:
                    analysis.sections[idx] = f.result()
                    print(f"    ✅ [{idx+1}/{len(analysis.sections)}] {analysis.sections[idx].heading[:40]}")
                except Exception as e:
                    print(f"    ⚠️ Section {idx+1} failed: {e}")

        return analysis

    def _refs_for_section(self, sec: Section, analysis: PaperAnalysis) -> str:
        """Build reference context for ONLY the refs cited in this section."""
        lines = []
        for cid in sec.cited_ref_ids:
            ref = analysis.references.get(cid)
            if ref:
                contrib = ref.key_contribution or ref.abstract[:200] or ref.bib_text[:150]
                lines.append(f"{cid} \"{ref.title}\": {contrib}")
        # Also include any level-2 refs connected to cited L1 refs
        for l2_id, l2_ref in analysis.level2_references.items():
            for cid in sec.cited_ref_ids:
                if cid in l2_id:
                    lines.append(f"  └─ {l2_ref.title} [cited by {cid}]: {l2_ref.key_contribution[:150]}")
        return "\n".join(lines) if lines else "(No reference details available for cited works)"

    def _analyze(self, sec: Section, title: str, ref_ctx: str, idx: int, total: int) -> Section:
        raw = modal_llm(
            system=f"""You are analyzing section "{sec.heading}" of the paper "{title}".

HARD RULES:
- NEVER say "would typically", "likely", "probably", "generally" without evidence.
- Every claim MUST include a verbatim evidence snippet (<=25 words) from the section text.
- If content is missing or unclear, write: "Not reported in extracted text."
- Only explain references that are ACTUALLY CITED in this section (listed below).
- Include ALL numbers, metrics, dataset names, model names you find.

REFERENCES CITED IN THIS SECTION:
{ref_ctx}

TABLE/FIGURE CAPTIONS FOUND:
{chr(10).join(sec.table_captions + sec.figure_captions) if (sec.table_captions or sec.figure_captions) else "(none)"}

Return ONLY valid JSON:
{{
    "section_summary": "3-5 sentence summary of what this section does. Ground every sentence.",
    "key_claims": [
        {{"claim": "specific claim", "evidence_snippet": "verbatim <=25 words from text", "where": "beginning/middle/end of section"}}
    ],
    "numbers": [
        {{"value": "0.82", "unit": "AUROC", "refers_to": "ViT-B on EMBED dataset", "evidence_snippet": "achieves 0.82 AUROC on..."}}
    ],
    "cited_refs": {json.dumps(sec.cited_ref_ids)},
    "why_cited": {{
        "[1]": "Cited because the section states: '<evidence from section text>'"
    }},
    "open_questions": ["questions raised but not answered in this section"],
    "key_takeaway": "the single most important point, grounded in evidence"
}}""",
            user=f"SECTION CONTENT:\n{sec.content[:5500]}",
            temp=0.0,
        )

        result = safe_json(raw)
        if isinstance(result, dict) and "raw" not in result:
            sec.summary = result.get("section_summary", "")
            sec.key_takeaway = result.get("key_takeaway", "")
            sec.open_questions = result.get("open_questions", [])
            sec.ref_rationales = result.get("why_cited", {})

            for c in result.get("key_claims", []):
                sec.claims.append(Claim(
                    claim=c.get("claim", ""),
                    evidence_snippet=c.get("evidence_snippet", ""),
                ))
            for n in result.get("numbers", []):
                sec.numbers.append(NumberFact(
                    value=n.get("value", ""),
                    unit=n.get("unit", ""),
                    refers_to=n.get("refers_to", ""),
                    evidence_snippet=n.get("evidence_snippet", ""),
                ))

        return sec


# ============================================================================
# STEP 4.5: VERIFIER — Drop unsupported claims
# ============================================================================

class Verifier:
    def verify(self, analysis: PaperAnalysis) -> PaperAnalysis:
        print(f"\n🔎 [Verifier] Checking claims against section text...")
        total_claims = 0
        dropped = 0

        for sec in analysis.sections:
            verified_claims = []
            for claim in sec.claims:
                total_claims += 1
                # Check if evidence snippet actually appears in section content
                snippet = claim.evidence_snippet.lower().strip()
                content_lower = sec.content.lower()

                if not snippet or len(snippet) < 5:
                    claim.status = "UNSUPPORTED"
                    dropped += 1
                elif snippet in content_lower:
                    claim.status = "SUPPORTED"
                    verified_claims.append(claim)
                else:
                    # Fuzzy: check if >=60% of words appear nearby
                    words = snippet.split()
                    found = sum(1 for w in words if w in content_lower)
                    if found / max(len(words), 1) >= 0.6:
                        claim.status = "SUPPORTED"
                        verified_claims.append(claim)
                    else:
                        claim.status = "UNSUPPORTED"
                        dropped += 1

            sec.claims = verified_claims

        print(f"  ✅ {total_claims - dropped}/{total_claims} claims verified, {dropped} dropped")
        return analysis


# ============================================================================
# STEP 5: EXPLAINER — Generate final markdown from fact store
# ============================================================================

class Explainer:
    def explain(self, analysis: PaperAnalysis) -> str:
        print(f"\n📝 [Explainer] GPT-4o generating final analysis...")

        # Build structured input from fact store (not raw text)
        sections_json = []
        for sec in analysis.sections:
            sections_json.append({
                "heading": sec.heading,
                "summary": sec.summary,
                "key_takeaway": sec.key_takeaway,
                "verified_claims": [
                    {"claim": c.claim, "evidence": c.evidence_snippet} for c in sec.claims
                ],
                "numbers": [
                    {"value": n.value, "unit": n.unit, "refers_to": n.refers_to} for n in sec.numbers
                ],
                "cited_refs": sec.cited_ref_ids,
                "why_cited": sec.ref_rationales,
                "tables_figures": sec.table_captions + sec.figure_captions,
                "open_questions": sec.open_questions,
            })

        # Build reference lookup
        ref_lookup = {}
        for rid, ref in analysis.references.items():
            ref_lookup[rid] = {
                "title": ref.title,
                "contribution": ref.key_contribution,
                "level2_refs": [],
            }
        for l2id, l2ref in analysis.level2_references.items():
            # Find parent
            for rid in analysis.references:
                if rid in l2id:
                    if rid in ref_lookup:
                        ref_lookup[rid]["level2_refs"].append({
                            "title": l2ref.title,
                            "contribution": l2ref.key_contribution,
                        })

        final = openai_llm(
            system="""You are writing a deep, section-by-section analysis of a research paper.
Your audience: a graduate student who is smart but may not know every cited work.

INPUT: You receive a structured JSON "fact store" — every claim has been verified against the paper text.

HARD RULES:
- NEVER write "would typically", "likely introduces", "generally". 
- If a section has no verified claims, write: "The extracted text did not contain sufficient detail for this section."
- For each cited reference: explain what it did AND why THIS paper cites it, using the rationale provided.
- Include ALL numbers/metrics from the numbers array.
- Show Level-2 reference chains: "This paper cites [X], which itself builds on [Y] for..."
- Use analogies where they help, but never at the expense of accuracy.

OUTPUT FORMAT (Markdown):
# Executive Summary
(3-4 sentences covering the paper's main contribution, approach, and key results)

## Section: [heading]
**What this section does**: (from summary)
**Key findings**:
- [claim] — *Evidence: "[snippet]"*
**Numbers & metrics**:
- [value] [unit] for [refers_to]
**Referenced works**:
- [ref_id] "[title]": [why cited]. This work [contribution]. It builds on [level-2 refs].
**Key takeaway**: ...
**Open questions**: ...

(repeat for each section)

## Reference Chain
Show how the key ideas build: Paper → cites [X] → which builds on [Y] → which pioneered [Z]

Write in clear, engaging prose. Be specific. No filler.""",
            user=json.dumps({
                "paper_title": analysis.title,
                "authors": analysis.authors[:5],
                "abstract": analysis.abstract,
                "sections": sections_json,
                "reference_lookup": ref_lookup,
            }, indent=2),
            max_tok=8000,
        )

        print(f"  ✅ Final analysis: {len(final)} chars")
        return final


# ============================================================================
# ORCHESTRATOR
# ============================================================================

def analyze_paper(arxiv_input: str, output_path: str | None = None) -> str:
    print("=" * 60)
    print("🔬 DEEP PAPER ANALYZER v2 (Evidence-Anchored)")
    print("=" * 60)
    t0 = time.time()

    analysis = PaperFetcher().fetch(arxiv_input)
    analysis = ReferenceFinder().find_references(analysis)
    analysis = PaperChunker().chunk(analysis)
    analysis = DeepParser().parse(analysis)
    analysis = Verifier().verify(analysis)
    final_md = Explainer().explain(analysis)

    # Build output
    header = f"""# Deep Analysis: {analysis.title}

**Authors**: {', '.join(analysis.authors[:5])}  
**ArXiv**: [{analysis.arxiv_id}](https://arxiv.org/abs/{analysis.arxiv_id})  
**References**: {len(analysis.references)} (Level 1) + {len(analysis.level2_references)} (Level 2)  
**Time**: {time.time() - t0:.0f}s

---

"""
    output = header + final_md

    # Reference appendix
    output += "\n\n---\n\n# Reference Appendix\n\n## Level 1: Directly Cited\n\n"
    for rid, ref in sorted(analysis.references.items()):
        if ref.key_contribution or ref.abstract:
            output += f"**{rid}**: {ref.title}\n"
            if ref.key_contribution:
                output += f"  - *Contribution*: {ref.key_contribution}\n"
            if ref.url:
                output += f"  - *URL*: {ref.url}\n"
            output += "\n"

    if analysis.level2_references:
        output += "## Level 2: Cited by Cited Papers\n\n"
        for l2id, ref in analysis.level2_references.items():
            output += f"**{ref.title}**\n"
            output += f"  - *Via*: {l2id}\n"
            if ref.key_contribution:
                output += f"  - *Contribution*: {ref.key_contribution}\n"
            output += "\n"

    # if output_path:
    #     Path(output_path).write_text(output, encoding="utf-8")
    #     print(f"\n💾 Saved to: {output_path}")

    print(f"\n✅ Done in {time.time() - t0:.0f}s | {len(analysis.sections)} sections | "
          f"{len(analysis.references)} L1 + {len(analysis.level2_references)} L2 refs")
    return output


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deep Paper Analyzer v2")
    parser.add_argument("paper", nargs="?", help="ArXiv URL or ID")
    parser.add_argument("--output", "-o", default="deep_analysis.md")
    parser.add_argument("--check-modal", action="store_true")
    args = parser.parse_args()

    if args.check_modal:
        try:
            r = modal_client.chat.completions.create(
                model="/model", temperature=0, max_tokens=10,
                messages=[{"role": "user", "content": "Say OK"}],
            )
            print(f"✅ Modal: {r.choices[0].message.content}")
        except Exception as e:
            print(f"❌ Modal: {e}")
    elif args.paper:
        analyze_paper(args.paper, output_path=args.output)
        print(f"\n📝 Open: {args.output}")
    else:
        parser.print_help()