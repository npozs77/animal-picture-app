"""SQLite database helpers for storing and retrieving animal pictures."""

import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "animals.db")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Return a connection to the SQLite database, creating it if needed."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Create the pictures table and indexes if they don't exist."""
    conn = get_connection(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pictures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                animal TEXT NOT NULL,
                image BLOB NOT NULL,
                batch_id TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_animal_batch
            ON pictures(animal, batch_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_animal_created
            ON pictures(animal, created_at DESC)
        """)
        conn.commit()
    finally:
        conn.close()


def save_pictures(db_path: str, animal: str, images: list[bytes], batch_id: str) -> None:
    """Insert a batch of pictures into the database."""
    conn = get_connection(db_path)
    try:
        conn.executemany(
            "INSERT INTO pictures (animal, image, batch_id) VALUES (?, ?, ?)",
            [(animal, img, batch_id) for img in images],
        )
        conn.commit()
    finally:
        conn.close()


def get_latest_batch(db_path: str, animal: str) -> list[bytes]:
    """Return all images from the most recent fetch call for the given animal."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """SELECT batch_id FROM pictures
               WHERE animal = ?
               ORDER BY created_at DESC, id DESC
               LIMIT 1""",
            (animal,),
        ).fetchone()
        if not row:
            return []
        batch_id = row[0]
        rows = conn.execute(
            "SELECT image FROM pictures WHERE animal = ? AND batch_id = ? ORDER BY id",
            (animal, batch_id),
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def get_all_pictures(db_path: str, animal: str) -> list[bytes]:
    """Return all stored images for the given animal, newest-first."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT image FROM pictures WHERE animal = ? ORDER BY created_at DESC, id DESC",
            (animal,),
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def evict_old_batches(db_path: str, animal: str, keep: int = 5) -> None:
    """Delete pictures from fetch calls older than the most recent `keep` calls."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """SELECT DISTINCT batch_id FROM pictures
               WHERE animal = ?
               ORDER BY created_at DESC""",
            (animal,),
        ).fetchall()
        batch_ids = [r[0] for r in rows]
        if len(batch_ids) > keep:
            old_ids = batch_ids[keep:]
            placeholders = ",".join("?" * len(old_ids))
            conn.execute(
                f"DELETE FROM pictures WHERE animal = ? AND batch_id IN ({placeholders})",
                [animal, *old_ids],
            )
            conn.commit()
    finally:
        conn.close()
