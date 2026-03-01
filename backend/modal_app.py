"""Modal app — deploys Qwen3 (vLLM) and MiniLM embeddings as HTTPS endpoints.

Uses:
  - Modal Volumes to cache HuggingFace model weights (no re-download)
  - GPU memory snapshots to snapshot the loaded model in GPU memory
    (cold starts restore from snapshot instead of re-loading weights)

Usage:
    cd backend
    uv run modal setup                  # one-time auth (opens browser)
    uv run modal deploy modal_app.py    # deploy → prints endpoint URLs

Then add the printed URLs to your root .env:
    MODAL_LLM_ENDPOINT=https://<your-username>--paper-tech-llmserver-v1-chat-completions.modal.run
    MODAL_EMBED_ENDPOINT=https://<your-username>--paper-tech-embedserver-embed.modal.run
"""

import modal

# ── Modal app + volumes ────────────────────────────────────────

app = modal.App("paper-tech")

# Persistent volume for HuggingFace model weights cache.
hf_cache_vol = modal.Volume.from_name("paper-tech-hf-cache", create_if_missing=True)
HF_CACHE_DIR = "/root/.cache/huggingface"

# ── Images ─────────────────────────────────────────────────────

vllm_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("vllm>=0.6", "torch>=2.1", "fastapi[standard]")
)

embed_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("sentence-transformers>=3.0", "torch>=2.1", "fastapi[standard]")
)

# ── Configuration ──────────────────────────────────────────────

# Swap to "Qwen/Qwen3-30B-A3B" + gpu="A100" for demo/production
LLM_MODEL = "Qwen/Qwen3-4B"
LLM_GPU = "A10G"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ── LLM Inference Endpoint ────────────────────────────────────

@app.cls(
    image=vllm_image,
    gpu=LLM_GPU,
    timeout=300,
    scaledown_window=120,
    volumes={HF_CACHE_DIR: hf_cache_vol},
    enable_memory_snapshot=True,
    experimental_options={"enable_gpu_snapshot": True},
)
@modal.concurrent(max_inputs=10)
class LLMServer:
    @modal.enter(snap=True)
    def load_model(self):
        """Load model into GPU and snapshot the state.

        This runs once during snapshot creation. On subsequent cold starts,
        the container restores directly from the GPU memory snapshot —
        skipping model download AND GPU loading entirely.
        """
        from vllm import LLM, SamplingParams

        self.llm = LLM(
            model=LLM_MODEL,
            trust_remote_code=True,
            enable_prefix_caching=True,
        )
        # Warm up with a sample forward pass so CUDA kernels are compiled
        # and included in the snapshot.
        self.llm.generate(
            ["<|im_start|>user\nwarmup<|im_end|>\n<|im_start|>assistant\n"],
            SamplingParams(max_tokens=1),
        )
        hf_cache_vol.commit()

    @modal.fastapi_endpoint(method="POST", docs=True)
    def v1_chat_completions(self, request: dict):
        """OpenAI-compatible /v1/chat/completions endpoint."""
        from vllm import SamplingParams

        messages = request.get("messages", [])
        max_tokens = request.get("max_tokens", 1024)
        temperature = request.get("temperature", 0.7)

        # Build ChatML prompt from messages
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
        prompt_parts.append("<|im_start|>assistant\n")
        prompt = "\n".join(prompt_parts)

        params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["<|im_end|>"],
        )
        outputs = self.llm.generate([prompt], params)
        text = outputs[0].outputs[0].text.strip()

        return {
            "id": "chatcmpl-modal",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                }
            ],
            "model": LLM_MODEL,
        }


# ── Embedding Endpoint ─────────────────────────────────────────

@app.cls(
    image=embed_image,
    gpu="T4",
    timeout=120,
    scaledown_window=120,
    volumes={HF_CACHE_DIR: hf_cache_vol},
    enable_memory_snapshot=True,
    experimental_options={"enable_gpu_snapshot": True},
)
class EmbedServer:
    @modal.enter(snap=True)
    def load_model(self):
        """Load embedding model and snapshot GPU state."""
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(EMBED_MODEL)
        # Warm up with a sample encoding
        self.model.encode(["warmup"], normalize_embeddings=True)
        hf_cache_vol.commit()

    @modal.fastapi_endpoint(method="POST", docs=True)
    def embed(self, request: dict):
        """Generate embeddings for a list of texts.

        Request:  {"texts": ["text1", "text2", ...]}
        Response: {"embeddings": [[0.1, ...], ...], "model": "...", "dim": 384}
        """
        texts = request.get("texts", [])
        if not texts:
            return {"embeddings": [], "model": EMBED_MODEL, "dim": 384}

        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return {
            "embeddings": embeddings.tolist(),
            "model": EMBED_MODEL,
            "dim": embeddings.shape[1],
        }
