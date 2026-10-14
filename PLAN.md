# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

core-skeleton

## Roadmap

### core-skeleton — Core FastAPI/React Skeleton with Health Check

Status: in_progress

Acceptance:
- FastAPI backend starts and serves /api/health
- React + Vite frontend builds and loads
- Docker compose brings up both services
- Backend tests pass (pytest)
- Frontend typecheck and build pass

Implementation: `backend/app/main.py`, `backend/requirements.txt`, `backend/Dockerfile`, `frontend/package.json`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `compose.yaml`, `.github/workflows/ci.yml`

Tests: `backend/tests/test_health.py`, `frontend/src/App.test.tsx`

### sqlite-storage — SQLite Persistent Storage with Session/Observation Models

Status: planned

Acceptance:
- SQLAlchemy models for sessions, observations, summaries
- Migrations run on startup via introspection
- CRUD endpoints for sessions and observations
- Tests cover persistence and querying

### auth-oidc — OIDC Authentication with Keycloak

Status: planned

Acceptance:
- Keycloak integration in docker compose
- Login/logout flow with PKCE
- Protected API endpoints with role-based access
- Demo mode for local development

### observer-pipeline — Observer Response Pipeline with Classification

Status: planned

Acceptance:
- Output classifier with closed enum
- Policy table: preserve/confirm/abort per class
- Token budget enforcement on history
- Tests with recorded provider transcripts

### context-injection — Context Injection and Search Workflows

Status: planned

Acceptance:
- Semantic search over observations
- Context injection into new sessions
- Dashboard showing relevant memories
- Export/import workflows

### llm-adapters — LLM Provider Adapters (OpenAI-compatible, Anthropic, Gemini, Ollama)

Status: planned

Acceptance:
- Unified adapter interface
- Configurable provider/model/endpoint
- Bounded timeouts and redacted errors
- Keys only server-side

