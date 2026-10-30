"""Precompute CLAP text embeddings for the mood presets.

Mood search normally runs a query through CLAP's text encoder, which means
shipping torch and a 586 MB checkpoint -- about 1 GB resident, more than a
free hosting tier allows. But the *presets* are a fixed list, so their vectors
can be computed once here and shipped as a small file: six vectors is 12 KB.

The deployed backend then serves the mood tiles with no model at all. Only
free-text mood search needs the real encoder, and the API says so plainly
rather than silently returning nonsense.

Run this locally (where torch is installed) whenever the preset list changes:

    python -m scripts.precompute_moods
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config  # noqa: E402

# Must match MOODS in web/src/App.tsx and MOOD_PRESETS in mobile/App.tsx.
PRESETS = [
    "acoustic folk guitar",
    "dreamy synth pop",
    "chill lo-fi beats",
    "upbeat indie rock",
    "cinematic ambient",
    "smooth jazz",
]


def main() -> None:
    from app import embed

    print(f"embedding {len(PRESETS)} mood presets with {config.CLAP_MODEL}")
    vectors = embed.embed_text(PRESETS)

    payload = {
        "model": config.CLAP_MODEL,
        "dim": int(vectors.shape[1]),
        "presets": {p: [round(float(v), 6) for v in vec]
                    for p, vec in zip(PRESETS, vectors)},
    }
    config.MOOD_VECTORS.write_text(json.dumps(payload), encoding="utf-8")

    size_kb = config.MOOD_VECTORS.stat().st_size / 1024
    print(f"wrote {len(PRESETS)} vectors of dim {payload['dim']} "
          f"to {config.MOOD_VECTORS.name} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
