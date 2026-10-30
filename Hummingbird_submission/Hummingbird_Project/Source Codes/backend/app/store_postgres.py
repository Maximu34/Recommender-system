"""Postgres (Supabase) storage backend.

Mirrors :mod:`app.store_sqlite` function for function, so callers do not care
which one is active.

Two things do not port and are reimplemented rather than translated:

* **FTS5 does not exist in Postgres.** Search uses a generated ``tsvector``
  column with a GIN index. Prefix matching (typing "bohem" and matching
  "Bohemian") is preserved by building a ``to_tsquery`` with ``:*`` suffixes,
  which is the closest equivalent of FTS5's ``"tok"*`` -- ``websearch_to_tsquery``
  is friendlier but does no prefix matching, which would break search-as-you-type.
* **``rebuild_fts`` is a no-op.** The generated column is always current, so
  there is no index to repopulate. The function is kept so the two backends
  present the same interface.

Connection comes from ``config.POSTGRES_URL`` (an environment variable). No
credential is ever read from, or written to, the repository.
"""

from __future__ import annotations

from typing import Iterable, Sequence
from urllib.parse import unquote, urlsplit

from . import config
from .models import TRACK_COLUMNS, Track

SCHEMA = """
CREATE TABLE IF NOT EXISTS tracks (
    id          BIGINT PRIMARY KEY,    -- iTunes trackId
    title       TEXT NOT NULL,
    artist      TEXT NOT NULL,
    album       TEXT,
    genre       TEXT,
    preview_url TEXT,
    artwork_url TEXT,
    duration_ms INTEGER,
    local_path  TEXT,   -- set on the machine that cached the clip; unused here
    source      TEXT,
    lyrics      TEXT    -- for search only; never served to clients
);

ALTER TABLE tracks ADD COLUMN IF NOT EXISTS lyrics TEXT;

-- Full-text search. 'simple' rather than 'english' deliberately: song titles
-- are names, not prose, and stemming "Lose" to "lose" is fine while stemming
-- artist names is not helpful.
-- Weighted title > artist > lyrics. Searching "billie" surfaces the song
-- "Billie Jean" ahead of every track by Billie Eilish, and ahead of any song
-- that merely says "billie" in a verse. Someone typing a song name wants the
-- song; without weights the ordering between a title, artist and lyric hit
-- would be arbitrary.
ALTER TABLE tracks ADD COLUMN IF NOT EXISTS search_doc tsvector
  GENERATED ALWAYS AS (
    setweight(to_tsvector('simple', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('simple', coalesce(artist, '')), 'B') ||
    setweight(to_tsvector('simple', coalesce(lyrics, '')), 'C')
  ) STORED;

CREATE INDEX IF NOT EXISTS tracks_search_idx ON tracks USING GIN (search_doc);

-- Trigram fallback, so a misspelled title still resolves.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS tracks_title_trgm
  ON tracks USING GIN (title gin_trgm_ops);
"""


def connect(path=None):
    """Open a Postgres connection. ``path`` is accepted and ignored, for parity.

    Supabase offers three endpoints and the choice matters:

    * **Session pooler** (5432) -- what this backend wants. It is IPv4-friendly
      and keeps a session per connection, so prepared statements work.
    * **Direct** (5432) -- fine too, but IPv6-only on the free tier, which many
      hosting providers cannot reach.
    * **Transaction pooler** (6543) -- built for serverless. It multiplexes
      statements across backends and **does not support prepared statements**.

    psycopg3 silently starts preparing a query once it has been seen a few
    times, so against the transaction pooler an endpoint works for the first
    few requests and then starts failing. That is a horrible bug to meet in
    production, so preparing is disabled automatically when the URL points at
    port 6543.
    """
    import psycopg
    from psycopg.rows import dict_row

    url = config.POSTGRES_URL
    if not url:
        raise RuntimeError(
            "POSTGRES_URL is not set. Copy backend/.env.example to backend/.env "
            "and put your Supabase connection string in it."
        )

    # None disables prepared statements entirely; the default is 5.
    prepare_threshold = None if ":6543" in url else 5

    # Pass the parts as keyword arguments rather than handing libpq the raw
    # URL. Supabase generates strong passwords containing characters that are
    # URL delimiters -- '@', ':', '/', '#' -- and libpq would parse such a URL
    # incorrectly and fail with a misleading "could not translate host name"
    # rather than an auth error. urlsplit splits userinfo at the *last* '@',
    # so it recovers the password correctly, and psycopg then takes the value
    # verbatim with no percent-encoding required from the user.
    parts = urlsplit(url)
    if parts.hostname:
        return psycopg.connect(
            host=parts.hostname,
            port=parts.port or 5432,
            user=unquote(parts.username or ""),
            password=unquote(parts.password or ""),
            dbname=(parts.path or "/postgres").lstrip("/") or "postgres",
            sslmode="require",          # Supabase requires TLS
            row_factory=dict_row,
            autocommit=False,
            prepare_threshold=prepare_threshold,
        )

    return psycopg.connect(
        url,
        row_factory=dict_row,
        autocommit=False,
        prepare_threshold=prepare_threshold,
    )


def init_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(SCHEMA)

        # A generated column's expression cannot be altered, and
        # "ADD COLUMN IF NOT EXISTS" silently keeps whatever definition already
        # exists. So a database created before lyrics were indexed keeps a
        # search_doc built from title and artist only, and lyric search fails
        # quietly -- queries just fall through to the trigram fallback and
        # return something plausible but wrong.
        #
        # Compare the live expression against what this module expects and
        # rebuild it when they differ.
        cur.execute(
            """SELECT pg_get_expr(d.adbin, d.adrelid) AS expr
                 FROM pg_attrdef d
                 JOIN pg_attribute a
                   ON a.attrelid = d.adrelid AND a.attnum = d.adnum
                WHERE d.adrelid = 'tracks'::regclass
                  AND a.attname = 'search_doc'"""
        )
        row = cur.fetchone()
        expression = (row or {}).get("expr") or ""
        if "lyrics" not in expression:
            cur.execute("ALTER TABLE tracks DROP COLUMN IF EXISTS search_doc")
            cur.execute(SCHEMA)
    conn.commit()


def upsert_tracks(conn, tracks: Iterable[Track]) -> int:
    rows = [t.as_row() for t in tracks]
    if not rows:
        return 0
    cols = ", ".join(TRACK_COLUMNS)
    marks = ", ".join(["%s"] * len(TRACK_COLUMNS))
    with conn.cursor() as cur:
        cur.executemany(
            f"""INSERT INTO tracks ({cols}) VALUES ({marks})
                ON CONFLICT (id) DO UPDATE SET
                  title=EXCLUDED.title, artist=EXCLUDED.artist,
                  album=EXCLUDED.album, genre=EXCLUDED.genre,
                  preview_url=EXCLUDED.preview_url,
                  artwork_url=EXCLUDED.artwork_url,
                  duration_ms=EXCLUDED.duration_ms,
                  -- COALESCE, not a plain assignment: build_catalog constructs
                  -- tracks with no lyrics, so overwriting unconditionally
                  -- would erase everything fetch_lyrics collected.
                  lyrics=COALESCE(EXCLUDED.lyrics, tracks.lyrics)""",
            rows,
        )
    conn.commit()
    return len(rows)


def set_local_path(conn, track_id: int, path: str) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE tracks SET local_path=%s WHERE id=%s", (path, track_id))
    conn.commit()


def rebuild_fts(conn) -> None:
    """No-op: ``search_doc`` is a generated column and is never stale."""
    return None


def _to_track(row: dict) -> Track:
    return Track(**{k: row[k] for k in row if k in Track.__dataclass_fields__})


def get_track(conn, track_id: int) -> Track | None:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM tracks WHERE id=%s", (track_id,))
        row = cur.fetchone()
    return _to_track(row) if row else None


def get_tracks(conn, ids: Sequence[int]) -> dict[int, Track]:
    if not ids:
        return {}
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM tracks WHERE id = ANY(%s)", (list(ids),))
        rows = cur.fetchall()
    return {r["id"]: _to_track(r) for r in rows}


def all_tracks(conn, with_audio: bool = False) -> list[Track]:
    sql = "SELECT * FROM tracks"
    if with_audio:
        sql += " WHERE local_path IS NOT NULL"
    with conn.cursor() as cur:
        cur.execute(sql)
        return [_to_track(r) for r in cur.fetchall()]


def _ts_query(q: str) -> str:
    """Build a prefix ``to_tsquery`` string, mirroring FTS5's ``"tok"*``.

    Tokens are reduced to alphanumerics first, so punctuation in a title
    (``Don't``, ``Mr. Brightside``) cannot be parsed as tsquery operator syntax.
    """
    tokens = [t for t in "".join(c if c.isalnum() else " " for c in q).split() if t]
    return " & ".join(f"{t}:*" for t in tokens)


def search_tracks(conn, q: str, limit: int = 20) -> list[Track]:
    """Metadata title/artist search. Deliberately *not* an embedding search."""
    tsq = _ts_query(q)
    if not tsq:
        return []

    with conn.cursor() as cur:
        cur.execute(
            """SELECT *, ts_rank(search_doc, query) AS rank
                 FROM tracks, to_tsquery('simple', %s) AS query
                WHERE search_doc @@ query
                ORDER BY rank DESC, id
                LIMIT %s""",
            (tsq, limit),
        )
        rows = cur.fetchall()

        # Nothing matched: fall back to fuzzy title matching so a typo still
        # finds the song. Trigram search cannot do prefixes, which is why it is
        # a fallback rather than the primary path.
        if not rows:
            cur.execute(
                """SELECT *, similarity(title, %s) AS rank
                     FROM tracks
                    WHERE similarity(title, %s) > 0.25
                    ORDER BY rank DESC, id
                    LIMIT %s""",
                (q, q, limit),
            )
            rows = cur.fetchall()

    return [_to_track(r) for r in rows]


def count_tracks(conn) -> tuple[int, int]:
    """(total tracks, tracks with a cached clip)."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT COUNT(*) AS total,
                      COUNT(local_path) AS with_audio
                 FROM tracks"""
        )
        row = cur.fetchone()
    return int(row["total"]), int(row["with_audio"])


def ids_by_artist(conn, artist: str) -> set[int]:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM tracks WHERE artist=%s", (artist,))
        return {r["id"] for r in cur.fetchall()}
