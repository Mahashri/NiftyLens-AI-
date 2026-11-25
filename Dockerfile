FROM node:22-bookworm-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip python3-venv && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PORT=8000
COPY . .
EXPOSE 8000
CMD ["sh","-c","uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
