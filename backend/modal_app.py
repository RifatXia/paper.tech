# """Modal app — deploys Qwen3 (vLLM) and MiniLM embeddings as HTTPS endpoints.

# Uses:
#   - Modal Volumes to cache HuggingFace model weights (no re-download)
#   - GPU memory snapshots to snapshot the loaded model in GPU memory
#     (cold starts restore from snapshot instead of re-loading weights)

# Usage:
#     cd backend
#     uv run modal setup                  # one-time auth (opens browser)
#     uv run modal deploy modal_app.py    # deploy → prints endpoint URLs

# Then add the printed URLs to your root .env:
#     MODAL_LLM_ENDPOINT=https://<your-username>--paper-tech-llmserver-v1-chat-completions.modal.run
#     MODAL_EMBED_ENDPOINT=https://<your-username>--paper-tech-embedserver-embed.modal.run
# """

# import modal

# # ── Modal app + volumes ────────────────────────────────────────

# app = modal.App("paper-tech")

# # Persistent volume for HuggingFace model weights cache.
# hf_cache_vol = modal.Volume.from_name("paper-tech-hf-cache", create_if_missing=True)
# HF_CACHE_DIR = "/root/.cache/huggingface"

# # ── Images ─────────────────────────────────────────────────────

# vllm_image = (
#     modal.Image.debian_slim(python_version="3.11")
#     .pip_install("vllm>=0.6", "torch>=2.1", "fastapi[standard]")
# )

# embed_image = (
#     modal.Image.debian_slim(python_version="3.11")
#     .pip_install("sentence-transformers>=3.0", "torch>=2.1", "fastapi[standard]")
# )

# # ── Configuration ──────────────────────────────────────────────

# # Swap to "Qwen/Qwen3-30B-A3B" + gpu="A100" for demo/production
# LLM_MODEL = "Qwen/Qwen3-4B"
# LLM_GPU = "A10G"

# EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# # ── LLM Inference Endpoint ────────────────────────────────────

# @app.cls(
#     image=vllm_image,
#     gpu=LLM_GPU,
#     timeout=300,
#     scaledown_window=120,
#     volumes={HF_CACHE_DIR: hf_cache_vol},
#     enable_memory_snapshot=True,
#     experimental_options={"enable_gpu_snapshot": True},
# )
# @modal.concurrent(max_inputs=10)
# class LLMServer:
#     @modal.enter(snap=True)
#     def load_model(self):
#         """Load model into GPU and snapshot the state.

#         This runs once during snapshot creation. On subsequent cold starts,
#         the container restores directly from the GPU memory snapshot —
#         skipping model download AND GPU loading entirely.
#         """
#         from vllm import LLM, SamplingParams

#         self.llm = LLM(
#             model=LLM_MODEL,
#             trust_remote_code=True,
#             enable_prefix_caching=True,
#         )
#         # Warm up with a sample forward pass so CUDA kernels are compiled
#         # and included in the snapshot.
#         self.llm.generate(
#             ["<|im_start|>user\nwarmup<|im_end|>\n<|im_start|>assistant\n"],
#             SamplingParams(max_tokens=1),
#         )
#         hf_cache_vol.commit()

#     @modal.fastapi_endpoint(method="POST", docs=True)
#     def v1_chat_completions(self, request: dict):
#         """OpenAI-compatible /v1/chat/completions endpoint."""
#         from vllm import SamplingParams

#         messages = request.get("messages", [])
#         max_tokens = request.get("max_tokens", 1024)
#         temperature = request.get("temperature", 0.7)

#         # Build ChatML prompt from messages
#         prompt_parts = []
#         for msg in messages:
#             role = msg.get("role", "user")
#             content = msg.get("content", "")
#             prompt_parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
#         prompt_parts.append("<|im_start|>assistant\n")
#         prompt = "\n".join(prompt_parts)

#         params = SamplingParams(
#             max_tokens=max_tokens,
#             temperature=temperature,
#             stop=["<|im_end|>"],
#         )
#         outputs = self.llm.generate([prompt], params)
#         text = outputs[0].outputs[0].text.strip()

#         return {
#             "id": "chatcmpl-modal",
#             "object": "chat.completion",
#             "choices": [
#                 {
#                     "index": 0,
#                     "message": {"role": "assistant", "content": text},
#                     "finish_reason": "stop",
#                 }
#             ],
#             "model": LLM_MODEL,
#         }


# # ── Embedding Endpoint ─────────────────────────────────────────

# @app.cls(
#     image=embed_image,
#     gpu="T4",
#     timeout=120,
#     scaledown_window=120,
#     volumes={HF_CACHE_DIR: hf_cache_vol},
#     enable_memory_snapshot=True,
#     experimental_options={"enable_gpu_snapshot": True},
# )
# class EmbedServer:
#     @modal.enter(snap=True)
#     def load_model(self):
#         """Load embedding model and snapshot GPU state."""
#         from sentence_transformers import SentenceTransformer

#         self.model = SentenceTransformer(EMBED_MODEL)
#         # Warm up with a sample encoding
#         self.model.encode(["warmup"], normalize_embeddings=True)
#         hf_cache_vol.commit()

#     @modal.fastapi_endpoint(method="POST", docs=True)
#     def embed(self, request: dict):
#         """Generate embeddings for a list of texts.

#         Request:  {"texts": ["text1", "text2", ...]}
#         Response: {"embeddings": [[0.1, ...], ...], "model": "...", "dim": 384}
#         """
#         texts = request.get("texts", [])
#         if not texts:
#             return {"embeddings": [], "model": EMBED_MODEL, "dim": 384}

#         embeddings = self.model.encode(texts, normalize_embeddings=True)
#         return {
#             "embeddings": embeddings.tolist(),
#             "model": EMBED_MODEL,
#             "dim": embeddings.shape[1],
#         }


"""
Modal vLLM Server — Optimized for Fast Startup
Key optimizations:
  1. Model weights baked INTO the container image (no runtime download)
  2. Minimum 1 container always warm (no cold starts)
  3. vLLM compilation cache persisted across restarts

Usage:
    python -m modal deploy modal_server.py    # Deploy (first time builds image ~10min)
    python -m modal run modal_server.py       # Test run
"""

import os
import subprocess

import modal

# ============================================================================
# CONFIG
# ============================================================================

MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.3"    # Proven with vLLM 0.9.1
# MODEL_NAME = "mistralai/Magistral-Small-2506"       # Newer Mistral, needs N_GPU=2
# MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"     # Needs HF approval

MODEL_DIR = "/model"          # Where weights live INSIDE the image
GPU_TYPE = "A100"
N_GPU = 1
VLLM_PORT = 8000
FAST_BOOT = True

APP_NAME = "research-agents-llm"

# ============================================================================
# MODAL APP
# ============================================================================

app = modal.App(APP_NAME)

# Only need cache volume now (weights are in the image)
cache_volume = modal.Volume.from_name(
    "research-llm-cache", create_if_missing=True
)

CACHE_DIR = "/cache"


# ============================================================================
# IMAGE: Bake model weights INTO the container image
# ============================================================================
# Weights are downloaded ONCE during `modal deploy` (image build),
# NOT on every container startup. Containers start in seconds, not minutes.

def download_model_to_image():
    """Runs during image build — downloads weights into the image layer."""
    from huggingface_hub import snapshot_download

    snapshot_download(
        MODEL_NAME,
        local_dir=MODEL_DIR,
        ignore_patterns=["*.pt", "*.bin"],  # prefer safetensors
        token=os.environ.get("HF_TOKEN"),
    )
    print(f"✅ Model {MODEL_NAME} baked into image at {MODEL_DIR}")


vllm_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "vllm==0.9.1",
        "huggingface_hub[hf_transfer]==0.32.0",
        "flashinfer-python==0.2.6.post1",
        extra_index_url="https://download.pytorch.org/whl/cu128",
    )
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "VLLM_USE_V1": "1",
    })
    .run_function(
        download_model_to_image,
        secrets=[modal.Secret.from_name("huggingface-secret")],
    )
)


# ============================================================================
# vLLM SERVER — Always-warm, OpenAI-Compatible
# ============================================================================

@app.function(
    image=vllm_image,
    gpu="A100",
    volumes={CACHE_DIR: cache_volume},
    secrets=[modal.Secret.from_name("huggingface-secret")],
    timeout=30 * 60,
    min_containers=1,
    max_containers=3,
    scaledown_window=600,
)
@modal.concurrent(max_inputs=100)
@modal.web_server(port=VLLM_PORT, startup_timeout=300)
def serve():
    """
    Launch vLLM as an OpenAI-compatible server.

    After deployment:
      https://<workspace>--research-agents-llm-serve.modal.run

    Use it like OpenAI:
      client = OpenAI(base_url="https://...modal.run/v1", api_key="not-needed")
    """
    cmd = [
        "vllm", "serve",
        MODEL_DIR,                        # Weights are already in the image!
        "--host", "0.0.0.0",
        "--port", str(VLLM_PORT),
        "--tensor-parallel-size", str(N_GPU),
        "--max-model-len", "8192",
    ]

    # enforce-eager = skip JIT compilation (faster boot, slightly slower inference)
    # For always-warm containers, set FAST_BOOT = False for better throughput
    cmd += ["--enforce-eager" if FAST_BOOT else "--no-enforce-eager"]

    print(f"🚀 Starting vLLM: {' '.join(cmd)}")
    subprocess.Popen(" ".join(cmd), shell=True)


# ============================================================================
# BATCH INFERENCE (for processing many papers at once)
# ============================================================================

@app.cls(
    image=vllm_image,
    gpu="A100",
    volumes={CACHE_DIR: cache_volume},
    secrets=[modal.Secret.from_name("huggingface-secret")],
    timeout=10 * 60,
    min_containers=0,
    scaledown_window=120,
)
class BatchInference:
    """
    Batch inference using vLLM's offline interface.
    Model loads ONCE per container via @modal.enter, stays loaded for all calls.
    """

    @modal.enter()
    def load_model(self):
        """Load model once when container starts — reused for all subsequent calls."""
        from vllm import LLM
        print(f"📦 Loading model from image: {MODEL_DIR}")
        self.llm = LLM(
            model=MODEL_DIR,
            tensor_parallel_size=N_GPU,
            enforce_eager=FAST_BOOT,
            max_model_len=8192,
        )
        print("✅ Model loaded and ready")

    @modal.method()
    def generate(self, prompts: list[str], max_tokens: int = 1024) -> list[str]:
        """
        Process a batch of prompts. Model is already loaded.

        Usage:
            batch = BatchInference()
            results = batch.generate.remote(["prompt1", "prompt2"])
        """
        from vllm import SamplingParams

        params = SamplingParams(
            temperature=0.2,
            max_tokens=max_tokens,
            top_p=0.95,
        )

        outputs = self.llm.generate(prompts, params)
        return [output.outputs[0].text for output in outputs]


# ============================================================================
# ENTRYPOINT FOR TESTING
# ============================================================================

@app.local_entrypoint()
def main():
    """Test the model with a sample prompt."""
    print("🧪 Testing batch inference (weights are pre-baked in image)...")

    test_prompts = [
        "You are a research paper parser. Given this abstract about Vision Transformers "
        "for medical imaging, extract the key findings in JSON format:\n\n"
        "Abstract: We present a novel approach using DINOv2 pretrained Vision Transformers "
        "for mammography-based breast cancer risk prediction. Our method achieves an AUROC "
        "of 0.82 on the EMBED dataset, outperforming ImageNet-pretrained baselines by 5%.\n\n"
        'Respond in JSON: {"key_findings": [...], "relevance_score": 0-10}',
    ]

    batch = BatchInference()
    results = batch.generate.remote(test_prompts)

    for prompt, result in zip(test_prompts, results):
        print(f"\n{'='*40}")
        print(f"Prompt: {prompt[:100]}...")
        print(f"Response: {result}")

    print("\n✅ Modal LLM is working!")
    print(f"Deploy with: python -m modal deploy modal_server.py")
    print(f"Endpoint: https://<workspace>--{APP_NAME}-serve.modal.run")
