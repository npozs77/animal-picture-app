# Test Strategy

## Approach

- **Mock at the external boundary only** — no real HTTP calls in the test suite
- **Layer isolation** — DB, fetcher, and API each tested independently
- **Temporary DB per test** — pytest `tmp_path` ensures zero test pollution
- **Coverage target (PoC):** happy path + key error/edge cases per layer

## Test Structure

| Layer | File | Tests | What's covered |
|-------|------|-------|---------------|
| Persistence | `tests/test_db.py` | 6 | Batch save/retrieve, latest-batch semantics, ordering, eviction, empty-state |
| HTTP Client | `tests/test_fetcher.py` | 7 | URL generation, retry-then-succeed, retry-exhausted, partial/total failure, cross-batch variety |
| API Endpoints | `tests/test_api.py` | 12 | All endpoints happy path, validation errors (422), upstream failure (502), eviction via API |

## Requirement → Test Traceability

| Requirement | Verified by |
|-------------|-------------|
| FR-API.1 (fetch, validate, save batch, retry) | `test_fetch_valid_request`, `test_fetch_invalid_animal`, `test_fetch_count_too_high`, `test_fetch_count_zero`, `test_retries_on_failure_then_succeeds`, `test_returns_none_after_exhausting_retries` |
| FR-API.2 (report saved count, 502 on total failure) | `test_fetch_valid_request`, `test_fetch_upstream_failure`, `test_fetch_partial_success` |
| FR-API.3 (latest = full batch, 404 if empty) | `test_latest_returns_batch`, `test_latest_not_found` |
| FR-API.4 (gallery across batches) | `test_pictures_returns_all_across_batches`, `test_pictures_not_found` |
| FR-DB.2 (5-batch retention, evict oldest) | `test_eviction_keeps_only_n_batches`, `test_eviction_after_six_calls` |
| Dimension jitter (variety) | `test_dimensions_vary_across_calls`, `test_bear_variety_across_batches` |

## Not in the automated suite

- **Live API calls** — third-party services are slow and flaky; verified manually
- **Docker offline test** — verified container starts without network access
- **End-to-end UI smoke** — static HTML + fetch/gallery verified via browser
