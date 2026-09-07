# AGENTS.md — TechHunt Engineering Conventions

This document is the authoritative reference for anyone (human or AI agent)
contributing to TechHunt. Read this before writing any code.

---

## 1. Project Identity

- **Name**: TechHunt
- **Tagline**: "Find your next technical opportunity."
- **Mission**: Unified discovery platform for hackathons, contests, meetups,
  workshops, conferences, AI/ML events, open-source programs, fellowships,
  startup competitions, grants, and student opportunities — from legitimate
  sources only.

---

## 2. Monorepo Structure

```
techhunt/
  frontend/          Next.js 14 App Router, TypeScript, Tailwind CSS
  backend/           FastAPI + SQLAlchemy 2 + Alembic
  connectors/        EventConnector interface + source connectors
  database/          Alembic migrations and seed scripts
  docs/              Architecture docs, plans, ADRs
  docker-compose.yml
  .env.example       Placeholder names only — no real secrets
  README.md
  AGENTS.md          ← you are here
```

---

## 3. Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | Next.js 14, App Router | Pages in `frontend/app/` |
| Language | TypeScript (strict) | `"strict": true` in tsconfig |
| Styling | Tailwind CSS v3 | No inline styles; use class utilities |
| Backend | FastAPI, Python 3.12 | Async throughout |
| ORM | SQLAlchemy 2.x (async) | Never use synchronous session |
| Migrations | Alembic | One migration per schema change |
| Database | PostgreSQL 15 | All timestamps in UTC |
| Auth | JWT + bcrypt | `passlib[bcrypt]`, `python-jose` |
| Containers | Docker Compose v2 | |
| Backend tests | Pytest + anyio + httpx | |
| Frontend tests | Vitest + Testing Library | |

---

## 4. Architecture Decisions

### 4.1 Connector Architecture
- Every source connector extends `connectors/base.py::EventConnector`.
- Connectors expose: `fetch_events`, `normalize_event`, `validate_event`, `get_source_status`.
- Source-specific shapes **never** leak beyond the connector boundary.
- All connectors must implement: timeouts, retries, pagination, rate-limit awareness, logging.
- `mock` connector is always active. All other connectors are stubs until credentials confirmed.

### 4.2 Event Canonical Model
- One canonical `events` row per real-world event.
- Multiple `event_sources` rows may point at the same canonical event (dedup).
- All datetimes stored as UTC TIMESTAMPTZ; `original_timezone` string kept for display.

### 4.3 AI Abstraction
- AI enrichment lives in `backend/app/services/ai_service.py` (future).
- The service interface is provider-agnostic — swap OpenAI, Anthropic, local models without changing callers.
- AI API keys are **never** exposed to the frontend.
- AI-generated content is labelled as AI-generated in the UI.
- Recommendations are described as "personalized suggestions," not objective truth.

### 4.4 Configuration
- All config flows through `backend/app/core/config.py::Settings` (pydantic-settings).
- Secrets come from environment variables only. Never hard-code secrets.
- `NEXT_PUBLIC_*` variables are the only values sent to the browser — never put secrets there.

### 4.5 API Versioning
- All backend routes are prefixed `/api/v1/`.
- When breaking changes are needed, add `/api/v2/` routes — do not break v1.

---

## 5. Security Rules

These rules are non-negotiable:

1. **Never commit secrets.** `.env` is gitignored. `.env.example` has placeholder names only.
2. **No secrets in the frontend.** Only `NEXT_PUBLIC_*` variables are browser-safe.
3. **No ToS bypass.** Never bypass robots.txt, CAPTCHAs, anti-bot systems, paywalls, rate limits, or platform terms.
4. **Official sources only.** Use only official APIs, public permitted feeds, or organizer-submitted events.
5. **No fake integrations.** Never pretend a connector is live when it returns mock data. Label mock data clearly.
6. **Password hashing.** Use bcrypt via `passlib`. Never store plain-text passwords.
7. **Parameterized queries.** Use SQLAlchemy ORM only — never raw string SQL with user input.
8. **CORS.** In production, allow only `FRONTEND_URL`. Localhost variants are development-only.
9. **Input validation.** All request bodies validated via Pydantic schemas.
10. **Principle of least privilege.** DB user should have only the permissions it needs.

---

## 6. Coding Standards

### Python (backend + connectors)
- Python 3.12, type hints on every function signature.
- Async-first: use `async def` and `await` throughout. Never use sync DB calls on async paths.
- Follow PEP 8. Use `ruff` for linting and formatting.
- Maximum line length: 100 characters.
- Docstrings on all public functions, classes, and modules.
- Imports: stdlib → third-party → local, separated by blank lines.
- Exception handling: catch specific exceptions, not bare `except Exception` without logging.
- No `print()` statements — use the `logging` module.

### TypeScript (frontend)
- `"strict": true` in `tsconfig.json`. No `any` types — use `unknown` and narrow.
- Functional components only — no class components.
- Co-locate component styles with the component file using Tailwind classes.
- Prefer named exports. No default exports except Next.js pages/layouts.
- Use `const` unless mutation is necessary.
- API client lives in `frontend/lib/api.ts`. All backend calls go through it.
- No hardcoded backend URLs in component files.

### General
- Write the minimal change that solves the problem.
- No speculative features, no premature abstractions.
- Tests for every new public API endpoint and critical business logic.
- Self-describing variable and function names — avoid abbreviations.
- Every file has a module-level docstring (Python) or a comment header (TypeScript).

---

## 7. Git Conventions

- Branch naming: `feature/<short-description>`, `fix/<short-description>`, `chore/<short-description>`
- Commit messages: imperative mood, ≤72 chars subject line.
  - `feat: add GET /api/v1/events endpoint`
  - `fix: correct UTC offset in event normalization`
  - `chore: update requirements.txt`
- Never commit directly to `main`. Use pull requests.
- `.env` is gitignored — never commit it.

---

## 8. Key Commands

### Docker

```bash
# Start everything
docker compose up --build

# Start backend + DB only
docker compose up --build backend db

# Stop (keep volumes)
docker compose down

# Stop and wipe volumes
docker compose down -v

# View logs
docker compose logs -f backend
```

### Backend (local)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000    # dev server
pytest -v                                     # tests
ruff check .                                  # lint
ruff format .                                 # format
```

### Frontend (local)

```bash
cd frontend
npm install
npm run dev                                   # dev server
npm test                                      # vitest
npm run build                                 # production build
npm run lint                                  # eslint
```

### Alembic migrations

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1
```

---

## 9. Stage Roadmap (Summary)

| Stage | Scope |
|---|---|
| **1 ✅** | Scaffold, health endpoint, landing page, Docker, tests |
| 2 | DB schema, events API, auth |
| 3 | Mock ingestion, organizer submission, admin |
| 4 | AI enrichment, recommendations |
| 5 | Live connectors (per confirmed credentials), deduplication |
| 6 | Email, OAuth, maps, Sentry, PostHog |

**Do not implement a later stage until explicitly asked.**

---

## 10. Adding a New Connector

1. Create `connectors/<source_key>.py`.
2. Subclass `EventConnector` from `connectors/base.py`.
3. Set `source_key` and `requires_credentials`.
4. Implement all four abstract methods.
5. If credentials are not yet confirmed, implement `get_source_status()` returning `SourceStatusCode.STUB` and raise `NotImplementedError` in the other methods.
6. Document what permission/credential check is needed before activation.
7. Add a row to `event_sources` table when activating.
8. Write tests for `normalize_event` and `validate_event`.

---

## 11. Environment Variable Reference

| Variable | Backend | Frontend | Notes |
|---|---|---|---|
| `DATABASE_URL` | ✅ | ❌ | Never expose to browser |
| `POSTGRES_USER` | ✅ | ❌ | Docker Compose only |
| `POSTGRES_PASSWORD` | ✅ | ❌ | Secret — never commit |
| `POSTGRES_DB` | ✅ | ❌ | |
| `SECRET_KEY` | ✅ | ❌ | JWT signing — never expose |
| `FRONTEND_URL` | ✅ | ❌ | CORS origin |
| `NEXT_PUBLIC_API_BASE_URL` | ❌ | ✅ | Sent to browser — safe |
| `OPENAI_API_KEY` | ✅ | ❌ | Never expose to browser |
| `GOOGLE_CLIENT_ID` | ✅ | ❌ | Future OAuth |
| `GOOGLE_CLIENT_SECRET` | ✅ | ❌ | Secret — never expose |
| `GITHUB_CLIENT_ID` | ✅ | ❌ | Future OAuth |
| `GITHUB_CLIENT_SECRET` | ✅ | ❌ | Secret — never expose |
| `LUMA_API_KEY` | ✅ | ❌ | Not active until credentials confirmed |
| `MEETUP_API_KEY` | ✅ | ❌ | Not active until credentials confirmed |
