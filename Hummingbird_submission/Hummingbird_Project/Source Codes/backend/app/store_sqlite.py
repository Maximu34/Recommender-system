"""SQLite storage backend.

The default, and the one the evaluation scripts use: it needs no network, no
credentials and no running service, so the measured results in the README stay
reproducible on any machine that clones the repo.

Full-text search uses **FTS5**, which is the one genuinely non-portable part of
this module -- Postgres has no equivalent, so :mod:`app.store_postgres`
reimplements search with ``tsvector`` rather than translating this.
"""

from __future__ import annotations

import sqlite3
from typing import Iterable, Sequence

from . import config
from .models import TRACK_COLUMNS, Track

SCHEMA = """
CREATE TABLE IF NOT EXISTS tracks (
    id          INTEGER PRIMARY KEY,   -- iTunes trackId
    title       TEXT NOT NULL,
    artist      TEXT NOT NULL,
    album       TEXT,
    genre       TEXT,
    preview_url TEXT,
    artwork_url TEXT,
    duration_ms INTEGER,
    local_path  TEXT,                  -- set once the preview is cached
    source      TEXT,                  -- 'listenbrainz' | 'curated'
    lyrics      TEXT                   -- for search only; never served to clients
);

-- Lyrics are indexed alongside title and artist so a half-remembered line
-- finds the song. Ranking still favours the title (see search_tracks).
CREATE VIRTUAL TABLE IF NOT EXISTS tracks_fts
USING fts5(title, artist, lyrics, content='tracks', content_rowid='id');
"""


def connect(path=None) -> sqlite3.Connection:
    config.ensure_dirs()
    conn = sqlite3.connect(path or config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)

    # SQLite has no ADD COLUMN IF NOT EXISTS, and a database created before
    # lyrics existed needs the column added rather than the table recreated.
    cols = {r[1] for r in conn.execute("PRAGMA table_info(tracks)")}
    if "lyrics" not in cols:
        conn.execute("ALTER TABLE tracks ADD COLUMN lyrics TEXT")
        # The FTS table's shape is fixed at creation, so it must be rebuilt to
        # gain the new column.
        conn.execute("DROP TABLE IF EXISTS tracks_fts")
        conn.executescript(SCHEMA)
        conn.execute("INSERT INTO tracks_fts(tracks_fts) VALUES('rebuild')")
    conn.commit()


def upsert_tracks(conn: sqlite3.Connection, tracks: Iterable[Track]) -> int:
    rows = [t.as_row() for t in tracks]
    cols = ", ".join(TRACK_COLUMNS)
    marks = ", ".join("?" * len(TRACK_COLUMNS))
    conn.executemany(
        f"""INSERT INTO tracks ({cols}) VALUES ({marks})
            ON CONFLICT(id) DO UPDATE SET
              title=excluded.title, artist=excluded.artist,
              album=excluded.album, genre=excluded.genre,
              preview_url=excluded.preview_url,
              artwork_url=excluded.artwork_url,
              duration_ms=excluded.duration_ms,
              -- COALESCE, not a plain assignment: build_catalog constructs
              -- tracks with no lyrics, so overwriting unconditionally would
              -- erase everything fetch_lyrics collected on the next catalog
              -- rebuild.
              lyrics=COALESCE(excluded.lyrics, tracks.lyrics)""",
        rows,
    )
    conn.commit()
    return len(rows)


def set_local_path(conn: sqlite3.Connection, track_id: int, path: str) -> None:
    conn.execute("UPDATE tracks SET local_path=? WHERE id=?", (path, track_id))
    conn.commit()


def rebuild_fts(conn: sqlite3.Connection) -> None:
    """Repopulate the FTS index from ``tracks``.

    Cheaper and less error-prone than maintaining sync triggers, since the
    catalog is only built in bulk.
    """
    conn.execute("INSERT INTO tracks_fts(tracks_fts) VALUES('rebuild')")
    conn.commit()


def _to_track(row: sqlite3.Row) -> Track:
    return Track(**{k: row[k] for k in row.keys()})


def get_track(conn: sqlite3.Connection, track_id: int) -> Track | None:
    row = conn.execute("SELECT * FROM tracks WHERE id=?", (track_id,)).fetchone()
    return _to_track(row) if row else None


def get_tracks(conn: sqlite3.Connection, ids: Sequence[int]) -> dict[int, Track]:
    if not ids:
        return {}
    marks = ",".join("?" * len(ids))
    rows = conn.execute(f"SELECT * FROM tracks WHERE id IN ({marks})", tuple(ids))
    return {r["id"]: _to_track(r) for r in rows}


def all_tracks(conn: sqlite3.Connection, with_audio: bool = False) -> list[Track]:
    sql = "SELECT * FROM tracks"
    if with_audio:
        sql += " WHERE local_path IS NOT NULL"
    return [_to_track(r) for r in conn.execute(sql)]


def _fts_query(q: str) -> str:
    """Turn user input into a safe FTS5 prefix query.

    Every token is quoted, so punctuation in a song title (``Don't``,
    ``Mr. Brightside``) can't be parsed as FTS operator syntax.
    """
    tokens = [t for t in "".join(c if c.isalnum() else " " for c in q).split() if t]
    return " ".join(f'"{t}"*' for t in tokens)


def search_tracks(conn: sqlite3.Connection, q: str, limit: int = 20) -> list[Track]:
    """Metadata title/artist search. Deliberately *not* an embedding search."""
    match = _fts_query(q)
    if not match:
        return []
    # bm25 column weights, in the FTS table's column order: title, artist,
    # lyrics. Mirrors the 'A'/'B'/'C' weighting on the Postgres side, so
    # "billie" returns the song "Billie Jean" rather than a Billie Eilish track
    # or something that merely says "billie" in a verse. bm25 returns a
    # negative score where lower is better, hence plain ascending order.
    rows = conn.execute(
        """SELECT t.* FROM tracks_fts f
             JOIN tracks t ON t.id = f.rowid
            WHERE tracks_fts MATCH ?
            ORDER BY bm25(tracks_fts, 10.0, 4.0, 1.0), t.id
            LIMIT ?""",
        (match, limit),
    ).fetchall()
    return [_to_track(r) for r in rows]


def count_tracks(conn: sqlite3.Connection) -> tuple[int, int]:
    """(total tracks, tracks with a cached clip)."""
    total = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
    with_audio = conn.execute(
        "SELECT COUNT(*) FROM tracks WHERE local_path IS NOT NULL").fetchone()[0]
    return int(total), int(with_audio)


def ids_by_artist(conn: sqlite3.Connection, artist: str) -> set[int]:
    rows = conn.execute("SELECT id FROM tracks WHERE artist=?", (artist,))
    return {r["id"] for r in rows}
