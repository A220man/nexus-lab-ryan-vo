# Changelog

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## [1.1.0] - 2026-10-17

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- SQLite persistent storage: SQLAlchemy models for `sessions`, `observations`, `session_summaries`
- CRUD API endpoints for sessions (`/api/sessions`) and observations (`/api/sessions/{id}/observations`)
- Observation deduplication by content hash with `occurrence_count` tracking
- Bulk observation import endpoint (`/api/observations/bulk-import`)
- Observation search across projects by keyword and type
- Session filtering by project, status, and platform source
- 17 backend tests covering all persistence workflows and cascade deletes
- **Alembic migration system initialized with initial schema migration**
- **Database initialization runs Alembic migrations with create_all fallback**
- **File-based SQLite persistence verified across application restarts**

### Fixed
- Backend version test: derive version from settings instead of hardcoding, preventing future drift
- Frontend `package-lock.json` version aligned with `VERSION` and `pyproject.toml`
## [1.0.0] - 2026-10-14

### Added
- Initial project scaffold: FastAPI backend, React + Vite frontend
- Docker Compose with PostgreSQL, Keycloak, ChromaDB, backend, frontend
- Health check endpoint (`GET /api/health`)
- Portfolio metadata (`portfolio.json`)
- CI workflow (backend tests, frontend build/test, Docker builds)
- Project documentation (README, architecture diagram, API reference)
- MIT License

### Security
- Demo mode restricted to localhost only
- LLM API keys server-side only
- OIDC tokens validated for signature, issuer, audience
