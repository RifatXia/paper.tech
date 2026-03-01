FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY actiancortex-0.1.0b1-py3-none-any.whl /tmp/
RUN pip install --no-cache-dir /tmp/actiancortex-0.1.0b1-py3-none-any.whl && \
    rm /tmp/actiancortex-0.1.0b1-py3-none-any.whl

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
