# Backend Dockerfile — multi-stage, production-ready
# Stage 1 (builder): install dependencies into a virtual environment
# Stage 2 (runtime): copy only the venv and application code

# ── Builder ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tooling
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first for layer caching
COPY backend/requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Runtime ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app/backend

# Runtime system deps (libpq for asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application, connector, and migration sources from the monorepo root.
COPY backend /app/backend
COPY connectors /app/connectors
COPY database /app/database
COPY alembic.ini /app/alembic.ini
ENV PYTHONPATH="/app:/app/backend"

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

EXPOSE 8000

# Uvicorn with sensible defaults; override via env in docker-compose
CMD ["sh", "-c", "alembic -c /app/alembic.ini upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
