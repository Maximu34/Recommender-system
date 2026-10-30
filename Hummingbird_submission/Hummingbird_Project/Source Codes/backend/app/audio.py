"""One decode path for every audio file in the project.

iTunes previews are AAC in an m4a container, which libsndfile (and therefore
``soundfile``/``librosa``) cannot read, and there is no system ffmpeg on the
target machine. PyAV ships its own ffmpeg libraries inside the wheel, so it
decodes m4a, mp3 and wav with no external install.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


def load_audio(path: str | Path, sr: int, max_seconds: float | None = None) -> np.ndarray:
    """Decode ``path`` to a mono float32 array at ``sr`` Hz, values in [-1, 1]."""
    import av  # imported lazily so that non-audio code paths don't pay for it

    path = str(path)
    chunks: list[np.ndarray] = []

    with av.open(path) as container:
        if not container.streams.audio:
            raise ValueError(f"no audio stream in {path}")
        stream = container.streams.audio[0]
        stream.thread_type = "AUTO"

        resampler = av.AudioResampler(format="fltp", layout="mono", rate=sr)
        limit = int(max_seconds * sr) if max_seconds else None
        total = 0

        for frame in container.decode(stream):
            for out in resampler.resample(frame):
                arr = out.to_ndarray()          # (1, n) for mono fltp
                chunks.append(arr)
                total += arr.shape[-1]
            if limit and total >= limit:
                break
        else:
            # Flush the resampler only when decoding ran to completion.
            for out in resampler.resample(None):
                chunks.append(out.to_ndarray())

    if not chunks:
        raise ValueError(f"decoded no samples from {path}")

    audio = np.concatenate(chunks, axis=-1).ravel().astype(np.float32)
    if limit:
        audio = audio[:limit]
    return audio


def probe(path: str | Path) -> dict:
    """Container/codec/duration, for the install gate and for debugging."""
    import av

    with av.open(str(path)) as c:
        if not c.streams.audio:
            return {"error": "no audio stream"}
        s = c.streams.audio[0]
        return {
            "format": c.format.name,
            "codec": s.codec_context.name,
            "sample_rate": s.codec_context.sample_rate,
            "channels": s.codec_context.channels,
            "duration_s": round(float(c.duration) / 1_000_000, 2) if c.duration else None,
        }
