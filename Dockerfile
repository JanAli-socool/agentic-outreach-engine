# Multi stage build for smaller final image
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

RUN useradd -m -u 1000 agent && chown -R agent:agent /app

COPY --from=builder /root/.local /home/agent/.local
COPY --chown=agent:agent agent/ ./agent/
COPY --chown=agent:agent scripts/ ./scripts/
COPY --chown=agent:agent evals/ ./evals/

USER agent

ENV PATH=/home/agent/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /app/logs

CMD ["python", "-m", "scripts.run_evals"]