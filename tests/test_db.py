"""Tests for app.db — persistence layer."""

from app.db import (
    evict_old_batches,
    get_all_pictures,
    get_latest_batch,
    init_db,
    save_pictures,
)

FAKE_IMAGE = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"


def _db(tmp_path) -> str:
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


def test_save_and_retrieve_batch(tmp_path):
    """Pictures inserted in one call share a batch_id and are retrievable together."""
    db = _db(tmp_path)
    save_pictures(db, "cat", [FAKE_IMAGE, FAKE_IMAGE, FAKE_IMAGE], "batch-1")

    result = get_latest_batch(db, "cat")
    assert len(result) == 3


def test_latest_batch_returns_most_recent(tmp_path):
    """get_latest_batch returns only the most recent batch, not earlier ones."""
    db = _db(tmp_path)
    save_pictures(db, "dog", [FAKE_IMAGE], "batch-old")
    # Insert second batch — same created_at (datetime precision), but higher rowid
    save_pictures(db, "dog", [FAKE_IMAGE, FAKE_IMAGE], "batch-new")

    result = get_latest_batch(db, "dog")
    # The latest batch should have 2 images
    assert len(result) == 2


def test_get_all_pictures_orders_newest_first(tmp_path):
    """get_all_pictures returns all stored images, newest batch first."""
    db = _db(tmp_path)
    save_pictures(db, "bear", [b"first"], "batch-1")
    save_pictures(db, "bear", [b"second"], "batch-2")

    result = get_all_pictures(db, "bear")
    assert result[0] == b"second"
    assert result[1] == b"first"


def test_eviction_keeps_only_n_batches(tmp_path):
    """After 6 batches, only 5 are retained."""
    db = _db(tmp_path)
    for i in range(6):
        save_pictures(db, "cat", [FAKE_IMAGE], f"batch-{i}")
    evict_old_batches(db, "cat", keep=5)

    result = get_all_pictures(db, "cat")
    assert len(result) == 5


def test_latest_batch_empty_when_nothing_stored(tmp_path):
    """get_latest_batch returns [] for an animal with no data."""
    db = _db(tmp_path)
    assert get_latest_batch(db, "cat") == []


def test_get_all_empty_when_nothing_stored(tmp_path):
    """get_all_pictures returns [] for an animal with no data."""
    db = _db(tmp_path)
    assert get_all_pictures(db, "dog") == []
