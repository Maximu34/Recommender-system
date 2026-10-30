"""Hand-crafted audio features.

Two jobs:

1. The **baseline** feature vector, which is the comparison arm of the
   experiment: classic MIR descriptors (MFCC, chroma, spectral shape, tempo)
   versus a learned CLAP embedding, on the same retrieval metric.
2. Human-readable **descriptors** -- tempo, key, brightness, energy -- which
   power the "why is this similar?" panel in the app.
"""

from __future__ import annotations

import numpy as np

# Krumhansl-Schmuckler key profiles, used to estimate a track's key from its
# averaged chroma vector.
_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _tempo(y: np.ndarray, sr: int) -> float:
    """Estimate tempo in BPM.

    librosa has moved this function twice (``librosa.beat.tempo`` ->
    ``librosa.feature.rhythm.tempo`` -> ``librosa.feature.tempo`` in 1.0), so
    resolve it at call time rather than importing a path that breaks on a
    different version.
    """
    import librosa

    fn = getattr(librosa.feature, "tempo", None)
    if fn is None:
        rhythm = getattr(librosa.feature, "rhythm", None)
        fn = getattr(rhythm, "tempo", None) if rhythm else None
    if fn is None:
        fn = getattr(librosa.beat, "tempo", None)
    if fn is None:
        raise RuntimeError("no tempo estimator found in this librosa version")
    return float(np.atleast_1d(fn(y=y, sr=sr))[0])


def baseline_features(y: np.ndarray, sr: int) -> np.ndarray:
    """~85-d hand-crafted descriptor vector for one clip."""
    import librosa

    if y.size == 0:
        raise ValueError("empty audio")

    parts: list[np.ndarray] = []

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    parts += [mfcc.mean(axis=1), mfcc.std(axis=1)]

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    parts += [chroma.mean(axis=1), chroma.std(axis=1)]

    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    parts += [contrast.mean(axis=1), contrast.std(axis=1)]

    for fn in (librosa.feature.spectral_centroid,
               librosa.feature.spectral_rolloff,
               librosa.feature.zero_crossing_rate):
        v = fn(y=y) if fn is librosa.feature.zero_crossing_rate else fn(y=y, sr=sr)
        parts += [np.array([v.mean()]), np.array([v.std()])]

    rms = librosa.feature.rms(y=y)
    parts += [np.array([rms.mean()]), np.array([rms.std()])]

    parts.append(np.array([_tempo(y, sr)]))

    return np.concatenate(parts).astype(np.float32)


def estimate_key(y: np.ndarray, sr: int) -> tuple[str, str]:
    """Estimate (pitch class, 'major'|'minor') by Krumhansl-Schmuckler."""
    import librosa

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    if chroma.sum() == 0:
        return "C", "major"
    chroma = chroma / chroma.sum()

    best, best_score = ("C", "major"), -np.inf
    for i in range(12):
        for name, profile in (("major", _MAJOR), ("minor", _MINOR)):
            score = float(np.corrcoef(np.roll(chroma, -i), profile)[0, 1])
            if score > best_score:
                best_score, best = score, (PITCH_CLASSES[i], name)
    return best


def descriptors(y: np.ndarray, sr: int) -> dict:
    """Interpretable summary of a clip, for the explainability panel."""
    import librosa

    tempo = _tempo(y, sr)
    centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
    rms = float(librosa.feature.rms(y=y).mean())
    key, mode = estimate_key(y, sr)
    return {
        "tempo_bpm": round(tempo, 1),
        "key": f"{key} {mode}",
        "brightness_hz": round(centroid, 1),
        "energy": round(rms, 4),
    }
