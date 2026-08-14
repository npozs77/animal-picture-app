# Animal Picture App

A microservice that fetches random pictures of cats, dogs, and bears from external image APIs, stores them in SQLite, and serves them via a REST API and simple web UI.

## Run locally

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 in your browser.

## Run with Docker

```bash
docker buildx build -t animal-picture-app .
docker run --rm -p 8000:8000 animal-picture-app
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/fetch` | Fetch & store pictures. Body: `{"animal": "cat", "count": 3}` |
| GET | `/latest/{animal}` | Returns all pictures from the last fetch call as JSON (base64 array + count) |
| GET | `/pictures/{animal}` | Returns all stored pictures for that animal as JSON (up to 25) |

Animals: `cat`, `dog`, `bear`. Count: 1–5. Retries failed fetches up to 2 times per image. Retains last 5 fetch calls per animal.

## Development

```bash
make quality    # lint + format check + tests (all-in-one)
make lint       # ruff check
make fmt-check  # ruff format --check
make test       # pytest
make dev        # uvicorn with --reload
make clean      # remove DB and caches
```

## Approach

I used a lightweight, simplified version of **Spec-Driven Development** to demonstrate the methodology — see `docs/` for the requirements, design, and implementation plan that preceded the code. The idea: think before typing, verify requirements with the stakeholder, trace every feature back to a decision.

- `docs/requirements.md` — functional/non-functional requirements + user stories
- `docs/design.md` — architecture, schema, endpoint contracts, key decisions
- `docs/plan.md` — build order + test strategy with traceability
- `docs/test-strategy.md` — requirement→test mapping and layered test approach

**Stack rationale:** FastAPI for async + auto-validation, sqlite3 stdlib for zero-setup persistence, httpx for async HTTP with retry, uv for fast dependency management, single-stage Docker on the official `astral-sh/uv` image.

## What I'd add with more time

- **Exponential backoff** on retries (currently fixed retry, no delay between attempts)
- **Health check** endpoint for container orchestration
- **Rate limiting** to protect upstream APIs
- **Structured logging** (JSON) for production observability
- **Integration tests** hitting the real APIs (guarded by an env flag)
- **Image metadata** (dimensions, file size, fetch timestamp) in the API response
- **Postgres** for production (concurrent writes, proper backups)

## Known limitations

- Bear pictures come from placebear.com's small fixed pool (~10 images) — expect occasional repeats
- SQLite DB calls are synchronous (stdlib `sqlite3`), blocking the async event loop briefly per request — acceptable at PoC scale, would need `aiosqlite` for production concurrency
- No authentication or rate limiting — open API suitable for local/demo use only
