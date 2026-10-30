"""Fetch lyrics for the catalog so songs can be found by a remembered line.

Source is **LRCLIB** (https://lrclib.net) -- an open, community-maintained
lyrics database with a free API that needs no key and no account. It also
reports whether a track is instrumental, which is how "Take Five" ends up
correctly stored with no lyrics rather than with somebody else's.

Lyrics are stored for **search indexing only**. The API strips the column from
every response and returns just the single matching line as a snippet, so the
app never displays a full copyrighted lyric.

Resumable: tracks that already have lyrics, or that were confirmed
instrumental, are skipped.

Usage:
    python -m scripts.fetch_lyrics
    python -m scripts.fetch_lyrics --limit 50
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import store  # noqa: E402

UA = {"User-Agent": "Hummingbird/0.1 (final-year project; contact: student)"}
LRCLIB = "https://lrclib.net/api/get"

# Stored for an instrumental so the track is not retried on every run.
INSTRUMENTAL = "[instrumental]"


def fetch(title: str, artist: str, timeout: int = 20) -> str | None:
    """Plain lyrics, INSTRUMENTAL, or None when nothing is found."""
    url = LRCLIB + "?" + urllib.parse.urlencode(
        {"track_name": title, "artist_name": artist}
    )
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=UA), timeout=timeout
        ) as r:
            data = json.load(r)
    except Exception:
        # A 404 here just means LRCLIB has no entry for this track.
        return None

    if data.get("instrumental"):
        return INSTRUMENTAL
    plain = (data.get("plainLyrics") or "").strip()
    return plain or None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument("--delay", type=float, default=0.25,
                    help="seconds between requests; LRCLIB is a free service")
    args = ap.parse_args()

    conn = store.connect()
    store.init_schema(conn)
    tracks = [t for t in store.all_tracks(conn) if not t.lyrics]
    if args.limit:
        tracks = tracks[: args.limit]

    if not tracks:
        print("every track already has lyrics or is marked instrumental")
        return

    print(f"fetching lyrics for {len(tracks)} tracks from LRCLIB")
    found = instrumental = missing = 0
    batch: list[store.Track] = []

    for i, t in enumerate(tracks, 1):
        result = fetch(t.title, t.artist)
        if result == INSTRUMENTAL:
            t.lyrics = INSTRUMENTAL
            instrumental += 1
            batch.append(t)
        elif result:
            t.lyrics = result
            found += 1
            batch.append(t)
        else:
            missing += 1

        time.sleep(args.delay)

        if len(batch) >= 50 or i == len(tracks):
            if batch:
                store.upsert_tracks(conn, batch)
                batch.clear()
            print(f"  {i}/{len(tracks)}  lyrics={found} "
                  f"instrumental={instrumental} missing={missing}")

    store.rebuild_fts(conn)
    coverage = (found + instrumental) / max(1, len(tracks)) * 100
    print(f"\ndone: {found} with lyrics, {instrumental} instrumental, "
          f"{missing} not in LRCLIB ({coverage:.0f}% resolved)")
    conn.close()


if __name__ == "__main__":
    main()
