"""Build the track catalog.

    ListenBrainz popular recordings  +  a hand-curated list
                      |
                      v
        iTunes Search API (keyless)  ->  preview URL + genre label
                      |
                      v
                  SQLite (tracks + FTS5)

The curated list is not a shortcut: the humming evaluation needs songs the
raters actually know, so letting them name those songs is what makes that
evaluation valid. ListenBrainz popularity reflects its own userbase, so the
curated list is also what corrects that sampling bias.

Usage:
    python -m scripts.build_catalog --target 2000
    python -m scripts.build_catalog --target 50 --skip-listenbrainz   # quick test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config, store  # noqa: E402

UA = {"User-Agent": "Hummingbird/0.1 (final-year project; contact: student)"}

LISTENBRAINZ = "https://api.listenbrainz.org/1/stats/sitewide/recordings"
ITUNES = "https://itunes.apple.com/search"

# Each range surfaces a different slice of popularity; the union is wider and
# less trend-skewed than any single one.
LB_RANGES = ["week", "month", "quarter", "half_yearly", "year", "all_time"]

CACHE_PATH = config.DATA / "itunes_cache.json"


def _get_json(url: str, timeout: int = 25) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def norm_key(title: str, artist: str) -> str:
    """Normalised (title, artist) key for de-duplication."""
    def clean(s: str) -> str:
        s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
        s = s.lower()
        # Drop bracketed qualifiers: "(Remastered 2011)", "[Live]", "- Radio Edit"
        s = re.sub(r"\(.*?\)|\[.*?\]", " ", s)
        s = re.sub(r"\s-\s.*$", " ", s)
        s = re.sub(r"\bfeat\b.*$|\bft\b.*$", " ", s)
        return re.sub(r"[^a-z0-9]+", " ", s).strip()
    return f"{clean(title)}|{clean(artist)}"


def _words(s: str) -> set[str]:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return {w for w in re.sub(r"[^a-z0-9]+", " ", s.lower()).split() if w}


def _artist_words(artist: str) -> set[str]:
    """Artist name reduced to comparable tokens.

    Only the *artist* is trimmed, of the qualifiers iTunes appends -- "(feat.
    X)", "& Y". The query is never trimmed: an earlier version stripped
    everything after the word "with" and thereby deleted the whole of
    "With or Without You U2", rejecting a correct row.
    """
    artist = re.sub(r"\(.*?\)|\[.*?\]", " ", artist or "")
    # Word boundaries matter: without them "ft" matches inside "Daft
    # Punk" and "Swift" and truncates them to "Da" and "Swi", rejecting
    # every correct row for those artists.
    artist = re.split(r"\bfeat\b|\bft\b|\bwith\b|&|,", artist, flags=re.I)[0]
    return _words(artist)


def artist_matches(query: str, artist: str) -> bool:
    """Does ``artist`` plausibly answer ``query``?

    One shared token is enough. Short and punctuated names -- U2, AC/DC,
    R.E.M., a-ha -- survive normalisation badly, so requiring more would
    reject correct rows. Verified against the 74 hand-curated songs, which are
    known-correct: this rule rejects none of them.
    """
    aw = _artist_words(artist)
    return bool(aw and (aw & _words(query)))


# --- sources -------------------------------------------------------------

def fetch_listenbrainz(target: int, verbose: bool = True) -> list[tuple[str, str]]:
    """Popular recordings across several time ranges (keyless API).

    Paging dies somewhere past offset ~1000 per range, so we walk each range
    until it stops returning rows and move on to the next.
    """
    seen: dict[str, tuple[str, str]] = {}
    for rng in LB_RANGES:
        offset = 0
        while len(seen) < target:
            url = f"{LISTENBRAINZ}?count=100&offset={offset}&range={rng}"
            try:
                payload = _get_json(url).get("payload", {})
            except Exception as exc:
                if verbose:
                    print(f"  [{rng}] stopped at offset {offset}: {exc}")
                break
            recs = payload.get("recordings", [])
            if not recs:
                break
            for rec in recs:
                title, artist = rec.get("track_name"), rec.get("artist_name")
                if title and artist:
                    seen.setdefault(norm_key(title, artist), (title, artist))
            offset += len(recs)
            time.sleep(0.2)
        if verbose:
            print(f"  [{rng:12s}] running unique total: {len(seen)}")
        if len(seen) >= target:
            break
    return list(seen.values())


def read_curated() -> list[tuple[str, str]]:
    """Read ``data/curated_songs.txt`` -- one ``Title - Artist`` per line."""
    if not config.CURATED_LIST.exists():
        return []
    out = []
    for line in config.CURATED_LIST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        title, sep, artist = line.partition(" - ")
        if sep:
            out.append((title.strip(), artist.strip()))
        else:
            out.append((line, ""))
    return out


# --- iTunes resolution ---------------------------------------------------

def load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")


def resolve_itunes(title: str, artist: str, cache: dict, delay: float) -> dict | None:
    """Resolve one (title, artist) to an iTunes track with a preview URL.

    Successful lookups are cached on disk so re-runs cost nothing. Rate-limit
    failures are deliberately *not* cached: 403/429 from this API means "slow
    down", not "no such song", and caching those would turn a transient
    throttle into a permanent hole in the catalog. Re-run the script to pick
    them up.
    """
    term = f"{title} {artist}".strip()
    if term in cache:
        return cache[term]

    url = ITUNES + "?" + urllib.parse.urlencode(
        {"term": term, "media": "music", "entity": "song", "limit": 5}
    )

    # Apple throttles hard and needs seconds, not milliseconds, to cool off.
    backoff = max(5.0, delay * 10)
    data = None
    for attempt in range(4):
        try:
            data = _get_json(url)
            break
        except Exception as exc:
            if attempt == 3:
                print(f"    rate limited on {term!r} ({exc}) -- re-run to retry")
                return None
            time.sleep(backoff)
            backoff *= 2

    if data is None:
        return None

    # Take the first candidate that has a preview *and* is actually by the
    # artist we asked for. Accepting the top hit blindly returned a lullaby
    # cover of Green Day for "Boulevard of Broken Dreams", and Migos for
    # "Nuts RM" -- measured at 9.4% of lookups. A track that misrepresents its
    # audio, its genre and its title is worse than a missing one, so an
    # unmatchable query resolves to nothing.
    results = data.get("results") or []
    hit = next(
        (r for r in results
         if r.get("previewUrl") and artist_matches(term, r.get("artistName", ""))),
        None,
    )
    cache[term] = hit          # a real answer, including a genuine "not found"
    time.sleep(delay)
    return hit


def to_track(hit: dict, source: str) -> store.Track:
    return store.Track(
        id=int(hit["trackId"]),
        title=hit.get("trackName", ""),
        artist=hit.get("artistName", ""),
        album=hit.get("collectionName"),
        genre=hit.get("primaryGenreName"),
        preview_url=hit.get("previewUrl"),
        artwork_url=hit.get("artworkUrl100"),
        duration_ms=hit.get("trackTimeMillis"),
        source=source,
    )


def prune_unbacked(conn, cache: dict) -> int:
    """Delete catalog rows no longer backed by a cached lookup.

    --reresolve purges the cache entries whose artist failed the check, so a
    track id still in the database but absent from every cached result came
    from one of those bad lookups. upsert_tracks only inserts and updates, so
    without this the corrected row is added *alongside* the wrong one -- which
    is how the catalog ended up holding both Robyn's "Into The Sun" and the
    BTS song it should have resolved to.
    """
    good = {int(h["trackId"]) for h in cache.values() if h and h.get("trackId")}
    if not good:
        return 0
    doomed = {t.id for t in store.all_tracks(conn)} - good
    for track_id in doomed:
        conn.execute("DELETE FROM tracks WHERE id=?", (track_id,))
    conn.commit()
    return len(doomed)


# Artists that publish generated ambience rather than music. ListenBrainz
# ranks them highly because people leave them running for hours, but they are
# not songs: one of them came first for a "chill lo-fi" mood query.
#
# Matched on ARTIST, never on title. "Sleep Token" and "Sleep Theory" are real
# bands, and a title-based rule for "sleep" or "noise" would delete them.
NON_MUSIC_ARTIST_PATTERNS = (
    "white noise", "noise for", "rain sounds", "sleep sounds",
    "noise foundation", "baby sleep", "nature sounds", "asmr", "binaural",
)


def is_non_music(artist: str) -> bool:
    a = (artist or "").lower()
    return any(pat in a for pat in NON_MUSIC_ARTIST_PATTERNS)


def drop_non_music(tracks: dict) -> dict:
    kept = {i: t for i, t in tracks.items() if not is_non_music(t.artist)}
    dropped = len(tracks) - len(kept)
    if dropped:
        print(f"dropped {dropped} non-music tracks (generated ambience)")
    return kept


def cap_per_genre(tracks: dict[int, store.Track], cap: int) -> dict[int, store.Track]:
    """Limit how many tracks any one genre contributes.

    ListenBrainz popularity reflects that site's own listeners, so an
    uncapped pull can leave a single genre dominating the catalog. That skews
    the evaluation twice over: the random control rises towards the majority
    genre's share, and the humming study needs songs the raters actually know.

    Curated entries are kept ahead of scraped ones, since those are the songs
    somebody named on purpose.
    """
    from collections import defaultdict

    kept: dict[int, store.Track] = {}
    counts: dict[str, int] = defaultdict(int)

    ordered = sorted(tracks.values(), key=lambda t: (t.source != "curated", t.id))
    dropped = 0
    for t in ordered:
        genre = t.genre or "Unknown"
        if counts[genre] >= cap and t.source != "curated":
            dropped += 1
            continue
        counts[genre] += 1
        kept[t.id] = t

    if dropped:
        print(f"genre cap {cap}: dropped {dropped} tracks from over-represented genres")
    return kept


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=2000,
                    help="how many candidate titles to gather before resolving")
    ap.add_argument("--delay", type=float, default=0.35,
                    help="seconds between iTunes calls (it is rate limited)")
    ap.add_argument("--skip-listenbrainz", action="store_true",
                    help="use only data/curated_songs.txt")
    ap.add_argument("--reresolve", action="store_true",
                    help="drop cached lookups whose artist fails the check and "
                         "look them up again; good answers are left alone")
    ap.add_argument("--max-per-genre", type=int, default=0,
                    help="cap tracks per genre (0 = no cap). ListenBrainz "
                         "popularity is heavily skewed towards its own "
                         "userbase, so one genre can swamp the catalog.")
    args = ap.parse_args()

    config.ensure_dirs()

    curated = read_curated()
    print(f"curated list: {len(curated)} songs")

    candidates: dict[str, tuple[str, str]] = {
        norm_key(t, a): (t, a) for t, a in curated
    }
    sources = {norm_key(t, a): "curated" for t, a in curated}

    if not args.skip_listenbrainz:
        print("fetching ListenBrainz popular recordings...")
        for title, artist in fetch_listenbrainz(args.target):
            key = norm_key(title, artist)
            if key not in candidates:
                candidates[key] = (title, artist)
                sources[key] = "listenbrainz"

    print(f"\n{len(candidates)} unique candidates -> resolving via iTunes")
    print("(cached on disk; re-runs are free)\n")

    cache = load_cache()

    if args.reresolve:
        stale = [
            term for term, hit in cache.items()
            if hit and not artist_matches(term, hit.get("artistName", ""))
        ]
        for term in stale:
            del cache[term]
        print(f"--reresolve: dropped {len(stale)} cached lookups with a "
              f"mismatched artist; {len(cache)} good answers kept")

    tracks: dict[int, store.Track] = {}
    misses = 0

    try:
        for i, (key, (title, artist)) in enumerate(candidates.items(), 1):
            hit = resolve_itunes(title, artist, cache, args.delay)
            if hit and hit.get("trackId"):
                tracks[int(hit["trackId"])] = to_track(hit, sources[key])
            else:
                misses += 1
            if i % 25 == 0:
                print(f"  {i}/{len(candidates)}  resolved={len(tracks)} missed={misses}")
                save_cache(cache)
    except KeyboardInterrupt:
        print("\ninterrupted -- saving what we have")
    finally:
        save_cache(cache)

    tracks = drop_non_music(tracks)

    if args.max_per_genre:
        tracks = cap_per_genre(tracks, args.max_per_genre)

    conn = store.connect()
    store.init_schema(conn)
    n = store.upsert_tracks(conn, tracks.values())

    if args.reresolve:
        removed = prune_unbacked(conn, cache)
        if removed:
            print(f"pruned {removed} rows left over from mismatched lookups")

    store.rebuild_fts(conn)

    total = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
    genres = conn.execute(
        "SELECT genre, COUNT(*) c FROM tracks GROUP BY genre ORDER BY c DESC LIMIT 8"
    ).fetchall()
    conn.close()

    print(f"\nwrote {n} tracks; catalog now holds {total}")
    print("top genres: " + ", ".join(f"{g['genre']}({g['c']})" for g in genres))


if __name__ == "__main__":
    main()
