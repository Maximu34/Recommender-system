"""Query by humming: pitch-contour extraction and subsequence DTW matching.

Pipeline, identical for an indexed track and for a hum so the two are
comparable:

    audio -> pYIN f0 -> voiced frames -> median filter -> semitones
          -> subtract median (key invariance) -> resample to MELODY_HZ

Matching uses *subsequence* DTW rather than plain end-to-end DTW: a 6-second
hum corresponds to a short stretch somewhere inside a 30-second clip, so the
alignment must be free to start and end anywhere in the reference.
"""

from __future__ import annotations

import numpy as np

from . import config

# Tempo ratios tried for each query. The DTW step pattern absorbs local
# wobble; these cover a singer taking the tune globally faster or slower.
TEMPO_SCALES = (0.7, 0.85, 1.0, 1.2, 1.5)


HOP_LENGTH = 512


def extract_contour(y: np.ndarray, sr: int, monophonic: bool = False
                    ) -> tuple[np.ndarray, float]:
    """Return (normalised semitone contour, voiced_ratio).

    ``voiced_ratio`` is the fraction of frames where pYIN found a sustained
    pitch. It is how the melody index filters out beat-only and ambient
    tracks that humming could never match.

    Set ``monophonic`` for a hum query: it searches a narrower pitch band at
    coarser resolution, which is far faster and loses no accuracy on a single
    voice. Indexed tracks are polyphonic and need the wide search.
    """
    import librosa

    kwargs = dict(sr=sr, frame_length=2048, hop_length=HOP_LENGTH)
    if monophonic:
        kwargs.update(fmin=config.HUM_FMIN, fmax=config.HUM_FMAX,
                      resolution=config.HUM_RESOLUTION)
    else:
        kwargs.update(fmin=config.FMIN, fmax=config.FMAX)

    f0, voiced_flag, _ = librosa.pyin(y, **kwargs)
    if f0 is None or len(f0) == 0:
        return np.zeros(0, dtype=np.float32), 0.0

    voiced = np.asarray(voiced_flag, dtype=bool)
    voiced_ratio = float(voiced.mean()) if voiced.size else 0.0
    if voiced.sum() < 4:
        return np.zeros(0, dtype=np.float32), voiced_ratio

    # Hz -> MIDI semitones; keep only voiced frames.
    semis = 69.0 + 12.0 * np.log2(np.where(voiced, f0, np.nan) / 440.0)

    # Bridge short unvoiced gaps (breaths, consonants); leave long ones out.
    idx = np.arange(len(semis))
    good = ~np.isnan(semis)
    semis = np.interp(idx, idx[good], semis[good])

    semis = _median_filter(semis, 5)

    # Key invariance: only the shape of the melody matters, not its pitch.
    semis = semis - np.median(semis)

    # Resample to a fixed rate so query and reference share a time base.
    # Derived from the hop actually used -- hardcoding 512 here would silently
    # skew the time base if the hop ever changed.
    frame_hz = sr / HOP_LENGTH
    n_out = max(2, int(round(len(semis) / frame_hz * config.MELODY_HZ)))
    contour = np.interp(
        np.linspace(0, len(semis) - 1, n_out), np.arange(len(semis)), semis
    )
    return contour.astype(np.float32), voiced_ratio


def _median_filter(x: np.ndarray, k: int) -> np.ndarray:
    if k <= 1 or len(x) < k:
        return x
    pad = k // 2
    padded = np.pad(x, pad, mode="edge")
    strided = np.lib.stride_tricks.sliding_window_view(padded, k)
    return np.median(strided, axis=-1)


def subsequence_dtw(query: np.ndarray, ref: np.ndarray) -> float:
    """Cost of the best alignment of ``query`` against any stretch of ``ref``.

    Uses a step pattern whose moves all advance the query by one frame --
    (i-1, j), (i-1, j-1), (i-1, j-2) -- so each row depends only on the
    previous one and the whole matrix can be filled with vectorised numpy.
    A step pattern with horizontal moves would serialise the inner loop and
    make scanning a few thousand tracks far too slow in Python.
    """
    n, m = len(query), len(ref)
    if n == 0 or m == 0:
        return float("inf")
    if m < n // 2:
        return float("inf")

    # Row 0: free start -- the query may begin anywhere in the reference.
    prev = np.abs(ref - query[0])

    big = np.float32(1e9)
    for i in range(1, n):
        cost = np.abs(ref - query[i])

        shift1 = np.empty_like(prev)
        shift1[0] = big
        shift1[1:] = prev[:-1]

        shift2 = np.empty_like(prev)
        shift2[:2] = big
        shift2[2:] = prev[:-2]

        prev = cost + np.minimum(prev, np.minimum(shift1, shift2))

    # Free end: the alignment may finish anywhere in the reference.
    return float(prev.min() / n)


class MelodyIndex:
    """Pitch contours packed into one matrix so DTW runs across all tracks at once.

    Scoring tracks one at a time costs about 43 ms each, so a few hundred
    melodies already blows a 3-second query budget. Padding every contour into
    a single ``(n_tracks, max_len)`` matrix lets the DTW recurrence advance all
    tracks simultaneously: the only Python-level loop left is over the query's
    frames (about 60), and each step is one numpy operation over the whole
    matrix.
    """

    PAD = np.float32(1e6)   # padded cells can never win a minimum

    def __init__(self, contours: dict[int, np.ndarray]):
        self.track_ids = list(contours)
        if not self.track_ids:
            self.refs = np.zeros((0, 0), dtype=np.float32)
            self.lengths = np.zeros(0, dtype=int)
            return
        self.lengths = np.array([len(contours[t]) for t in self.track_ids])
        width = int(self.lengths.max())
        refs = np.full((len(self.track_ids), width), self.PAD, dtype=np.float32)
        for row, tid in enumerate(self.track_ids):
            c = contours[tid]
            refs[row, : len(c)] = c
        self.refs = refs

    def __len__(self) -> int:
        return len(self.track_ids)

    def _costs(self, query: np.ndarray) -> np.ndarray:
        """Subsequence-DTW cost of ``query`` against every track. Shape (n,)."""
        R = self.refs
        n = len(query)
        if n == 0 or R.size == 0:
            return np.full(len(self.track_ids), np.inf, dtype=np.float32)

        prev = np.abs(R - query[0])          # free start anywhere in each ref
        big = self.PAD

        for i in range(1, n):
            cost = np.abs(R - query[i])

            shift1 = np.empty_like(prev)
            shift1[:, 0] = big
            shift1[:, 1:] = prev[:, :-1]

            shift2 = np.empty_like(prev)
            shift2[:, :2] = big
            shift2[:, 2:] = prev[:, :-2]

            prev = cost + np.minimum(prev, np.minimum(shift1, shift2))

        # Free end, but only within each track's real length.
        valid = np.arange(R.shape[1])[None, :] < self.lengths[:, None]
        prev = np.where(valid, prev, np.inf)
        costs = prev.min(axis=1) / n

        # A reference much shorter than the query cannot contain it. Without
        # this, a short flat contour can score deceptively well against a flat
        # stretch of a hum.
        costs = np.where(self.lengths >= n // 2, costs, np.inf)
        return costs

    def match(self, query: np.ndarray, k: int = 20) -> list[tuple[int, float]]:
        """Rank tracks against a hummed contour. Lower cost is better."""
        if len(query) == 0 or not self.track_ids:
            return []

        best = np.full(len(self.track_ids), np.inf, dtype=np.float32)
        for scale in TEMPO_SCALES:
            n_out = max(4, int(round(len(query) * scale)))
            variant = np.interp(
                np.linspace(0, len(query) - 1, n_out),
                np.arange(len(query)),
                query,
            ).astype(np.float32)
            best = np.minimum(best, self._costs(variant))

        order = np.argsort(best)[:k]
        return [(self.track_ids[i], float(best[i])) for i in order]


def match(query: np.ndarray, index, k: int = 20) -> list[tuple[int, float]]:
    """Rank indexed tracks against a hummed contour.

    Accepts either a :class:`MelodyIndex` or a plain ``{track_id: contour}``
    mapping, so callers and tests can pass whichever they have.
    """
    if not isinstance(index, MelodyIndex):
        index = MelodyIndex(index)
    return index.match(query, k=k)
