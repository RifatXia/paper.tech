FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy and install actiancortex wheel
COPY actiancortex-0.1.0b1-py3-none-any.whl /tmp/
RUN pip install --no-cache-dir /tmp/actiancortex-0.1.0b1-py3-none-any.whl

# Copy backend code only
COPY backend/ .

# Install Python deps
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

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
