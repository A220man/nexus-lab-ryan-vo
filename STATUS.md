# Checkpoint status

Work in progress; not a release-readiness or successful QA claim.

Version: 1.0.0

## Completed this round (sqlite-storage)

- SQLite persistent storage with SQLAlchemy ORM models:
  - `Session` model with project, name, status, platform_source, platform_session_id, metadata
  - `Observation` model with type enum, title, narrative, files_read/edited, content_hash dedup, occurrence_count
  - `SessionSummary` model with format, content, discovery_tokens, relevance_count
  - All with UUID primary keys, UTC timestamps, cascade deletes, foreign key constraints
- CRUD API endpoints for sessions and observations
- Observation deduplication by SHA-256 content hash with `occurrence_count` increment
- Bulk observation import
- Observation search by project, keyword, type
- Session filtering by project, status, platform_source
- 17 backend tests: all passing
- Fixed hardcoded version strings in tests (now derived from settings)
- Fixed package.json and package-lock.json version to match VERSION file (1.0.0)

## Verification

- Backend: 21/21 tests pass (`PYTHONPATH=backend .venv/bin/pytest backend/tests -v`)
- Frontend: 7/7 tests pass (`cd frontend && npm test`)
- Frontend build: succeeds (`cd frontend && npm run build`)

## Next round

Implement auth-oidc: Keycloak OIDC authorization-code flow with PKCE, backend session management,
protected endpoints, demo mode, and frontend login/logout.


Storage acceptance audit: CRUD source is retained, but sqlite-storage remains in progress. Current tests use an in-memory database; restart persistence and schema-upgrade migration behavior are not demonstrated. create_all initializes missing tables but does not implement schema-upgrade migrations. Complete and verify these acceptance criteria in a later storage feature round. This round selects core-skeleton for independent review.
