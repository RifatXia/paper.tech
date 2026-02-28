"""Modal app — deploys Qwen3 (vLLM) and MiniLM embeddings as HTTPS endpoints.

Uses Modal Volumes to cache model weights — first deploy downloads them once,
subsequent cold starts load from the volume instead of re-downloading.

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
# First cold start downloads weights here; all future cold starts
# load from the volume (~seconds instead of ~minutes).
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
)
@modal.concurrent(max_inputs=10)
class LLMServer:
    @modal.enter()
    def load_model(self):
        from vllm import LLM
        self.llm = LLM(
            model=LLM_MODEL,
            trust_remote_code=True,
            enable_prefix_caching=True,
        )
        # Commit any newly downloaded weights to the volume so
        # the next cold start doesn't re-download them.
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
)
class EmbedServer:
    @modal.enter()
    def load_model(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(EMBED_MODEL)
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
