"""Storage: catalog metadata and embedding matrices.

Two concerns deliberately kept apart:

* **Metadata** -- the ``tracks`` table. This is what a typed *song title* search
  hits, and it never touches an embedding model. It lives behind a backend
  chosen by ``config.DB_BACKEND``: :mod:`app.store_sqlite` (default, no network,
  used by the evaluation scripts) or :mod:`app.store_postgres` (Supabase).
* **Embeddings** -- the ``.npy`` matrices, loaded into memory once and searched
  with a plain matrix multiply. These are backend-independent by design: at a
  few thousand tracks a matmul is sub-millisecond, whereas putting them in the
  database would add a network round-trip to every query. See the plan's
  "why not pgvector" note.

Callers import from here and never from a backend module directly, so switching
backends is a config change rather than an edit to eight call sites.
"""

from __future__ import annotations

import json
from typing import Iterable, Sequence

import numpy as np

from . import config
from .models import TRACK_COLUMNS, Track  # noqa: F401  (re-exported for callers)

__all__ = [
    "Track", "TRACK_COLUMNS", "VectorIndex", "backend", "backend_name",
    "connect", "init_schema", "upsert_tracks", "set_local_path", "rebuild_fts",
    "get_track", "get_tracks", "all_tracks", "search_tracks",
    "count_tracks", "ids_by_artist",
]


def backend():
    """The active storage backend module, selected by ``config.DB_BACKEND``."""
    name = (config.DB_BACKEND or "sqlite").lower()
    if name == "sqlite":
        from . import store_sqlite
        return store_sqlite
    if name in ("postgres", "postgresql", "supabase"):
        from . import store_postgres
        return store_postgres
    raise ValueError(
        f"unknown DB_BACKEND {name!r}; expected 'sqlite' or 'postgres'"
    )


def backend_name() -> str:
    return (config.DB_BACKEND or "sqlite").lower()


# --- metadata (delegated) -------------------------------------------------

def connect(path=None):
    return backend().connect(path)


def init_schema(conn) -> None:
    backend().init_schema(conn)


def upsert_tracks(conn, tracks: Iterable[Track]) -> int:
    return backend().upsert_tracks(conn, tracks)


def set_local_path(conn, track_id: int, path: str) -> None:
    backend().set_local_path(conn, track_id, path)


def rebuild_fts(conn) -> None:
    backend().rebuild_fts(conn)


def get_track(conn, track_id: int) -> Track | None:
    return backend().get_track(conn, track_id)


def get_tracks(conn, ids: Sequence[int]) -> dict[int, Track]:
    return backend().get_tracks(conn, ids)


def all_tracks(conn, with_audio: bool = False) -> list[Track]:
    return backend().all_tracks(conn, with_audio)


def search_tracks(conn, q: str, limit: int = 20) -> list[Track]:
    return backend().search_tracks(conn, q, limit)


def count_tracks(conn) -> tuple[int, int]:
    return backend().count_tracks(conn)


def ids_by_artist(conn, artist: str) -> set[int]:
    return backend().ids_by_artist(conn, artist)


# --- embedding matrices --------------------------------------------------

class VectorIndex:
    """In-memory embedding matrix with cosine search.

    Rows are L2-normalised at load, so cosine similarity is a single matrix
    multiply. At a few thousand tracks this is sub-millisecond -- an ANN
    library (FAISS/Qdrant) would add complexity for no gain.
    """

    def __init__(self, matrix: np.ndarray, track_ids: list[int],
                 standardize: bool = False):
        if matrix.shape[0] != len(track_ids):
            raise ValueError(
                f"matrix has {matrix.shape[0]} rows but {len(track_ids)} track ids"
            )
        matrix = matrix.astype(np.float32)

        if standardize:
            # Hand-crafted features live on wildly different scales -- MFCCs in
            # the hundreds, chroma in [0, 1], tempo around 120. Without
            # z-scoring, cosine similarity is decided almost entirely by the
            # largest-magnitude columns and the rest contribute nothing.
            self.mean = matrix.mean(axis=0)
            std = matrix.std(axis=0)
            std[std == 0] = 1.0
            self.std = std
            matrix = (matrix - self.mean) / self.std
        else:
            self.mean = None
            self.std = None

        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.matrix = (matrix / norms).astype(np.float32)
        self.track_ids = track_ids
        self._pos = {tid: i for i, tid in enumerate(track_ids)}

    @classmethod
    def load(cls, matrix_path, ids_path=None, standardize: bool = False
             ) -> "VectorIndex":
        ids_path = ids_path or config.TRACK_IDS_PATH
        matrix = np.load(matrix_path)
        track_ids = json.loads(ids_path.read_text())
        return cls(matrix, track_ids, standardize=standardize)

    def __len__(self) -> int:
        return len(self.track_ids)

    def has(self, track_id: int) -> bool:
        return track_id in self._pos

    def vector_for(self, track_id: int) -> np.ndarray:
        return self.matrix[self._pos[track_id]]

    def add(self, track_id: int, vector: np.ndarray) -> None:
        """Append one track to the in-memory index.

        Used when a song is found live and indexed on the spot, so it becomes
        recommendable without waiting for the next full build. Rebuilding the
        matrix for a single row is fine -- this happens once per newly
        discovered song, not per request.

        Standardised indices are deliberately refused: their column mean and
        standard deviation were fitted over the whole catalog, and appending a
        raw row would put it on a different scale from every other row.
        """
        if self.mean is not None:
            raise ValueError("cannot append to a standardised index")
        if track_id in self._pos:
            return

        v = np.asarray(vector, dtype=np.float32).ravel()
        n = np.linalg.norm(v)
        if n:
            v = v / n
        self.matrix = np.vstack([self.matrix, v[None, :]]).astype(np.float32)
        self._pos[track_id] = len(self.track_ids)
        self.track_ids.append(track_id)

    def search(
        self, query: np.ndarray, k: int = 20, exclude: set[int] | None = None
    ) -> list[tuple[int, float]]:
        q = query.astype(np.float32).ravel()
        n = np.linalg.norm(q)
        if n:
            q = q / n
        scores = self.matrix @ q

        exclude = exclude or set()
        # Over-fetch so that excluded ids can be dropped without a second pass.
        take = min(len(scores), k + len(exclude))
        top = np.argpartition(-scores, take - 1)[:take]
        top = top[np.argsort(-scores[top])]

        out: list[tuple[int, float]] = []
        for i in top:
            tid = self.track_ids[i]
            if tid in exclude:
                continue
            out.append((tid, float(scores[i])))
            if len(out) == k:
                break
        return out
