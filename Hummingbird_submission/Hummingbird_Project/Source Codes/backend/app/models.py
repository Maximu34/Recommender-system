"""Shared data types.

``Track`` lives here rather than in :mod:`app.store` so that both storage
backends can import it without a circular import, since ``store`` is what
dispatches to them.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

# Column order used by every backend's INSERT. Keeping it in one place means a
# new column cannot be added to one backend and forgotten in the other.
TRACK_COLUMNS = (
    "id", "title", "artist", "album", "genre",
    "preview_url", "artwork_url", "duration_ms", "local_path", "source",
    "lyrics",
)


@dataclass
class Track:
    id: int
    title: str
    artist: str
    album: str | None = None
    genre: str | None = None
    preview_url: str | None = None
    artwork_url: str | None = None
    duration_ms: int | None = None
    # Absolute path to the cached clip on the machine that downloaded it. It is
    # meaningless on any other machine, including a deployed server -- see the
    # note in scripts/build_index.py.
    local_path: str | None = None
    source: str | None = None       # 'listenbrainz' | 'curated'
    # Plain lyrics, stored so the catalog can be searched by a remembered line.
    # Never returned to clients: the API strips this and returns only the single
    # matching line as a snippet, which is what a search result needs and avoids
    # redistributing a copyrighted work.
    lyrics: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)

    def as_row(self) -> tuple:
        """Values in TRACK_COLUMNS order, for parameterised inserts."""
        return tuple(getattr(self, c) for c in TRACK_COLUMNS)
