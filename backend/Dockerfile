FROM python:3.11-slim

WORKDIR /app

# Install system deps for psycopg and numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy wheel and install it first
COPY actiancortex-0.1.0b1-py3-none-any.whl /tmp/
RUN pip install --no-cache-dir /tmp/actiancortex-0.1.0b1-py3-none-any.whl

# Copy all backend code
COPY . .

# Install the project (reads pyproject.toml)
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "-m", "paper_tech_backend"]
