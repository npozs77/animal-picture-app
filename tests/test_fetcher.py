"""Tests for app.fetcher — external API client with retry logic."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx2 as httpx
import pytest

from app.fetcher import _fetch_with_retry, _get_url, fetch_pictures

FAKE_IMAGE = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"


class TestGetUrl:
    """Tests for URL generation with dimension jitter."""

    def test_returns_valid_url_for_each_animal(self):
        """Each animal type produces a URL containing the animal's API domain."""
        assert "cataas.com" in _get_url("cat")
        assert "place.dog" in _get_url("dog")
        assert "placebear.com" in _get_url("bear")

    def test_dimensions_vary_across_calls(self):
        """Multiple calls produce different URLs (dimension jitter provides variety)."""
        urls = {_get_url("bear") for _ in range(20)}
        # With 11×11 possible dimension combos, 20 calls should produce multiple distinct URLs
        assert len(urls) > 1


class TestFetchWithRetry:
    """Tests for the retry mechanism."""

    @pytest.mark.asyncio
    async def test_succeeds_on_first_try(self):
        """Returns image bytes immediately on success."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = FAKE_IMAGE
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        result = await _fetch_with_retry(mock_client, "http://example.com/img")
        assert result == FAKE_IMAGE
        assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_failure_then_succeeds(self):
        """Retries after a failure and returns the successful result."""
        mock_client = AsyncMock()

        fail_response = MagicMock()
        fail_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )

        success_response = MagicMock()
        success_response.content = FAKE_IMAGE
        success_response.raise_for_status = MagicMock()

        mock_client.get.side_effect = [fail_response, success_response]

        result = await _fetch_with_retry(mock_client, "http://example.com/img")
        assert result == FAKE_IMAGE
        assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_returns_none_after_exhausting_retries(self):
        """Returns None when all retry attempts fail."""
        mock_client = AsyncMock()

        fail_response = MagicMock()
        fail_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )
        mock_client.get.return_value = fail_response

        result = await _fetch_with_retry(mock_client, "http://example.com/img")
        assert result is None
        assert mock_client.get.call_count == 3  # 1 try + 2 retries


class TestFetchPictures:
    """Tests for the top-level fetch orchestration."""

    @pytest.mark.asyncio
    async def test_returns_all_on_success(self):
        """Returns a list of image bytes when all fetches succeed."""
        with patch("app.fetcher._fetch_with_retry", new_callable=AsyncMock) as mock:
            mock.return_value = FAKE_IMAGE
            result = await fetch_pictures("cat", 3)

        assert len(result) == 3
        assert all(img == FAKE_IMAGE for img in result)

    @pytest.mark.asyncio
    async def test_skips_failed_fetches(self):
        """Failed individual fetches are skipped, successful ones returned."""
        with patch("app.fetcher._fetch_with_retry", new_callable=AsyncMock) as mock:
            mock.side_effect = [FAKE_IMAGE, None, FAKE_IMAGE]
            result = await fetch_pictures("dog", 3)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_when_all_fail(self):
        """Returns empty list when every fetch fails."""
        with patch("app.fetcher._fetch_with_retry", new_callable=AsyncMock) as mock:
            mock.return_value = None
            result = await fetch_pictures("bear", 3)

        assert result == []

    def test_bear_variety_across_batches(self):
        """Defensive: URLs generated for bear vary across separate calls (regression coverage)."""
        # Calling _get_url multiple times should produce different URLs due to random jitter
        # This documents the invariant: we never get the same fixed set from batch to batch
        urls_batch_1 = [_get_url("bear") for _ in range(5)]
        urls_batch_2 = [_get_url("bear") for _ in range(5)]
        # Not guaranteed all different (randomness), but very unlikely all 10 are identical
        all_urls = set(urls_batch_1 + urls_batch_2)
        assert len(all_urls) > 1
