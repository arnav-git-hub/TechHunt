# TechHunt — Implementation Plan

> Version 1.0 · Status: Draft

---

## 1. Product Overview

**TechHunt** is a unified technical-opportunity discovery platform. Users find hackathons, coding contests, workshops, meetups, conferences, AI/ML events, open-source programs, fellowships, startup competitions, grants, and student opportunities from legitimate sources in one place.

**Tagline:** "Find your next technical opportunity."

---

## 2. Repository Layout

```
techhunt/                         ← monorepo root (this repo)
  frontend/                       ← Next.js 14 App Router, TypeScript, Tailwind
    app/                          ← App Router pages and layouts
    components/                   ← Shared UI components
    lib/                          ← API client, utilities
    hooks/                        ← React custom hooks
    types/                        ← Shared TypeScript types
    public/                       ← Static assets
  backend/                        ← FastAPI + SQLAlchemy + Alembic
    app/
      api/                        ← Route handlers (v1/)
      auth/                       ← JWT helpers, password hashing
      database/                   ← Engine, session, base declarative
      models/                     ← SQLAlchemy ORM models
      schemas/                    ← Pydantic request/response schemas
      services/                   ← Business logic
      utils/                      ← Shared utilities
      main.py                     ← FastAPI application factory
    tests/                        ← Pytest test suite
    requirements.txt
    Dockerfile
  connectors/                     ← Source connector library
    base.py                       ← Abstract EventConnector interface
    mock.py                       ← Mock connector (always present)
    luma.py                       ← Placeholder — not active
    meetup.py                     ← Placeholder — not active
    devpost.py                    ← Placeholder — not active
    unstop.py                     ← Placeholder — not active
    commudle.py                   ← Placeholder — not active
    devfolio.py                   ← Placeholder — not active
    mlh.py                        ← Placeholder — not active
    kaggle.py                     ← Placeholder — not active
  database/
    migrations/                   ← Alembic migration scripts
    seed/                         ← Seed scripts (no unverified data yet)
  docs/                           ← Architecture, plans, ADRs
  .env.example                    ← Variable names, no real values
  docker-compose.yml
  README.md
  AGENTS.md
```

---

## 3. Tech Stack Decisions

| Layer | Choice | Rationale |
|---|---|---|
| Frontend framework | Next.js 14 (App Router) | SSR, SSG, file-based routing, edge-ready |
| Frontend language | TypeScript (strict) | Type safety across the whole frontend |
| Styling | Tailwind CSS v3 | Utility-first, consistent design tokens |
| Backend framework | FastAPI | Async, OpenAPI auto-docs, Pythonic |
| Backend language | Python 3.12 | Type hints, modern async |
| ORM | SQLAlchemy 2.x (async) | Mature, migration-friendly |
| Migrations | Alembic | Schema version control |
| Database | PostgreSQL 15 | ACID, full-text search, JSONB |
| Auth (future) | JWT + bcrypt; OAuth via Authlib | Secure, extensible |
| Containerization | Docker Compose v2 | Reproducible local + CI environments |
| Tests (backend) | Pytest + httpx AsyncClient | Async-native, clear fixtures |
| Tests (frontend) | Vitest + Testing Library | Fast, co-located |
| API docs | FastAPI OpenAPI (auto) | Zero-extra-effort |
| AI abstraction | Provider-agnostic service interface | No vendor lock-in |

---

## 4. Data Model (Full Target)

### 4.1 Core tables

#### `users`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | TEXT NOT NULL | |
| email | TEXT UNIQUE NOT NULL | |
| password_hash | TEXT | nullable for OAuth users |
| role | ENUM(user, organizer, admin) | default: user |
| bio | TEXT | |
| location | TEXT | |
| experience_level | TEXT | |
| email_verified_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | server default: now() |
| updated_at | TIMESTAMPTZ | auto-updated |

#### `events`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| title | TEXT NOT NULL | |
| slug | TEXT UNIQUE NOT NULL | auto-generated |
| description | TEXT | |
| source | TEXT NOT NULL | connector identifier |
| source_event_id | TEXT | ID from originating source |
| canonical_event_id | UUID FK | → events.id (dedup) |
| event_url | TEXT | |
| image_url | TEXT | |
| organizer | TEXT | |
| opportunity_type | TEXT NOT NULL | hackathon, contest, meetup… |
| category | TEXT | |
| start_at_utc | TIMESTAMPTZ | |
| end_at_utc | TIMESTAMPTZ | |
| original_timezone | TEXT | |
| registration_deadline_utc | TIMESTAMPTZ | |
| location | TEXT | |
| city | TEXT | |
| state | TEXT | |
| country | TEXT | |
| latitude | NUMERIC | |
| longitude | NUMERIC | |
| is_online | BOOLEAN | default: false |
| eligibility | TEXT | |
| difficulty | TEXT | |
| price_type | ENUM(free, paid, unknown) | default: unknown |
| event_status | ENUM(draft, pending, published, rejected, archived, cancelled) | default: draft |
| ai_summary | TEXT | |
| published_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

#### Join / supporting tables
- `event_tags` (event_id, tag)
- `event_skills` (event_id, skill)
- `event_technologies` (event_id, technology)
- `user_interests` (user_id, interest)
- `user_skills` (user_id, skill)
- `saved_events` (user_id, event_id, saved_at)
- `notifications` (id, user_id, type, payload, read_at, created_at)
- `recommendations` (id, user_id, event_id, score, explanation, created_at)
- `organizer_submissions` (id, user_id, raw_payload, status, reviewed_by, created_at)
- `event_sources` (id, connector_key, label, status, last_run_at, config_json)
- `ingestion_runs` (id, source_id, started_at, finished_at, events_fetched, events_created, events_updated, errors)
- `admin_audit_logs` (id, admin_id, action, entity_type, entity_id, before_json, after_json, created_at)

---

## 5. Connector Architecture

```python
# connectors/base.py
class EventConnector(ABC):
    source_key: str           # unique identifier, e.g. "devpost"
    requires_credentials: bool

    async def fetch_events(self, **kwargs) -> list[RawEvent]: ...
    def normalize_event(self, raw: RawEvent) -> NormalizedEvent: ...
    def validate_event(self, event: NormalizedEvent) -> ValidationResult: ...
    def get_source_status(self) -> SourceStatus: ...
```

- **mock.py** — always active; returns deterministic fixture data; explicitly labelled "mock" in API responses.
- All other connectors are **placeholder stubs** that raise `NotImplementedError` with a clear message until credentials and permissions are confirmed.
- All connectors enforce: timeouts, exponential-backoff retries, pagination, rate-limit awareness, per-run logging.
- Source shapes never leak into the public API.

---

## 6. API Design (v1)

Base path: `/api/v1`

| Method | Path | Description | Stage |
|---|---|---|---|
| GET | `/health` | Health check (DB ping, version) | 1 |
| GET | `/events` | List events (paginated, filtered) | 2 |
| GET | `/events/{id}` | Event detail | 2 |
| POST | `/events/search` | Full-text + structured search | 3 |
| POST | `/auth/register` | Register with email/password | 2 |
| POST | `/auth/login` | Login, return JWT | 2 |
| GET | `/users/me` | Current user profile | 2 |
| POST | `/submissions` | Organizer event submission | 3 |
| GET | `/admin/sources` | List connector sources | 3 |
| POST | `/admin/ingest/{source}` | Trigger ingestion run | 3 |

---

## 7. Security Rules

1. Never commit secrets. `.env` is in `.gitignore`. `.env.example` contains only placeholder names.
2. Never expose `SECRET_KEY`, DB credentials, or API keys to the frontend.
3. All `NEXT_PUBLIC_*` variables are public by design — put only safe values there.
4. Do not bypass robots.txt, CAPTCHAs, anti-bot systems, paywalls, or rate limits.
5. Use only official APIs, permitted public feeds, or organizer-submitted events.
6. Password hashing: bcrypt via `passlib`.
7. JWT tokens: `python-jose`, short-lived access tokens + refresh tokens (future).
8. CORS: allow only `FRONTEND_URL` in production.
9. SQL injection: use parameterized queries via SQLAlchemy ORM only.
10. Rate limiting and input validation on all public endpoints (future: `slowapi`).

---

## 8. Stage Roadmap

| Stage | Scope | Status |
|---|---|---|
| **1** | Monorepo scaffold, health endpoint, landing page, Docker Compose, tests | **Complete** |
| 2 | DB schema + Alembic migrations, events API, auth (register/login/JWT), event list + detail pages | **Complete** |
| 3 | Mock connector ingestion, organizer submission flow, admin moderation, saved events, notifications | **Complete** |
| 4 | Provider-neutral AI enrichment interface, profile-based suggestions, NL event query | **Complete** |
| 5 | Live connector integrations (per confirmed credentials), deduplication, calendar export | Pending |
| 6 | Email reminders, OAuth (Google/GitHub), map view, Sentry, PostHog | Pending |

---

## 9. Stage 1 Checklist

- [ ] `techhunt/` monorepo directory structure
- [ ] `frontend/` — Next.js 14, TypeScript, Tailwind CSS
- [ ] `backend/` — FastAPI application skeleton
- [ ] `connectors/` — base interface + mock + stubs
- [ ] `docker-compose.yml` — frontend, backend, postgres services
- [ ] `backend/app/api/v1/health.py` — GET /health endpoint
- [ ] `frontend/lib/api.ts` — typed API client
- [ ] `frontend/.env.local.example` / root `.env.example`
- [ ] Landing page with brand, tagline, hero, search UI, filter chips, CTA, health status indicator
- [ ] `backend/tests/test_health.py` — pytest tests for health endpoint
- [ ] `README.md` — full setup guide
- [ ] `AGENTS.md` — conventions for future agents

---

## 10. Assumptions & Constraints

1. No live external connectors are activated until credentials and permission status are confirmed per connector.
2. Mock data is explicitly labelled "mock" and is deterministic (no random data).
3. AI provider abstraction is scaffolded (interface + config) but no provider key is used in Stage 1.
4. The frontend displays health status by calling the backend — this proves end-to-end connectivity.
5. All timestamps are stored as UTC; original timezone string retained for display.
6. Duplicate detection is designed for but not implemented in Stage 1.
7. Recommendation scores are described as "personalized suggestions," not objective truth.
