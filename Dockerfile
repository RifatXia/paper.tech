# Stage 1: Build frontend
FROM node:18-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend + serve frontend
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/actiancortex-0.1.0b1-py3-none-any.whl /tmp/
RUN pip install --no-cache-dir /tmp/actiancortex-0.1.0b1-py3-none-any.whl && \
    rm /tmp/actiancortex-0.1.0b1-py3-none-any.whl

COPY backend/ .

# Copy built frontend into static/ so FastAPI serves it
COPY --from=frontend-build /frontend/dist ./static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
