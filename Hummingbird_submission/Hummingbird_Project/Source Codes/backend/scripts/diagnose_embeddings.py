"""Diagnose an embedding space: is it actually discriminative?

Built after the first CLAP index returned Billie Jean as the nearest
neighbour of Take Five at 0.992 similarity. High cosine numbers can hide a
degenerate space, so this reports the things that reveal one:

* **Pairwise cosine spread.** If unrelated tracks all sit near 1.0, the space
  is not separating anything.
* **Mean-vector norm (anisotropy).** If every embedding is mostly one shared
  direction, cosine is dominated by that common component. A norm near 1.0 is
  pathological; near 0 is healthy.
* **Top singular value share.** How much variance one direction absorbs.
* **Text-query discrimination.** For a joint audio-text model, four unrelated
  prompts must produce four different rankings. Identical rankings are the
  signature of a degenerate audio space -- the constant component decides the
  order, so the query barely matters.

Usage:
    python -m scripts.diagnose_embeddings
    python -m scripts.diagnose_embeddings --matrix ../data/embeddings_clap_fixed.npy
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config, store  # noqa: E402

PROMPTS = [
    "jazz saxophone and piano",
    "heavy distorted electric guitar rock",
    "hip hop rap beat",
    "solo acoustic folk guitar",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", default=str(config.CLAP_MATRIX))
    ap.add_argument("--standardize", action="store_true")
    ap.add_argument("--skip-text", action="store_true",
                    help="skip the text probe (avoids loading the model)")
    args = ap.parse_args()

    matrix_path = Path(args.matrix)
    ids_path = matrix_path.with_name(matrix_path.stem + "_ids.json")
    if not (matrix_path.exists() and ids_path.exists()):
        print(f"no index at {matrix_path}")
        return

    index = store.VectorIndex.load(matrix_path, ids_path,
                                   standardize=args.standardize)
    M = index.matrix
    conn = store.connect()
    store.init_schema(conn)
    tracks = {t.id: t for t in store.all_tracks(conn)}
    conn.close()

    print(f"\nindex: {matrix_path.name}  {M.shape}\n")

    S = M @ M.T
    off = S[~np.eye(len(M), dtype=bool)]
    print("pairwise cosine")
    print(f"   mean={off.mean():+.3f}  std={off.std():.3f}  "
          f"min={off.min():+.3f}  max={off.max():+.3f}")
    if off.mean() > 0.8:
        print("   ^ PATHOLOGICAL: unrelated tracks are all near-identical")

    mu = np.linalg.norm(M.mean(axis=0))
    print(f"\nanisotropy (mean-vector norm) = {mu:.3f}")
    print("   0.0 = healthy, isotropic;  1.0 = every vector points the same way")
    if mu > 0.7:
        print(f"   ^ {mu * 100:.0f}% of each embedding is one shared direction")

    _, sv, _ = np.linalg.svd(M - M.mean(axis=0), full_matrices=False)
    share = sv**2 / (sv**2).sum()
    print(f"\ntop-5 variance share: {np.round(share[:5], 3).tolist()}")

    if args.skip_text:
        return

    from app import embed

    print("\ntext-query discrimination (four unrelated prompts)")
    rankings = []
    for q in PROMPTS:
        vec = embed.embed_text([q])[0]
        scores = M @ vec
        top = np.argsort(-scores)[:3]
        rankings.append(tuple(index.track_ids[j] for j in top))
        print(f'   "{q}"')
        for j in top:
            t = tracks.get(index.track_ids[j])
            name = f"{t.title[:30]} [{t.genre}]" if t else index.track_ids[j]
            print(f"       {scores[j]:+.3f}  {name}")

    distinct = len(set(rankings))
    print(f"\n   {distinct}/{len(PROMPTS)} prompts produced a distinct top-3")
    if distinct == 1:
        print("   ^ BROKEN: the query is not influencing the ranking at all")
    elif distinct < len(PROMPTS):
        print("   ^ weak: some prompts are indistinguishable")
    else:
        print("   ^ healthy: each prompt retrieves something different")


if __name__ == "__main__":
    main()
