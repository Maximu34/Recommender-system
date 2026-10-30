"""FastAPI service for the tune-based recommender.

Endpoint map (note the deliberate split between the two text paths):

    GET  /find?q=              the song + its neighbours, in one call
    GET  /search?q=            title/artist/lyric lookup -> full-text, no model
    GET  /similar/{id}         "sounds like this"    -> CLAP audio embedding
    POST /similar-by-text      "dreamy rainy guitar" -> CLAP *text* embedding
    POST /hum                  hummed melody         -> pYIN + subsequence DTW
    GET  /track/{id}           metadata + descriptors
    GET  /audio/{id}           cached 30s clip
"""

from __future__ import annotations

import json
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import (BackgroundTasks, FastAPI, File, HTTPException, Query,
                     UploadFile)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import audio as audio_io, config, itunes, melody, snippets, store

# Loaded once at startup and shared by every request.
STATE: dict = {
    "clap": None,          # store.VectorIndex
    "baseline": None,      # store.VectorIndex
    "melody": {},          # {track_id: np.ndarray}
    "descriptors": {},     # {track_id: dict}
    "moods": {},           # {preset text: np.ndarray} -- precomputed
}


def _load_indices() -> None:
    if config.CLAP_MATRIX.exists():
        ids_path = config.CLAP_MATRIX.with_name(config.CLAP_MATRIX.stem + "_ids.json")
        if ids_path.exists():
            STATE["clap"] = store.VectorIndex.load(config.CLAP_MATRIX, ids_path)

    if config.BASELINE_MATRIX.exists():
        ids_path = config.BASELINE_MATRIX.with_name(
            config.BASELINE_MATRIX.stem + "_ids.json")
        if ids_path.exists():
            # Hand-crafted features need z-scoring; CLAP embeddings do not.
            STATE["baseline"] = store.VectorIndex.load(
                config.BASELINE_MATRIX, ids_path, standardize=True)

    if config.MELODY_INDEX.exists():
        raw = json.loads(config.MELODY_INDEX.read_text())
        STATE["melody"] = melody.MelodyIndex(
            {int(k): np.asarray(v, dtype=np.float32) for k, v in raw.items()})

    if config.DESCRIPTORS.exists():
        raw = json.loads(config.DESCRIPTORS.read_text())
        STATE["descriptors"] = {int(k): v for k, v in raw.items()}

    # Precomputed mood-preset vectors. They let a deployed instance serve the
    # mood tiles without torch and a 586 MB checkpoint -- about 1 GB resident,
    # more than a free tier allows.
    if config.MOOD_VECTORS.exists():
        raw = json.loads(config.MOOD_VECTORS.read_text())
        STATE["moods"] = {
            k: np.asarray(v, dtype=np.float32)
            for k, v in raw.get("presets", {}).items()
        }


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_indices()
    c, b, m = STATE["clap"], STATE["baseline"], STATE["melody"]
    print(f"indices loaded -- clap={len(c) if c else 0} "
          f"baseline={len(b) if b else 0} melody={len(m)}")
    yield


app = FastAPI(title="Hummingbird API", lifespan=lifespan)

# The Expo client runs on a phone, so every request is cross-origin.
#
# Worth being honest about what this does and does not buy: CORS is enforced by
# browsers, and a React Native app is not a browser. Restricting origins will
# not stop anyone curling this API once it is public -- it only affects a web
# build. The real protections for a deployed instance are rate limiting and,
# if it ever holds user data, authentication. Neither is needed yet because the
# API is read-only over a public music catalog.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _conn():
    """A short-lived connection for one request.

    The server never calls ``init_schema``. Creating schema is a setup step
    owned by the build and migration scripts -- running the DDL per request is
    merely wasteful on SQLite, but against Postgres it re-runs CREATE EXTENSION
    and index creation every time and trips the statement timeout.
    """
    return store.connect()


def _index_for(engine: str) -> store.VectorIndex:
    idx = STATE.get(engine)
    if idx is None:
        raise HTTPException(
            503, f"{engine} index not built yet -- run scripts/build_index.py")
    return idx


def _hydrate(pairs: list[tuple[int, float]], score_name: str = "similarity") -> list[dict]:
    """Attach metadata + descriptors to (track_id, score) pairs."""
    conn = _conn()
    tracks = store.get_tracks(conn, [tid for tid, _ in pairs])
    conn.close()

    out = []
    for tid, score in pairs:
        t = tracks.get(tid)
        if not t:
            continue
        row = t.as_dict()
        # Neither belongs in a response: the path is meaningless off this
        # machine, and lyrics are stored for indexing only.
        row.pop("local_path", None)
        row.pop("lyrics", None)
        row[score_name] = round(float(score), 4)
        row["descriptors"] = STATE["descriptors"].get(tid)
        out.append(row)
    return out


def _mmr(candidates: list[tuple[int, float]], index: store.VectorIndex,
         k: int, diversity: float) -> list[tuple[int, float]]:
    """Maximal Marginal Relevance re-ranking.

    ``diversity`` of 0 keeps the pure similarity ranking; higher values trade
    similarity for variety, which is what the playlist slider exposes.
    """
    if diversity <= 0 or not candidates:
        return candidates[:k]

    lam = 1.0 - min(diversity, 0.95)
    chosen: list[tuple[int, float]] = []
    pool = list(candidates)

    while pool and len(chosen) < k:
        if not chosen:
            chosen.append(pool.pop(0))
            continue
        chosen_mat = np.stack([index.vector_for(tid) for tid, _ in chosen])
        best_i, best_val = 0, -np.inf
        for i, (tid, score) in enumerate(pool):
            redundancy = float(np.max(chosen_mat @ index.vector_for(tid)))
            val = lam * score - (1 - lam) * redundancy
            if val > best_val:
                best_i, best_val = i, val
        chosen.append(pool.pop(best_i))
    return chosen


@app.get("/health")
def health() -> dict:
    conn = _conn()
    try:
        total, with_audio = store.count_tracks(conn)
    finally:
        conn.close()
    return {
        "status": "ok",
        "db": store.backend_name(),
        "tracks": total,
        "tracks_with_audio": with_audio,
        "clap_index": len(STATE["clap"]) if STATE["clap"] else 0,
        "baseline_index": len(STATE["baseline"]) if STATE["baseline"] else 0,
        "melody_index": len(STATE["melody"]),
    }


@app.get("/search")
def search(q: str = Query(..., min_length=1), limit: int = 20) -> list[dict]:
    """Song *title* search. Plain metadata lookup -- no embedding model."""
    conn = _conn()
    try:
        results = store.search_tracks(conn, q, limit)
    finally:
        conn.close()
    return [_public(t, q) for t in results]


def _public(t: store.Track, query: str | None = None) -> dict:
    """A track as the client sees it: no lyrics, no server paths."""
    row = t.as_dict()
    row.pop("local_path", None)
    row.pop("lyrics", None)
    row["descriptors"] = STATE["descriptors"].get(t.id)
    if query:
        field = snippets.matched_by(t, query)
        row["matched_by"] = field
        if field == "lyrics":
            # Show the line that matched, so a lyric hit explains itself.
            row["matched_line"] = snippets.lyric_snippet(t.lyrics, query)
    return row


def _can_index_live() -> bool:
    """Can this instance embed a newly discovered song?

    A deployed instance ships without torch to fit a free tier, so it can find
    and play a song but never embed one. Saying so up front stops the client
    polling for recommendations that are never coming.
    """
    try:
        import torch  # noqa: F401
    except ImportError:
        return False
    return STATE.get("clap") is not None


def _index_live_track(track: store.Track) -> None:
    """Download and embed a newly discovered song, in the background.

    Done off the request because it is slow: about 12s for the hand-crafted
    features, and over a minute if CLAP has to load its checkpoint first. The
    song is playable immediately; recommendations appear once this finishes
    and the client asks again.

    Failures are swallowed on purpose. This is opportunistic work -- the track
    is already in the catalog, so the next full index build will pick it up
    regardless.
    """
    import urllib.request

    if not track.preview_url:
        return
    try:
        config.ensure_dirs()
        dest = config.PREVIEWS / f"{track.id}.m4a"
        if not dest.exists():
            with urllib.request.urlopen(track.preview_url, timeout=30) as r:
                data = r.read()
            if len(data) < 10_000:
                return
            dest.write_bytes(data)

        conn = _conn()
        try:
            store.set_local_path(conn, track.id, str(dest))
        finally:
            conn.close()

        # Decode straight at the melody rate rather than at 48 kHz and
        # resampling, which cost 4 of the 12 seconds.
        clap_index = STATE.get("clap")
        if clap_index is not None and not clap_index.has(track.id):
            from . import embed

            y48 = audio_io.load_audio(dest, config.CLAP_SR)
            clap_index.add(track.id, embed.embed_audio([y48])[0])
            print(f"indexed on demand: {track.title} ({track.id})")
    except Exception as exc:                       # noqa: BLE001
        print(f"on-demand indexing failed for {track.id}: {exc}")


def _live_lookup(q: str, background: BackgroundTasks | None = None) -> dict | None:
    """Find a song on iTunes that the catalog does not hold.

    The track is added to the catalog so it is there next time, but it has no
    embedding yet -- that needs the audio downloaded and indexed offline. The
    response says so rather than returning an empty recommendation list with
    no explanation.
    """
    try:
        hit = itunes.find_track(q)
    except itunes.Unavailable:
        # Apple throttled or timed out. Say so rather than letting it look
        # like the song does not exist.
        return {
            "query": q,
            "match": None,
            "match_type": None,
            "from_itunes": False,
            "itunes_unavailable": True,
            "note": (
                "We do not have this song, and could not reach iTunes to look "
                "it up just now. Try again in a moment."
            ),
            "alternatives": [],
            "results": [],
        }

    if not hit or not hit.get("trackId"):
        return None

    track = store.Track(
        id=int(hit["trackId"]),
        title=hit.get("trackName", ""),
        artist=hit.get("artistName", ""),
        album=hit.get("collectionName"),
        genre=hit.get("primaryGenreName"),
        preview_url=hit.get("previewUrl"),
        artwork_url=hit.get("artworkUrl100"),
        duration_ms=hit.get("trackTimeMillis"),
        source="live",
    )
    try:
        conn = _conn()
        try:
            store.upsert_tracks(conn, [track])
        finally:
            conn.close()
    except Exception:
        # Persisting is a nicety -- the catalog grows as people search. Never
        # fail the request over it.
        pass

    can_index = background is not None and _can_index_live()
    if can_index:
        background.add_task(_index_live_track, track)

    return {
        "query": q,
        "match": _public(track, q),
        "match_type": "title",
        "found_by_title": True,
        "from_itunes": True,
        "indexed": False,
        "indexing": can_index,
        "note": (
            "This song was not in our catalog, so it came from iTunes. It is "
            "being analysed now -- recommendations appear in a few seconds."
            if can_index else
            "This song was not in our catalog, so it came from iTunes. It "
            "plays, but this instance cannot analyse new songs, so there are "
            "no recommendations for it."
        ),
        "catalog_size": len(STATE["clap"]) if STATE["clap"] else 0,
        "alternatives": [],
        "results": [],
    }


@app.get("/find")
def find(background: BackgroundTasks, q: str = Query(..., min_length=1),
         k: int = 20, engine: str = "clap", diversity: float = 0.0) -> dict:
    """One-step search: the song you meant, plus songs that sound like it.

    Typing a title (or a half-remembered lyric) should land on the song
    directly rather than making the user pick from a list and tap again, so
    this resolves the best match and returns its neighbours with it.
    ``alternatives`` carries the runners-up for when the top hit is wrong.
    """
    conn = _conn()
    try:
        hits = store.search_tracks(conn, q, limit=6)
    finally:
        conn.close()

    # Nothing in the catalog matched the *title*. Falling back to a lyric hit
    # here is how searching "no lie" returned a BTS track whose lyrics repeat
    # that phrase, presented as though it were the song asked for. Ask iTunes
    # instead, so a song outside our 500-odd tracks is still findable.
    local_title_hit = any(snippets.matched_by(t, q) == "title" for t in hits)
    if not hits or not local_title_hit:
        live = _live_lookup(q, background)
        # Only take the live answer when it actually found something.
        # A throttled iTunes returns a match-less response, and preferring
        # that over a real local hit is how a lyric search for "caught in a
        # landslide" stopped returning Bohemian Rhapsody.
        if live and live.get("match"):
            live["alternatives"] += [_public(t, q) for t in hits[:3]]
            return live
        if live and not hits:
            return live          # nothing local either: report the outage

    if not hits:
        return {"query": q, "match": None, "alternatives": [], "results": []}

    match = hits[0]

    # Say how the match was found. A lyric hit for a title we do not hold is
    # still a real match -- searching "no lie" finds a song whose lyrics
    # repeat that phrase -- but presenting it as "your song" tells the user we
    # found what they asked for when we did not. The client uses this to say
    # so plainly instead.
    match_type = snippets.matched_by(match, q)
    payload = {
        "query": q,
        "match": _public(match, q),
        "match_type": match_type,
        "found_by_title": match_type == "title",
        "catalog_size": len(STATE["clap"]) if STATE["clap"] else 0,
        "alternatives": [_public(t, q) for t in hits[1:]],
        "results": [],
    }

    index = STATE.get(engine if engine in ("clap", "baseline") else "clap")
    if index is not None and index.has(match.id):
        over = k * 4 if diversity > 0 else k
        pairs = index.search(index.vector_for(match.id), k=over,
                             exclude={match.id})
        payload["results"] = _hydrate(_mmr(pairs, index, k, diversity))
        payload["engine"] = engine
    return payload


@app.get("/similar/{track_id}")
def similar(track_id: int, k: int = 20, engine: str = "clap",
            diversity: float = 0.0, same_artist: bool = True) -> dict:
    """Songs that sound like ``track_id``."""
    if engine not in ("clap", "baseline"):
        raise HTTPException(400, "engine must be 'clap' or 'baseline'")
    index = _index_for(engine)
    if not index.has(track_id):
        raise HTTPException(404, f"track {track_id} is not in the {engine} index")

    conn = _conn()
    seed = store.get_track(conn, track_id)
    conn.close()

    exclude = {track_id}
    if not same_artist and seed:
        conn = _conn()
        try:
            exclude |= store.ids_by_artist(conn, seed.artist)
        finally:
            conn.close()

    over = k * 4 if diversity > 0 else k
    pairs = index.search(index.vector_for(track_id), k=over, exclude=exclude)
    pairs = _mmr(pairs, index, k, diversity)

    return {
        "seed": ({**seed.as_dict(), "descriptors": STATE["descriptors"].get(track_id)}
                 if seed else None),
        "engine": engine,
        "results": _hydrate(pairs),
    }


def _text_vector(text: str) -> np.ndarray:
    """Embed a mood query, using CLAP when it is installed.

    A deployed instance ships without torch, because the model is about 1 GB
    resident and a free tier will not hold it. Only the precomputed presets
    can be answered there, so an unknown phrase gets a 503 naming what is
    missing and which phrases do work -- rather than plausible nonsense.
    """
    try:
        from . import embed

        return embed.embed_text([text])[0]
    except ImportError:
        pass          # torch absent; fall through to the presets

    moods = STATE["moods"]
    # Explicit None checks, not `a or b`: these values are numpy arrays, and
    # testing one for truthiness raises "truth value of an array with more
    # than one element is ambiguous".
    key = text.strip()
    preset = moods.get(key)
    if preset is None:
        preset = moods.get(key.lower())
    if preset is not None:
        return preset

    if moods:
        detail = (
            "Free-text mood search needs the CLAP model, which this instance "
            "does not ship. These presets work: " + ", ".join(sorted(moods))
        )
    else:
        detail = "Mood search is unavailable on this instance."
    raise HTTPException(503, detail)


class TextQuery(BaseModel):
    text: str
    k: int = 20
    diversity: float = 0.0


@app.post("/similar-by-text")
def similar_by_text(body: TextQuery) -> dict:
    """Mood/vibe search, e.g. "dreamy guitar for a rainy evening".

    This is the CLAP *text* encoder, which shares a space with the audio
    embeddings. It is not how a song title is looked up -- see /search.
    """
    index = _index_for("clap")
    vec = _text_vector(body.text)
    over = body.k * 4 if body.diversity > 0 else body.k
    pairs = index.search(vec, k=over)
    pairs = _mmr(pairs, index, body.k, body.diversity)
    return {"query": body.text, "results": _hydrate(pairs)}


@app.post("/hum")
async def hum(file: UploadFile = File(...), k: int = 20) -> dict:
    """Match a hummed or sung melody against the melody index.

    The client records WAV/PCM (see the Expo recorder config); anything PyAV
    can decode will also work.
    """
    if not STATE["melody"] or not len(STATE["melody"]):
        raise HTTPException(
            503, "melody index not built -- run scripts/build_index.py --only melody")

    suffix = Path(file.filename or "hum.wav").suffix or ".wav"
    data = await file.read()
    if len(data) < 1000:
        raise HTTPException(400, "recording too short or empty")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        y = audio_io.load_audio(tmp_path, config.MELODY_SR, max_seconds=15)
        contour, voiced = melody.extract_contour(
            y, config.MELODY_SR, monophonic=True)
        if len(contour) < 8:
            raise HTTPException(
                422, "could not hear a clear melody -- hum a bit longer and steadier")
        pairs = melody.match(contour, STATE["melody"], k=k)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    # DTW yields a cost; invert it so the client always sorts by "higher is better".
    results = _hydrate([(tid, 1.0 / (1.0 + cost)) for tid, cost in pairs], "score")
    return {
        "voiced_ratio": round(voiced, 3),
        "contour": [round(float(v), 2) for v in contour],  # for the hum visualiser
        "results": results,
    }


@app.get("/track/{track_id}")
def track(track_id: int) -> dict:
    conn = _conn()
    t = store.get_track(conn, track_id)
    conn.close()
    if not t:
        raise HTTPException(404, "no such track")
    return {**t.as_dict(), "descriptors": STATE["descriptors"].get(track_id)}


@app.get("/audio/{track_id}")
def audio(track_id: int):
    conn = _conn()
    t = store.get_track(conn, track_id)
    conn.close()
    if not t or not t.local_path or not Path(t.local_path).exists():
        raise HTTPException(404, "no cached clip for that track")
    return FileResponse(t.local_path, media_type="audio/mp4")
