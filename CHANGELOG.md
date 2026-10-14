# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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