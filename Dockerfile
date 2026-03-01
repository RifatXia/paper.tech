FROM python:3.12-slim

WORKDIR /app

# Copy backend source
COPY backend/ ./

# Install dependencies via pip from pyproject.toml
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
