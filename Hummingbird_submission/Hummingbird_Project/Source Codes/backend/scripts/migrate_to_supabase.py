"""Copy the local SQLite catalog into Supabase Postgres.

Idempotent: every row is an upsert keyed on the iTunes track id, so running it
twice changes nothing. Safe to re-run after adding tracks locally.

The local SQLite file stays the source of truth for indexing and evaluation --
this only mirrors metadata so a deployed backend can serve it. Embeddings are
deliberately *not* migrated: they load from the `.npy` files into memory, which
is faster than any database round-trip at this catalog size.

Setup, once:
  1. Create a free project at https://supabase.com
  2. Settings -> Database -> Connection string -> "Transaction pooler" (port 6543)
  3. Copy backend/.env.example to backend/.env and paste it as POSTGRES_URL

Usage:
    python -m scripts.migrate_to_supabase --dry-run   # check the connection
    python -m scripts.migrate_to_supabase
    python -m scripts.migrate_to_supabase --verify    # compare row counts
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config, store, store_postgres, store_sqlite  # noqa: E402


def _redact(url: str) -> str:
    """Show enough of the URL to confirm the target, never the password."""
    if not url:
        return "(unset)"
    try:
        head, _, tail = url.rpartition("@")
        scheme = head.split("://", 1)[0] if "://" in head else "postgresql"
        return f"{scheme}://***:***@{tail}"
    except Exception:
        return "(unparseable)"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="connect and report counts, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="compare row counts on both sides and exit")
    ap.add_argument("--batch", type=int, default=200)
    args = ap.parse_args()

    if not config.POSTGRES_URL:
        print("POSTGRES_URL is not set.")
        print("Copy backend/.env.example to backend/.env and add your Supabase")
        print("connection string, then run this again.")
        sys.exit(1)

    print(f"target: {_redact(config.POSTGRES_URL)}")

    sq = store_sqlite.connect()
    store_sqlite.init_schema(sq)
    tracks = store_sqlite.all_tracks(sq)
    sq.close()
    print(f"sqlite: {len(tracks)} tracks")

    pg = store_postgres.connect()
    try:
        store_postgres.init_schema(pg)
        print("postgres: schema ready (tracks + tsvector + pg_trgm)")

        with pg.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM tracks")
            before = cur.fetchone()["n"]
        print(f"postgres: {before} tracks before")

        if args.verify:
            print(f"\n{'MATCH' if before == len(tracks) else 'DIFFERENT'}: "
                  f"sqlite={len(tracks)} postgres={before}")
            return

        if args.dry_run:
            print("\ndry run -- nothing written")
            return

        written = 0
        for i in range(0, len(tracks), args.batch):
            chunk = tracks[i:i + args.batch]
            written += store_postgres.upsert_tracks(pg, chunk)
            print(f"  upserted {written}/{len(tracks)}")

        with pg.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM tracks")
            after = cur.fetchone()["n"]

        print(f"\npostgres: {after} tracks after ({after - before} new)")
        print("re-run this script; the count must not change (idempotency check)")
    finally:
        pg.close()


if __name__ == "__main__":
    main()
