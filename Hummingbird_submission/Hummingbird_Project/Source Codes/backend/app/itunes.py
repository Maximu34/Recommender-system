"""iTunes lookup, shared by catalog building and live search.

The catalog can only ever hold a slice of recorded music, so a user will
routinely ask for something that is not in it. Rather than quietly answering
with whatever the local index can offer -- which is how searching "no lie"
returned a BTS track whose lyrics happen to repeat that phrase -- the API
falls back to asking iTunes directly.

Artist verification lives here too, because both callers need it: accepting
the top hit blindly returned a lullaby cover of Green Day for "Boulevard of
Broken Dreams" and a Migos track for "Nuts RM".
"""

from __future__ import annotations

import json
import re
import unicodedata
import urllib.parse
import urllib.request

ENDPOINT = "https://itunes.apple.com/search"
UA = {"User-Agent": "Hummingbird/0.1 (final-year project; contact: student)"}


def _words(s: str) -> set[str]:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return {w for w in re.sub(r"[^a-z0-9]+", " ", s.lower()).split() if w}


def _artist_words(artist: str) -> set[str]:
    """Artist name reduced to comparable tokens.

    Only the *artist* is trimmed, of the qualifiers iTunes appends. The query
    is never trimmed: an earlier version stripped everything after the word
    "with" and so deleted the whole of "With or Without You U2".
    """
    artist = re.sub(r"\(.*?\)|\[.*?\]", " ", artist or "")
    # Word boundaries matter: without them "ft" matches inside "Daft Punk" and
    # "Swift", truncating them to "Da" and "Swi".
    artist = re.split(r"\bfeat\b|\bft\b|\bwith\b|&|,", artist, flags=re.I)[0]
    return _words(artist)


def artist_matches(query: str, artist: str) -> bool:
    """Does ``artist`` plausibly answer ``query``?

    One shared token is enough. Short and punctuated names -- U2, AC/DC, a-ha,
    R.E.M. -- survive normalisation badly, so requiring more rejects correct
    rows. Verified against the hand-curated songs: it rejects none of them.
    """
    aw = _artist_words(artist)
    return bool(aw and (aw & _words(query)))


def title_matches(query: str, title: str) -> bool:
    """Is every word of the query present in the title?

    Used for *live* lookup, where the query is a title the user typed rather
    than a "title artist" pair. Stricter than artist matching on purpose: a
    live result is shown as the song they asked for, so a loose match here is
    worse than no result.
    """
    tw = _words(title)
    qw = _words(query)
    return bool(qw and qw <= tw)


class Unavailable(Exception):
    """iTunes could not be reached -- not the same as finding nothing.

    Apple rate limits this endpoint hard (403), and an earlier version
    returned [] on any failure. That made a throttled lookup identical to a
    genuine miss, so a famous song would be reported as "not found" purely
    because a catalog build was competing for quota at the time.
    """


def search(term: str, limit: int = 8, timeout: int = 8) -> list[dict]:
    """Raw iTunes results for ``term``.

    Raises :class:`Unavailable` when the request itself fails, so callers can
    tell "Apple said no such song" from "we could not ask Apple".
    """
    url = ENDPOINT + "?" + urllib.parse.urlencode(
        {"term": term, "media": "music", "entity": "song", "limit": limit}
    )
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=UA), timeout=timeout
        ) as r:
            return json.load(r).get("results") or []
    except Exception as exc:
        raise Unavailable(str(exc)) from exc


def find_track(query: str) -> dict | None:
    """Best iTunes track for a typed query, or None if there genuinely is none.

    Requires a preview URL -- a result we cannot play is no use -- and that
    every word of the query appears in the title, so "no lie" returns the song
    called "No Lie" rather than something merely related.

    Propagates :class:`Unavailable` rather than reporting a miss.
    """
    for hit in search(query):
        if hit.get("previewUrl") and title_matches(query, hit.get("trackName", "")):
            return hit
    return None
