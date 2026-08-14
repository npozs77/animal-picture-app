# Implementation Plan

## Build Order

| Step | Deliverable | Traces to |
|------|-------------|-----------|
| 1 | `pyproject.toml`, `.gitignore` | NFR-2, US-6 |
| 2 | `app/db.py` — schema, save, get_latest_batch, get_all, evict (all with db_path DI) | FR-DB.1, FR-DB.2 |
| 3 | `app/fetcher.py` — async HTTP fetch with retry + dimension jitter | FR-API.1 |
| 4 | `app/main.py` — FastAPI app, all endpoints, static mount | FR-API.1–4, FR-UI.1 |
| 5 | `app/static/index.html` — UI (fetch, latest, gallery) | FR-UI.1, FR-UI.2, US-1–3 |
| 6 | `tests/test_db.py` — persistence layer unit tests | NFR-5, FR-DB.1, FR-DB.2 |
| 7 | `tests/test_fetcher.py` — HTTP client + retry unit tests | NFR-5, FR-API.1 |
| 8 | `tests/test_api.py` — endpoint integration tests | NFR-5, US-6 |
| 9 | `Dockerfile` — astral-sh/uv image, .venv/bin/uvicorn CMD | NFR-3, US-5 |
| 10 | `Makefile` — dev, build, quality, test, lint, format check, docker-build, docker-run, clean | US-6 |
| 11 | `.github/workflows/ci.yml` — lint + test + docker build on push to main | NFR-6, US-6 |
| 12 | `README.md` — run instructions, approach, limitations, future work | US-5, US-6 |

## Key Implementation Decisions

| Decision | Why |
|----------|-----|
| `db_path` as explicit parameter (DI) | Testable without monkeypatching, clear data flow |
| `DB_PATH` env var with default | Configurable in Docker without code changes |
| Split tests into 3 files (db, fetcher, api) | Layered diagnosis — know exactly which component broke |
| `.venv/bin/uvicorn` in Dockerfile CMD | `uv run` attempts DNS lookups in network-restricted containers |
| Mock at external boundary only | Tests verify real app logic; only HTTP calls are faked |

## Dependencies (build-time)

| Package | Purpose |
|---------|---------|
| fastapi | Web framework, routing, validation |
| httpx | Async HTTP client for upstream APIs |
| uvicorn | ASGI server |
| pytest | Test runner |
| pytest-asyncio | Async test support |
| ruff | Linter |
