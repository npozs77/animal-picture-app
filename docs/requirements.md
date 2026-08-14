# Requirements

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-API.1 | POST `/fetch` accepts `animal` (cat/dog/bear) and `count` (1–5), fetches that many random pictures from the upstream API, retries each failed fetch up to 2 times, and stores successful results in the DB. |
| FR-API.2 | POST `/fetch` response returns `{"saved": N}`. If all attempts fail, return 502. |
| FR-API.3 | GET `/latest/{animal}` returns all images from the most recent fetch call for that animal as JSON `{"pictures": [...], "count": N}`. Returns 404 if none stored. |
| FR-API.4 | GET `/pictures/{animal}` returns all stored pictures for that animal (up to 25) as a JSON array of base64-encoded images, ordered newest-first. |
| FR-DB.1 | Pictures stored as BLOBs in SQLite. Each row tracks: animal type, image bytes, batch ID, and timestamp. |
| FR-DB.2 | Retention: keep pictures from the last 5 fetch calls per animal. Evict oldest call on the 6th. |
| FR-UI.1 | Static HTML page with: animal dropdown, count input (max 5), "Fetch & Save", "Show Latest", "Show All" buttons. |
| FR-UI.2 | "Show All" displays a gallery of all stored pictures for the selected animal. |

## Non-Functional Requirements

| ID | Requirement | Rationale |
|----|-------------|-----------|
| NFR-1 | SQLite embedded, DB created at runtime, file not committed | Portable, no external service |
| NFR-2 | Runs locally via `uv sync` + `uv run` | Zero-friction local dev |
| NFR-3 | Runs via `docker build && docker run`, no other setup | Self-contained container |
| NFR-4 | Plain functions, no ORM, code readable by non-developer | Explicit constraint |
| NFR-5 | Automated tests (pytest), mocked upstream calls | Quality baseline |
| NFR-6 | Linting (ruff), CI (GitHub Actions: lint + test + docker build) | Professional hygiene |

## Constraints

- Python 3.13+, FastAPI, sqlite3 stdlib, httpx2, pytest
- Package management: uv (pyproject.toml + uv.lock)
- Container: single-stage Dockerfile on `astral-sh/uv` image
- No auth, pagination, multiple DB backends, message queues, docker-compose

## User Stories

### Personas

- **App User** — interacts with the UI/API to collect and browse animal pictures
- **Evaluator** — clones the repo, builds/runs the app, assesses it meets the assignment
- **Developer** — builds and submits the project, demonstrates professional hygiene

### Stories

| ID | As a... | I want to... | So that... | Acceptance Criteria |
|----|---------|-------------|-----------|-------------------|
| US-1 | App User | fetch N random pictures of a chosen animal | I can build a collection | Select animal, specify count 1–5, see confirmation of how many saved, retries on failure, clear error if all fail |
| US-2 | App User | see all pictures from my last fetch | I can verify what was saved | Click "Show Latest" → see all images from last batch, or "nothing stored" message |
| US-3 | App User | browse all stored pictures for an animal | I can see my collection | Click "Show All" → gallery of up to 25 images, newest-first |
| US-4 | App User | have old pictures cleaned up automatically | the app stays bounded | Only last 5 fetch calls per animal retained, no manual action |
| US-5 | Evaluator | run the app with minimal commands | I can verify it works quickly | `uv sync && uv run uvicorn app.main:app` or `docker build && docker run`, UI at localhost:8000 |
| US-6 | Developer | demonstrate professional practices | evaluators see engineering discipline | Makefile, pytest, ruff, uv, CI, SDD docs in repo, README references methodology |

## External APIs

| Animal | URL | Notes |
|--------|-----|-------|
| Cat | `https://cataas.com/cat?width={w}&height={h}` | Random images, supports resize |
| Dog | `https://place.dog/{w}/{h}` | Random images per call |
| Bear | `https://placebear.com/{w}/{h}` | Static per dimension — use jitter (395–405 × 295–305) for variety |
