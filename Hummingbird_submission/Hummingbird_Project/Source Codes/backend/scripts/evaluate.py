"""Quantitative evaluation: does the recommender actually work?

Primary metric is **genre-agreement precision@k** -- of the k nearest
neighbours returned for a seed track, what fraction share the seed's genre
label (from iTunes ``primaryGenreName``).

The **random control** is the important column. Precision@k means nothing on
its own: a catalog that is 40% Pop gives a random recommender ~0.40 by
accident. The control is what shows the system learned something.

"Sounds similar" has no perfect ground truth, and genre is only a proxy --
two very different-sounding Rock tracks both count as a hit. That is why the
plan pairs this with a small human study; this script measures the half that
can be automated.

Usage:
    python -m scripts.evaluate
    python -m scripts.evaluate --sample 500 --k 5 10 20
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config, store  # noqa: E402


# iTunes labels are fine-grained: Rock, Hard Rock and Alternative are three
# separate genres, so a musically sensible neighbour often scores as a miss.
# Results are reported against both the raw labels and these coarse families,
# because neither alone is the honest number -- fine labels under-credit a
# good recommender, coarse ones over-credit a mediocre one.
GENRE_FAMILIES = {
    "rock": ["rock", "hard rock", "alternative", "metal", "punk", "grunge",
             "classic rock", "adult alternative"],
    "pop": ["pop", "dance", "electronic", "house", "techno", "disco",
            "singer/songwriter", "soundtrack"],
    "hiphop": ["hip-hop/rap", "hip hop", "rap"],
    "soul": ["r&b/soul", "soul", "funk", "blues", "reggae", "roots reggae"],
    "jazz": ["jazz", "vocal jazz", "big band", "easy listening"],
    "country": ["country", "traditional country", "folk", "americana",
                "contemporary folk"],
    "classical": ["classical", "opera", "orchestral"],
}

_LOOKUP = {name: fam for fam, names in GENRE_FAMILIES.items() for name in names}


def coarse(genre: str | None) -> str | None:
    """Map a fine iTunes genre onto a broad family, or keep it if unknown."""
    if not genre:
        return None
    return _LOOKUP.get(genre.strip().lower(), genre.strip().lower())


def load_index(matrix_path: Path, standardize: bool = False):
    ids_path = matrix_path.with_name(matrix_path.stem + "_ids.json")
    if not (matrix_path.exists() and ids_path.exists()):
        return None
    return store.VectorIndex.load(matrix_path, ids_path, standardize=standardize)


def precision_at_k(index, genres: dict[int, str], ks: list[int],
                   sample: int, rng: np.random.Generator) -> dict[int, float]:
    """Mean fraction of the top-k that share the seed's genre."""
    ids = [t for t in index.track_ids if genres.get(t)]
    if not ids:
        return {k: float("nan") for k in ks}
    if sample and len(ids) > sample:
        ids = list(rng.choice(ids, size=sample, replace=False))

    rows = np.stack([index.vector_for(t) for t in ids])
    sims = rows @ index.matrix.T            # (sample, N)

    # Remove each seed's own column so it can't be its own neighbour.
    pos = {t: i for i, t in enumerate(index.track_ids)}
    for r, t in enumerate(ids):
        sims[r, pos[t]] = -np.inf

    max_k = max(ks)
    top = np.argpartition(-sims, max_k, axis=1)[:, :max_k]
    ordered = np.take_along_axis(top, np.argsort(-np.take_along_axis(sims, top, 1)), 1)

    out = {}
    for k in ks:
        hits = []
        for r, seed in enumerate(ids):
            seed_genre = genres[seed]
            neigh = [index.track_ids[j] for j in ordered[r, :k]]
            hits.append(np.mean([genres.get(n) == seed_genre for n in neigh]))
        out[k] = float(np.mean(hits))
    return out


def random_control(all_ids: list[int], genres: dict[int, str], ks: list[int],
                   sample: int, rng: np.random.Generator) -> dict[int, float]:
    ids = [t for t in all_ids if genres.get(t)]
    if sample and len(ids) > sample:
        seeds = list(rng.choice(ids, size=sample, replace=False))
    else:
        seeds = ids
    out = {}
    for k in ks:
        hits = []
        for seed in seeds:
            picks = rng.choice(ids, size=min(k, len(ids)), replace=False)
            hits.append(np.mean([genres.get(int(p)) == genres[seed] for p in picks]))
        out[k] = float(np.mean(hits))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, nargs="+", default=[5, 10, 20])
    ap.add_argument("--sample", type=int, default=500,
                    help="seeds to evaluate (0 = every track)")
    ap.add_argument("--seed", type=int, default=0, help="RNG seed")
    args = ap.parse_args()

    conn = store.connect()
    store.init_schema(conn)
    genres = {t.id: t.genre for t in store.all_tracks(conn) if t.genre}
    conn.close()

    if not genres:
        print("no catalog yet -- run build_catalog.py first")
        return

    clap = load_index(config.CLAP_MATRIX)
    base = load_index(config.BASELINE_MATRIX, standardize=True)
    if clap is None and base is None:
        print("no indices built -- run build_index.py first")
        return

    rng = np.random.default_rng(args.seed)
    results: dict[str, dict] = {}

    if clap is not None:
        results["CLAP (learned)"] = precision_at_k(
            clap, genres, args.k, args.sample, rng)
    if base is not None:
        results["Baseline (MFCC/chroma)"] = precision_at_k(
            base, genres, args.k, args.sample, rng)

    pool = (clap or base).track_ids
    results["Random control"] = random_control(
        pool, genres, args.k, args.sample, rng)

    coarse_genres = {k: coarse(v) for k, v in genres.items()}
    coarse_results: dict[str, dict] = {}
    if clap is not None:
        coarse_results["CLAP (learned)"] = precision_at_k(
            clap, coarse_genres, args.k, args.sample, np.random.default_rng(args.seed))
    if base is not None:
        coarse_results["Baseline (MFCC/chroma)"] = precision_at_k(
            base, coarse_genres, args.k, args.sample, np.random.default_rng(args.seed))
    coarse_results["Random control"] = random_control(
        pool, coarse_genres, args.k, args.sample, np.random.default_rng(args.seed))

    n_genres = len(set(genres.values()))
    print(f"\ncatalog: {len(genres)} labelled tracks, {n_genres} distinct genres")
    print(f"seeds evaluated: {min(args.sample, len(genres)) if args.sample else len(genres)}\n")

    header = f"{'engine':26s}" + "".join(f"  P@{k:<6d}" for k in args.k)
    print(header)
    print("-" * len(header))
    for name, scores in results.items():
        row = f"{name:26s}" + "".join(f"  {scores[k]:<8.3f}" for k in args.k)
        print(row)

    ctrl = results["Random control"]
    print("\nlift over random:")
    for name, scores in results.items():
        if name == "Random control":
            continue
        lifts = ", ".join(
            f"P@{k} x{scores[k]/ctrl[k]:.2f}" if ctrl[k] else f"P@{k} n/a"
            for k in args.k
        )
        print(f"  {name:26s} {lifts}")

    print("")
    print(f"coarse genre families ({len(set(coarse_genres.values()))} groups)")
    print(header)
    print("-" * len(header))
    for name, scores in coarse_results.items():
        print(f"{name:26s}" + "".join(f"  {scores[k]:<8.3f}" for k in args.k))
    cctrl = coarse_results["Random control"]
    print("")
    print("lift over random (coarse):")
    for name, scores in coarse_results.items():
        if name == "Random control":
            continue
        print(f"  {name:26s} " + ", ".join(
            f"P@{k} x{scores[k]/cctrl[k]:.2f}" if cctrl[k] else f"P@{k} n/a"
            for k in args.k))

    out_path = config.ROOT / "report" / "evaluation.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(
        {"k": args.k, "sample": args.sample, "results": results,
         "coarse_results": coarse_results}, indent=2))
    print(f"\nwritten to {out_path}")


if __name__ == "__main__":
    main()
