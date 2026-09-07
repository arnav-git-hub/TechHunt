# TechHunt

> **Find your next technical opportunity.**

TechHunt is a unified technical-opportunity discovery platform. It aggregates hackathons, coding contests, workshops, meetups, conferences, AI/ML events, open-source programs, fellowships, startup competitions, grants, and student opportunities from legitimate sources — all in one place.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          Browser                                │
│                   Next.js 14  (App Router)                      │
│               TypeScript · Tailwind CSS                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS / REST
┌──────────────────────────▼──────────────────────────────────────┐
│                     FastAPI  (Python 3.12)                      │
│           SQLAlchemy 2 · Alembic · Pydantic v2                  │
│                    /api/v1/*  endpoints                         │
└──────────┬──────────────────────────────┬───────────────────────┘
           │                              │
┌──────────▼──────────┐      ┌────────────▼────────────────────────┐
│   PostgreSQL 15      │      │       Connector Layer               │
│  (persistent data)  │      │  base.py  mock.py  [stubs…]         │
└─────────────────────┘      └────────────────────────────────────-┘
```

### Monorepo Layout

```
techhunt/
  frontend/          Next.js 14 App Router
  backend/           FastAPI application
  connectors/        Source connector library
  database/          Alembic migrations + seed scripts
  docs/              Architecture docs, plans, ADRs
  docker-compose.yml
  .env.example
  README.md
  AGENTS.md
```

---

## Prerequisites

| Tool | Minimum version |
|---|---|
| Docker Desktop (or Docker Engine + Compose v2) | 24.x |
| Node.js (for local frontend dev only) | 20.x LTS |
| Python (for local backend dev only) | 3.12 |
| Git | 2.x |

---

## Environment Setup

```bash
# 1. Clone the repository
git clone <repo-url> techhunt
cd techhunt

# 2. Create your local .env from the example
cp .env.example .env

# 3. Edit .env — fill in at minimum:
#    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, SECRET_KEY
#    Leave OAuth and connector keys empty for Stage 1.
#
#    Quick secret key generation:
#    python -c "import secrets; print(secrets.token_hex(32))"
```

> **Never commit `.env` to source control.**

---

## Running with Docker (recommended)

### Start all services

```bash
docker compose up --build
```

This starts:
- **PostgreSQL** on `localhost:5432`
- **FastAPI backend** on `localhost:8000`
- **Next.js frontend** on `localhost:3000`

### Start only the backend + database (useful during API development)

```bash
docker compose up --build backend db
```

### Run in detached mode

```bash
docker compose up --build -d
```

### View logs

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

### Stop and remove containers (keep data)

```bash
docker compose down
```

### Stop and remove containers **and volumes** (wipes DB data)

```bash
docker compose down -v
```

---

## Local Development (without Docker)

### Backend

```bash
cd backend

# Make the monorepo's connector package importable for local runs
# Windows PowerShell:
$env:PYTHONPATH = ".."
# macOS/Linux:
export PYTHONPATH=".."

# Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (or create a .env in backend/)
export DATABASE_URL="postgresql+asyncpg://techhunt:techhunt_dev@localhost:5432/techhunt"
export SECRET_KEY="dev-secret-change-in-production"
export FRONTEND_URL="http://localhost:3000"

# Start the development server (hot-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create local env file
cp .env.local.example .env.local
# Edit .env.local:
#   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Start the development server (hot-reload)
npm run dev
```

---

## Running Tests

### Backend

```bash
cd backend

# Install test dependencies (included in requirements.txt)
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_health.py -v
```

### Frontend

```bash
cd frontend

# Run Vitest unit tests
npm test

# Run with coverage
npm run test:coverage
```

---

## Key URLs

| URL | Description |
|---|---|
| `http://localhost:3000` | Frontend (landing page) |
| `http://localhost:8000/api/v1/health` | **Backend health check** |
| `http://localhost:8000/api/v1/events` | Published opportunities API |
| `http://localhost:8000/api/docs` | FastAPI interactive Swagger docs |
| `http://localhost:8000/api/redoc` | FastAPI ReDoc documentation |
| `http://localhost:8000/api/openapi.json` | OpenAPI JSON schema |

---

## Health Check

The health endpoint returns:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development",
  "uptime_seconds": 12.34,
  "database": "ok"
}
```

Verify manually:

```bash
curl http://localhost:8000/api/v1/health
```

---

## API Documentation

FastAPI auto-generates interactive documentation. With the backend running:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

---

## Connector Architecture

All source connectors implement the abstract `EventConnector` interface in [`connectors/base.py`](connectors/base.py).

- **`mock`** — always active; returns deterministic demo data labelled `[DEMO]`
- All other connectors are **placeholder stubs** that raise `NotImplementedError` until credentials and ToS compliance are confirmed

> TechHunt never bypasses robots.txt, anti-bot systems, CAPTCHAs, paywalls, rate limits, or platform terms of service.

---

## Stage Roadmap

| Stage | Status | Scope |
|---|---|---|
| **1** | ✅ Complete | Monorepo scaffold, health endpoint, landing page, Docker |
| 2 | ✅ Complete | DB schema, events API, auth (register/login/JWT) |
| 3 | ✅ Complete | Mock ingestion, organizer submissions, saved events, admin source controls |
| 4 | ✅ Complete | Provider-neutral AI enrichment interface, profile-based suggestions, natural-language event search |
| 5 | In progress | Deduplication and calendar export complete; live connectors await official credentials and permission |
| 6 | In progress | In-app reminders and map links complete; email, OAuth, Sentry, and PostHog await credentials |

---

## Contributing

See [`AGENTS.md`](AGENTS.md) for project conventions, architecture decisions, security rules, and coding standards.
