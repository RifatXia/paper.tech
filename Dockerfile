FROM python:3.11-slim

WORKDIR /app

# System deps needed by psycopg and numpy
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install the Actian VectorAI cortex SDK from local wheel
COPY actiancortex-0.1.0b1-py3-none-any.whl /tmp/
RUN pip install --no-cache-dir /tmp/actiancortex-0.1.0b1-py3-none-any.whl && \
    rm /tmp/actiancortex-0.1.0b1-py3-none-any.whl

# Install all Python dependencies in one layer
RUN pip install --no-cache-dir \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.30" \
    "pydantic-settings>=2.0" \
    "python-dotenv>=1.0" \
    "httpx>=0.27" \
    "openai>=1.0" \
    "psycopg[binary]>=3.1" \
    "numpy>=1.26" \
    "networkx>=3.2" \
    "supermemory>=0.1" \
    "google-genai>=1.0" \
    "sentence-transformers>=3.0"

# Copy only the backend source code into /app
# After this, /app contains: app/ db-scripts/ modal_app.py etc.
COPY backend/ .

EXPOSE 8000

# Direct uvicorn command — no module resolution, no pyproject.toml needed
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
