# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

auth-oidc

## Roadmap

### core-skeleton — Core FastAPI/React Skeleton with Health Check

Status: done

Acceptance:
- FastAPI backend starts and serves /api/health
- React + Vite frontend builds and loads
- Docker compose brings up both services
- Backend tests pass (pytest)
- Frontend typecheck and build pass

Implementation: `backend/app/main.py`, `backend/requirements.txt`, `backend/Dockerfile`, `frontend/package.json`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `compose.yaml`, `.github/workflows/ci.yml`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/security.py`, `backend/app/models/base.py`, `backend/app/api/health.py`, `backend/tests/conftest.py`, `frontend/src/test/setup.ts`, `frontend/index.html`, `frontend/vite.config.ts`, `frontend/nginx.conf`

Tests: `backend/tests/test_health.py`, `frontend/src/App.test.tsx`

### sqlite-storage — SQLite Persistent Storage with Session/Observation Models

Status: done

Acceptance:
- SQLAlchemy models for sessions, observations, summaries
- Database initialized on startup via Alembic migrations with create_all fallback
- CRUD endpoints for sessions and observations
- Tests cover persistence, querying, cascade deletes, and deduplication
- File-based SQLite persistence verified across restarts

Implementation: `backend/app/models/session.py`, `backend/app/models/__init__.py`, `backend/app/services/session_service.py`, `backend/app/services/observation_service.py`, `backend/app/services/__init__.py`, `backend/app/api/sessions.py`, `backend/app/api/observations.py`, `backend/app/api/__init__.py`, `backend/app/core/database.py`, `backend/alembic/env.py`, `backend/alembic/versions/e7d022b5483d_initial_migration.py`, `alembic.ini`

Tests: `backend/tests/test_sessions.py`, `backend/tests/conftest.py`

### auth-oidc — OIDC Authentication with Keycloak

Status: in_progress

Acceptance:
- Keycloak integration in docker compose
- Login/logout flow with PKCE
- Protected API endpoints with role-based access
- Demo mode for local development

Implementation: `backend/app/core/oidc.py`, `backend/app/api/auth.py`, `backend/app/core/security.py`, `backend/app/api/sessions.py`, `backend/app/api/observations.py`, `backend/app/main.py`, `backend/app/api/__init__.py`, `frontend/src/auth.ts`, `frontend/src/api.ts`, `frontend/src/components/Login.tsx`, `frontend/src/components/UserMenu.tsx`, `frontend/src/App.tsx`, `frontend/src/App.css`

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

