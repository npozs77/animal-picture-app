"""HTTP client for fetching random animal pictures from external APIs."""

import random

import httpx2 as httpx

TIMEOUT = 10.0  # seconds per request
MAX_RETRIES = 2


def _get_url(animal: str) -> str:
    """Generate the fetch URL for a given animal, with slight dimension jitter for variety."""
    w = random.randint(395, 405)
    h = random.randint(295, 305)
    urls = {
        "cat": f"https://cataas.com/cat?width={w}&height={h}",
        "dog": f"https://place.dog/{w}/{h}",
        "bear": f"https://placebear.com/{w}/{h}",
    }
    return urls[animal]


async def fetch_pictures(animal: str, count: int) -> list[bytes]:
    """Fetch `count` random pictures for the given animal type.

    Retries each failed fetch up to MAX_RETRIES times.
    Returns a list of image bytes for successful fetches.
    """
    results: list[bytes] = []

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        for _ in range(count):
            url = _get_url(animal)
            image = await _fetch_with_retry(client, url)
            if image:
                results.append(image)

    return results


async def _fetch_with_retry(client: httpx.AsyncClient, url: str) -> bytes | None:
    """Attempt to fetch an image, retrying up to MAX_RETRIES times on failure."""
    for attempt in range(1 + MAX_RETRIES):
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
        except httpx.HTTPError:
            if attempt == MAX_RETRIES:
                return None
    return None
