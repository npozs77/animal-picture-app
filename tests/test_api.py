"""Tests for app.main — FastAPI endpoint integration tests."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db import init_db
from app.main import app

FAKE_IMAGE = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Create a test client with a temporary database."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("app.main.DB_PATH", db_path)
    monkeypatch.setattr("app.db.DB_PATH", db_path)
    init_db(db_path)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestFetchEndpoint:
    """Tests for POST /fetch."""

    def test_fetch_valid_request(self, client):
        """Happy path: fetch and save returns correct count."""
        with patch("app.main.fetch_pictures", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [FAKE_IMAGE, FAKE_IMAGE, FAKE_IMAGE]
            response = client.post("/fetch", json={"animal": "cat", "count": 3})

        assert response.status_code == 200
        assert response.json() == {"saved": 3}

    def test_fetch_invalid_animal(self, client):
        """Invalid animal type returns 422."""
        response = client.post("/fetch", json={"animal": "fish", "count": 1})
        assert response.status_code == 422

    def test_fetch_count_too_high(self, client):
        """Count above 5 returns 422."""
        response = client.post("/fetch", json={"animal": "dog", "count": 10})
        assert response.status_code == 422

    def test_fetch_count_zero(self, client):
        """Count of 0 returns 422."""
        response = client.post("/fetch", json={"animal": "dog", "count": 0})
        assert response.status_code == 422

    def test_fetch_upstream_failure(self, client):
        """All upstream fetches fail returns 502."""
        with patch("app.main.fetch_pictures", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            response = client.post("/fetch", json={"animal": "bear", "count": 3})

        assert response.status_code == 502

    def test_fetch_partial_success(self, client):
        """Partial upstream success saves what worked."""
        with patch("app.main.fetch_pictures", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [FAKE_IMAGE, FAKE_IMAGE]
            response = client.post("/fetch", json={"animal": "cat", "count": 3})

        assert response.status_code == 200
        assert response.json() == {"saved": 2}


class TestLatestEndpoint:
    """Tests for GET /latest/{animal}."""

    def test_latest_not_found(self, client):
        """No stored pictures returns 404."""
        response = client.get("/latest/cat")
        assert response.status_code == 404

    def test_latest_returns_batch(self, client):
        """Returns all pictures from the most recent fetch call."""
        with patch("app.main.fetch_pictures", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [FAKE_IMAGE, FAKE_IMAGE]
            client.post("/fetch", json={"animal": "dog", "count": 2})

        response = client.get("/latest/dog")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["pictures"]) == 2

    def test_latest_invalid_animal(self, client):
        """Invalid animal returns 422."""
        response = client.get("/latest/fish")
        assert response.status_code == 422


class TestGalleryEndpoint:
    """Tests for GET /pictures/{animal}."""

    def test_pictures_not_found(self, client):
        """No stored pictures returns 404."""
        response = client.get("/pictures/bear")
        assert response.status_code == 404

    def test_pictures_returns_all_across_batches(self, client):
        """Multiple fetches are combined in the gallery."""
        with patch("app.main.fetch_pictures", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [FAKE_IMAGE, FAKE_IMAGE]
            client.post("/fetch", json={"animal": "cat", "count": 2})
            mock_fetch.return_value = [FAKE_IMAGE]
            client.post("/fetch", json={"animal": "cat", "count": 1})

        response = client.get("/pictures/cat")
        assert response.status_code == 200
        assert response.json()["count"] == 3


class TestEviction:
    """Tests for batch retention via the API."""

    def test_eviction_after_six_calls(self, client):
        """Only 5 most recent batches retained after 6 fetch calls."""
        with patch("app.main.fetch_pictures", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [FAKE_IMAGE]
            for _ in range(6):
                client.post("/fetch", json={"animal": "bear", "count": 1})

        response = client.get("/pictures/bear")
        assert response.status_code == 200
        assert response.json()["count"] == 5
