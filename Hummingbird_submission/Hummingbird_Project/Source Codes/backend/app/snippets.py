"""Pull the one lyric line that explains why a track matched a search.

Lyrics are stored for indexing but never served whole: a search result needs
to show *why* it matched, and a single line does that without redistributing a
copyrighted work. Matching happens in Python rather than via a database
snippet function so SQLite and Postgres produce identical output.
"""

from __future__ import annotations

INSTRUMENTAL = "[instrumental]"


def _tokens(text: str) -> list[str]:
    return [t for t in "".join(
        c.lower() if c.isalnum() else " " for c in text
    ).split() if t]


def lyric_snippet(lyrics: str | None, query: str, max_len: int = 90) -> str | None:
    """The lyric line best matching ``query``, or None.

    Returns None when the query is already explained by the title or artist --
    the caller decides that -- and when the track is instrumental.
    """
    if not lyrics or lyrics == INSTRUMENTAL:
        return None

    wanted = set(_tokens(query))
    if not wanted:
        return None

    best_line, best_score = None, 0
    for line in lyrics.splitlines():
        line = line.strip()
        if not line:
            continue
        line_tokens = set(_tokens(line))
        # Count whole-token hits first; fall back to prefix hits so a partial
        # word still matches the way search-as-you-type does.
        score = len(wanted & line_tokens)
        if not score:
            score = sum(
                1 for w in wanted
                if any(tok.startswith(w) for tok in line_tokens)
            )
        if score > best_score:
            best_line, best_score = line, score

    if not best_line:
        return None
    if len(best_line) > max_len:
        best_line = best_line[: max_len - 1].rstrip() + "\u2026"
    return best_line


def matched_by(track, query: str) -> str:
    """Which field explains this hit: 'title', 'artist' or 'lyrics'."""
    wanted = set(_tokens(query))
    if wanted & set(_tokens(track.title or "")):
        return "title"
    if wanted & set(_tokens(track.artist or "")):
        return "artist"
    return "lyrics"
