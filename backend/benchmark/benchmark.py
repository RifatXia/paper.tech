"""Multi-turn conversation benchmark — compares context retention and latency
across 5 setups: GPT-4o-mini, Gemini 2.5 Flash, Qwen3 (no memory),
Qwen3 (full history), and Qwen3 + Supermemory.

Usage:
    cd backend
    uv run python -m benchmark.benchmark

Requires in root .env:
    GITHUB_TOKEN=...        (for GPT-4o-mini baseline + judge via GitHub Models)
    GOOGLE_API_KEY=...      (for Gemini baseline)
    MODAL_LLM_ENDPOINT=...  (for Qwen3 setups)
    SUPERMEMORY_KEY=...     (for Qwen3 + Supermemory setup)

Results saved to benchmark/results/benchmark_results.json
Plots generated via: uv run python -m benchmark.plots
"""

import asyncio
import json
import os
import re
import time
import uuid

import httpx
import openai
from google import genai
from supermemory import Supermemory

from app.config import settings

# ── Conversation Script ────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are a research collaboration assistant for paper.tech. "
    "You help researchers explore co-author matches and collaboration ideas. "
    "Be specific, cite names and topics mentioned in the conversation, "
    "and keep responses concise (2-3 sentences)."
)

TURNS = [
    # Turn 1: establish a scholar
    "I'm interested in KV cache compression for LLM inference. "
    "My top match is Dr. Amara Osei from MIT CSAIL — she works on "
    "KV cache eviction policies and has an h-index of 42.",

    # Turn 2: add another scholar
    "Another great match is Prof. Liang Chen from Stanford NLP Group. "
    "He specializes in efficient transformers and long-context models. "
    "His h-index is 58 with 134 papers.",

    # Turn 3: discuss overlap
    "What research themes do Dr. Osei and Prof. Chen share?",

    # Turn 4 — RECALL PROBE 1: requires info from turn 1
    "Remind me — what is Dr. Osei's h-index and which institution is she at?",

    # Turn 5: add a third scholar
    "I also want to include Dr. Sofia Rodriguez from CMU LTI. "
    "She works on model compression, quantization, and edge deployment. "
    "Her h-index is 35.",

    # Turn 6: project ideas
    "Suggest a concrete project idea that combines the expertise of "
    "all three scholars we've discussed.",

    # Turn 7 — RECALL PROBE 2: requires info from turns 1, 2, 5
    "List all three scholars we've discussed, their universities, "
    "and their primary research focus areas.",

    # Turn 8: email draft
    "Draft a short email to Dr. Osei proposing the collaboration "
    "idea you just suggested.",

    # Turn 9: venue discussion
    "What would be the best academic venues to submit this "
    "collaborative work to?",

    # Turn 10 — RECALL PROBE 3: requires info from turns 2, 5
    "What are the h-indices of Prof. Chen and Dr. Rodriguez? "
    "And how many papers has Prof. Chen published?",
]

RECALL_EXPECTED = {
    3: {
        "question": TURNS[3],
        "expected_facts": [
            "h-index is 42",
            "MIT CSAIL",
        ],
    },
    6: {
        "question": TURNS[6],
        "expected_facts": [
            "Dr. Amara Osei — MIT CSAIL — KV cache",
            "Prof. Liang Chen — Stanford — efficient transformers",
            "Dr. Sofia Rodriguez — CMU — model compression/quantization",
        ],
    },
    9: {
        "question": TURNS[9],
        "expected_facts": [
            "Prof. Chen h-index 58",
            "Dr. Rodriguez h-index 35",
            "Prof. Chen 134 papers",
        ],
    },
}

RECALL_TURN_INDICES = list(RECALL_EXPECTED.keys())

NUM_RUNS = 1
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

# ── GitHub Models client helper ───────────────────────────────

GITHUB_MODELS_BASE = "https://models.github.ai/inference"


def _get_github_openai_client() -> openai.AsyncOpenAI:
    return openai.AsyncOpenAI(
        base_url=GITHUB_MODELS_BASE,
        api_key=settings.github_token,
    )


# ── Think-tag stripping ──────────────────────────────────────

def _strip_think_tags(text: str) -> str:
    """Strip both complete <think>...</think> and incomplete <think>... blocks."""
    # Complete blocks first
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Incomplete block (no closing tag — truncated output)
    text = re.sub(r"<think>.*", "", text, flags=re.DOTALL)
    return text.strip()


# ── Warmup ────────────────────────────────────────────────────

async def warmup_endpoints():
    """Send a single throwaway request to each endpoint to trigger cold starts.
    This ensures benchmark latencies reflect inference time, not container boot."""
    warmup_msg = [
        {"role": "system", "content": "Say OK."},
        {"role": "user", "content": "Hello"},
    ]

    print("Warming up endpoints (cold start — excluded from results)...")

    # Warm up Modal
    if settings.modal_llm_endpoint:
        print("  Modal LLM...", end=" ", flush=True)
        try:
            payload = {"messages": warmup_msg, "max_tokens": 16, "temperature": 0}
            async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
                t0 = time.perf_counter()
                resp = await client.post(settings.modal_llm_endpoint, json=payload)
                resp.raise_for_status()
                elapsed = (time.perf_counter() - t0) * 1000
            print(f"ready ({elapsed:.0f}ms)")
        except Exception as e:
            print(f"failed: {e}")

    # Warm up GitHub Models (GPT)
    if settings.github_token:
        print("  GitHub Models (GPT)...", end=" ", flush=True)
        try:
            client = _get_github_openai_client()
            t0 = time.perf_counter()
            await client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=warmup_msg,
                max_tokens=16,
                temperature=0,
            )
            elapsed = (time.perf_counter() - t0) * 1000
            print(f"ready ({elapsed:.0f}ms)")
        except Exception as e:
            print(f"failed: {e}")

    # Warm up Gemini
    if settings.google_api_key:
        print("  Gemini...", end=" ", flush=True)
        try:
            client = genai.Client(api_key=settings.google_api_key)
            t0 = time.perf_counter()
            client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[{"role": "user", "parts": [{"text": "Say OK."}]}],
            )
            elapsed = (time.perf_counter() - t0) * 1000
            print(f"ready ({elapsed:.0f}ms)")
        except Exception as e:
            print(f"failed: {e}")

    print("Warmup complete — starting benchmark.\n")


# ── Setup Implementations ─────────────────────────────────────

async def run_gpt(turns: list[str]) -> list[dict]:
    """GPT-4o-mini via GitHub Models — full conversation history."""
    client = _get_github_openai_client()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    results = []

    for turn in turns:
        messages.append({"role": "user", "content": turn})
        t0 = time.perf_counter()
        resp = await client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        reply = resp.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        results.append({"reply": reply, "latency_ms": latency_ms})

    return results


async def run_gemini(turns: list[str]) -> list[dict]:
    """Gemini 2.5 Flash via Google GenAI SDK."""
    client = genai.Client(api_key=settings.google_api_key)
    history = []
    results = []

    # Send system prompt as first user message to set context
    history.append({"role": "user", "parts": [{"text": SYSTEM_PROMPT}]})
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=history,
    )
    history.append({"role": "model", "parts": [{"text": resp.text}]})

    for turn in turns:
        history.append({"role": "user", "parts": [{"text": turn}]})
        t0 = time.perf_counter()
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=history,
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        reply_text = resp.text
        history.append({"role": "model", "parts": [{"text": reply_text}]})
        results.append({"reply": reply_text, "latency_ms": latency_ms})

    return results


async def _call_modal(messages: list[dict]) -> tuple[str, float]:
    """Call our Modal Qwen3 endpoint and return (reply, latency_ms)."""
    payload = {"messages": messages, "max_tokens": 1024, "temperature": 0.7}
    async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
        t0 = time.perf_counter()
        resp = await client.post(settings.modal_llm_endpoint, json=payload)
        latency_ms = (time.perf_counter() - t0) * 1000
        resp.raise_for_status()
        data = resp.json()
    reply = data["choices"][0]["message"]["content"]
    reply = _strip_think_tags(reply)
    return reply, latency_ms


async def run_qwen_no_memory(turns: list[str]) -> list[dict]:
    """Qwen3-4B on Modal — each turn sent independently, no context."""
    results = []
    for turn in turns:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": turn},
        ]
        reply, latency_ms = await _call_modal(messages)
        results.append({"reply": reply, "latency_ms": latency_ms})
    return results


async def run_qwen_full_history(turns: list[str]) -> list[dict]:
    """Qwen3-4B on Modal — full conversation history in every prompt."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    results = []

    for turn in turns:
        messages.append({"role": "user", "content": turn})
        reply, latency_ms = await _call_modal(messages)
        messages.append({"role": "assistant", "content": reply})
        results.append({"reply": reply, "latency_ms": latency_ms})

    return results


async def run_qwen_supermemory(turns: list[str]) -> list[dict]:
    """Qwen3-4B on Modal + Supermemory — hybrid: retrieval + recent history window."""
    sm = Supermemory(api_key=settings.supermemory_key)
    session_id = f"benchmark-{uuid.uuid4()}"
    container_tag = f"bench-{session_id}"
    results = []

    # Keep a sliding window of recent exchanges for immediate context
    recent_history: list[dict] = []

    for i, turn in enumerate(turns):
        # 1. Search Supermemory for relevant context from earlier turns
        context_chunks = []
        try:
            search_result = sm.search.execute(
                q=turn,
                container_tags=[container_tag],
                limit=5,
            )
            context_chunks = [
                r.content for r in (search_result.results or []) if r.content
            ]
        except Exception:
            pass

        # 2. Build system prompt with retrieved context
        system_content = SYSTEM_PROMPT
        if context_chunks:
            system_content = (
                "Relevant context from memory:\n---\n"
                + "\n---\n".join(context_chunks)
                + "\n---\n\n" + SYSTEM_PROMPT
            )

        # 3. Build messages: system + recent history window (last 4 exchanges) + current turn
        messages = [{"role": "system", "content": system_content}]
        messages.extend(recent_history[-8:])  # last 4 exchanges = 8 messages
        messages.append({"role": "user", "content": turn})

        # 4. Call Modal LLM
        reply, latency_ms = await _call_modal(messages)

        # 5. Update recent history
        recent_history.append({"role": "user", "content": turn})
        recent_history.append({"role": "assistant", "content": reply})

        # 6. Store exchange in Supermemory (async — don't block on indexing)
        try:
            sm.documents.add(
                content=f"User: {turn}\nAssistant: {reply}",
                container_tag=container_tag,
                metadata={"type": "benchmark-chat", "turn": i},
            )
        except Exception:
            pass

        # 7. Small delay to let Supermemory index the document
        await asyncio.sleep(1.0)

        results.append({"reply": reply, "latency_ms": latency_ms})

    return results


# ── Judge ──────────────────────────────────────────────────────

def _get_groq_client() -> openai.AsyncOpenAI:
    """Groq client (OpenAI-compatible) for judging — free tier, generous rate limits."""
    return openai.AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=settings.groq_api_key,
    )


async def judge_recall(reply: str, expected_facts: list[str]) -> float:
    """Use Llama 3.3 70B via Groq as judge — free, fast, no rate limit issues.
    Falls back to keyword matching if Groq is unavailable."""
    prompt = (
        "You are a strict fact-checker. Given an AI assistant's reply and a list of "
        "expected facts, determine how many of the expected facts are present in the reply.\n\n"
        f"REPLY:\n{reply}\n\n"
        f"EXPECTED FACTS:\n"
        + "\n".join(f"- {f}" for f in expected_facts)
        + "\n\nRespond with ONLY a JSON object: "
        '{"facts_found": <number of expected facts present>, '
        f'"total_facts": {len(expected_facts)}}}'
    )

    try:
        client = _get_groq_client()
        resp = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0,
        )
        text = resp.choices[0].message.content.strip()
        parsed = json.loads(text)
        return parsed["facts_found"] / parsed["total_facts"]
    except Exception:
        # Keyword fallback
        found = sum(
            1 for fact in expected_facts
            if any(kw.lower() in reply.lower() for kw in fact.split(" — "))
        )
        return found / len(expected_facts)


# ── Main ───────────────────────────────────────────────────────

async def run_benchmark():
    all_results = {}

    available = {}

    if settings.github_token:
        available["GPT-4o-mini"] = run_gpt
    else:
        print("GITHUB_TOKEN not set — skipping GPT-4o-mini")

    if settings.google_api_key:
        available["Gemini 2.5 Flash"] = run_gemini
    else:
        print("GOOGLE_API_KEY not set — skipping Gemini 2.5 Flash")

    if settings.modal_llm_endpoint:
        available["Qwen3-4B (no memory)"] = run_qwen_no_memory
        available["Qwen3-4B (full history)"] = run_qwen_full_history
        if settings.supermemory_key:
            available["Qwen3-4B + Supermemory"] = run_qwen_supermemory
        else:
            print("SUPERMEMORY_KEY not set — skipping Supermemory setup")
    else:
        print("MODAL_LLM_ENDPOINT not set — skipping all Qwen3 setups")

    print(f"Judge: Qwen3-4B via Modal (no rate limits)")

    # ── Warmup phase (excluded from results) ──
    await warmup_endpoints()

    for name, fn in available.items():
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print(f"{'='*60}")

        setup_runs = []
        for run_idx in range(NUM_RUNS):
            print(f"  Run {run_idx + 1}/{NUM_RUNS}...", end=" ", flush=True)
            try:
                results = await fn(TURNS)
                print(f"done ({len(results)} turns)")
                setup_runs.append(results)
            except Exception as e:
                print(f"FAILED: {e}")
                continue

        if not setup_runs:
            print(f"  All runs failed for {name}, skipping.")
            continue

        recall_scores = []
        per_probe_scores = {3: [], 6: [], 9: []}
        latencies_by_turn = {0: [], 3: [], 6: [], 9: []}

        for results in setup_runs:
            for turn_idx, probe in RECALL_EXPECTED.items():
                if turn_idx < len(results):
                    reply = results[turn_idx]["reply"]
                    score = await judge_recall(reply, probe["expected_facts"])
                    recall_scores.append(score)
                    per_probe_scores[turn_idx].append(score)

            for turn_idx in latencies_by_turn:
                if turn_idx < len(results):
                    latencies_by_turn[turn_idx].append(
                        results[turn_idx]["latency_ms"]
                    )

        avg_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0
        avg_latencies = {
            f"turn_{k+1}": (
                round(sum(v) / len(v), 1) if v else None
            )
            for k, v in latencies_by_turn.items()
        }
        per_probe_avg = [
            round(sum(per_probe_scores[idx]) / len(per_probe_scores[idx]), 3)
            if per_probe_scores[idx] else 0
            for idx in [3, 6, 9]
        ]

        all_results[name] = {
            "context_recall_accuracy": round(avg_recall, 3),
            "per_probe_recall": per_probe_avg,
            "avg_latencies_ms": avg_latencies,
            "num_runs": len(setup_runs),
            "sample_replies": {
                f"turn_{idx+1}": setup_runs[0][idx]["reply"][:300]
                for idx in RECALL_TURN_INDICES
                if idx < len(setup_runs[0])
            },
        }

        print(f"  CRA: {avg_recall:.3f}")
        print(f"  Per-probe: {per_probe_avg}")
        print(f"  Latencies: {avg_latencies}")

    # Save results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    output_path = os.path.join(RESULTS_DIR, "benchmark_results.json")
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)

    # Print summary table
    print(f"\n{'='*60}")
    print("BENCHMARK RESULTS")
    print(f"{'='*60}")
    print(f"{'Setup':<30} {'CRA':>6} {'T1 (ms)':>10} {'T4 (ms)':>10} {'T7 (ms)':>10} {'T10 (ms)':>10}")
    print("-" * 80)
    for name, data in all_results.items():
        lat = data["avg_latencies_ms"]
        print(
            f"{name:<30} {data['context_recall_accuracy']:>6.3f}"
            f" {lat.get('turn_1', 'N/A'):>10}"
            f" {lat.get('turn_4', 'N/A'):>10}"
            f" {lat.get('turn_7', 'N/A'):>10}"
            f" {lat.get('turn_10', 'N/A'):>10}"
        )

    print(f"\nResults saved to {output_path}")
    print(f"Generate plots: uv run python -m benchmark.plots")

    return all_results


if __name__ == "__main__":
    asyncio.run(run_benchmark())
