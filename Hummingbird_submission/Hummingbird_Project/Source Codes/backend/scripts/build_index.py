"""Build the search indices from cached preview clips.

Produces three artifacts:

* ``embeddings_clap.npy``     -- learned CLAP embeddings (the main engine)
* ``embeddings_baseline.npy`` -- hand-crafted MIR features (the comparison arm)
* ``melody_index.json``       -- pitch contours for query-by-humming

Resumable: every artifact is checkpointed, and a re-run skips tracks that are
already done. Embedding a few thousand clips on CPU takes a while, and losing
that to a crash would hurt.

Usage:
    python -m scripts.build_index --limit 100        # start small
    python -m scripts.build_index                    # everything
    python -m scripts.build_index --only melody
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import audio as audio_io, config, features, melody, store  # noqa: E402


def load_checkpoint(matrix_path: Path) -> dict[int, np.ndarray]:
    """Existing vectors keyed by track id, so a re-run can resume."""
    ids_path = matrix_path.with_name(matrix_path.stem + "_ids.json")
    if matrix_path.exists() and ids_path.exists():
        matrix = np.load(matrix_path)
        ids = json.loads(ids_path.read_text())
        if len(ids) == matrix.shape[0]:
            return {int(t): matrix[i] for i, t in enumerate(ids)}
    return {}


def save_checkpoint(matrix_path: Path, vectors: dict[int, np.ndarray]) -> None:
    ids = sorted(vectors)
    matrix = np.stack([vectors[i] for i in ids]).astype(np.float32)
    np.save(matrix_path, matrix)
    matrix_path.with_name(matrix_path.stem + "_ids.json").write_text(json.dumps(ids))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="0 = all tracks")
    ap.add_argument("--only", choices=["all", "clap", "baseline", "melody"],
                    default="all")
    ap.add_argument("--batch", type=int, default=8, help="CLAP batch size")
    ap.add_argument("--checkpoint-every", type=int, default=50)
    args = ap.parse_args()

    do_clap = args.only in ("all", "clap")
    do_base = args.only in ("all", "baseline")
    do_mel = args.only in ("all", "melody")

    config.ensure_dirs()
    conn = store.connect()
    store.init_schema(conn)

    tracks = [t for t in store.all_tracks(conn, with_audio=True)
              if t.local_path and Path(t.local_path).exists()]
    if args.limit:
        tracks = tracks[: args.limit]
    if not tracks:
        print("no cached clips found -- run build_catalog.py then fetch_previews.py")
        return

    clap_vecs = load_checkpoint(config.CLAP_MATRIX) if do_clap else {}
    base_vecs = load_checkpoint(config.BASELINE_MATRIX) if do_base else {}
    contours: dict[int, list[float]] = {}
    if do_mel and config.MELODY_INDEX.exists():
        contours = {int(k): v for k, v in
                    json.loads(config.MELODY_INDEX.read_text()).items()}

    descriptors: dict[int, dict] = {}
    if do_base and config.DESCRIPTORS.exists():
        descriptors = {int(k): v for k, v in
                       json.loads(config.DESCRIPTORS.read_text()).items()}

    todo = [t for t in tracks if
            (do_clap and t.id not in clap_vecs)
            or (do_base and t.id not in base_vecs)
            or (do_mel and t.id not in contours)]

    print(f"{len(tracks)} tracks with audio; {len(todo)} still need work")
    if not todo:
        print("everything already indexed")
        orphans = drop_orphans(conn, clap_vecs, base_vecs, contours,
                               descriptors)
        if orphans:
            print(f"dropped {orphans} indexed entries for tracks no longer "
                  f"in the catalog")
        _finalise(clap_vecs, base_vecs, contours, descriptors,
                  do_clap, do_base, do_mel)
        return

    started = time.time()
    pending_batch: list[tuple[int, np.ndarray]] = []
    skipped = 0

    for n, track in enumerate(todo, 1):
        try:
            y48 = audio_io.load_audio(track.local_path, config.CLAP_SR)
        except Exception as exc:
            skipped += 1
            print(f"  skip {track.id} ({track.title[:30]}): {exc}")
            continue

        if do_clap and track.id not in clap_vecs:
            pending_batch.append((track.id, y48))
            if len(pending_batch) >= args.batch:
                _flush_clap(pending_batch, clap_vecs)
                pending_batch.clear()

        need_base = do_base and track.id not in base_vecs
        need_mel = do_mel and track.id not in contours
        if need_base or need_mel:
            import librosa
            y16 = librosa.resample(y48, orig_sr=config.CLAP_SR,
                                   target_sr=config.MELODY_SR)

            if do_base and track.id not in base_vecs:
                try:
                    base_vecs[track.id] = features.baseline_features(
                        y16, config.MELODY_SR)
                    descriptors[track.id] = features.descriptors(
                        y16, config.MELODY_SR)
                except Exception as exc:
                    print(f"  baseline failed {track.id}: {exc}")

            if do_mel and track.id not in contours:
                try:
                    contour, voiced = melody.extract_contour(y16, config.MELODY_SR)
                    # Only keep tracks with a genuinely sustained melodic line.
                    if voiced >= config.MIN_VOICED_RATIO and len(contour) > 8:
                        contours[track.id] = [round(float(v), 3) for v in contour]
                except Exception as exc:
                    print(f"  melody failed {track.id}: {exc}")

        if n % args.checkpoint_every == 0:
            _flush_clap(pending_batch, clap_vecs)
            pending_batch.clear()
            _checkpoint(clap_vecs, base_vecs, contours, descriptors,
                    do_clap, do_base, do_mel)
            rate = n / (time.time() - started)
            eta = (len(todo) - n) / rate if rate else 0
            print(f"  {n}/{len(todo)}  {rate:.2f} tracks/s  eta {eta/60:.1f} min")

    _flush_clap(pending_batch, clap_vecs)
    _checkpoint(clap_vecs, base_vecs, contours, descriptors,
                    do_clap, do_base, do_mel)
    orphans = drop_orphans(conn, clap_vecs, base_vecs, contours, descriptors)
    if orphans:
        print(f"dropped {orphans} indexed entries for tracks no longer in the catalog")
    _finalise(clap_vecs, base_vecs, contours, descriptors,
              do_clap, do_base, do_mel)

    took = time.time() - started
    print(f"\ndone in {took/60:.1f} min ({skipped} clips unreadable)")
    if do_mel:
        kept = len(contours)
        print(f"melody index: {kept} of {len(tracks)} tracks passed the "
              f"voiced-ratio filter (>= {config.MIN_VOICED_RATIO})")


def drop_orphans(conn, *stores) -> int:
    """Remove indexed entries for tracks no longer in the catalog.

    build_catalog can delete rows -- a mis-resolved track the artist check now
    rejects -- but the .npy matrices and melody index keep their vectors. An
    orphan is not harmless: it can still be returned as a neighbour, where the
    API silently drops it (leaving short result lists) and evaluate.py counts
    it as a miss because it has no genre to agree with, quietly understating
    precision.
    """
    live = {t.id for t in store.all_tracks(conn)}
    removed = 0
    for mapping in stores:
        for track_id in [k for k in mapping if k not in live]:
            del mapping[track_id]
            removed += 1
    return removed


def _flush_clap(batch: list[tuple[int, np.ndarray]],
                clap_vecs: dict[int, np.ndarray]) -> None:
    if not batch:
        return
    from app import embed
    ids = [i for i, _ in batch]
    waves = [w for _, w in batch]
    try:
        vecs = embed.embed_audio(waves)
        for tid, vec in zip(ids, vecs):
            clap_vecs[tid] = vec
    except Exception as exc:
        print(f"  CLAP batch failed ({len(ids)} tracks): {exc}")


def _checkpoint(clap_vecs, base_vecs, contours, descriptors,
                do_clap, do_base, do_mel) -> None:
    if do_clap and clap_vecs:
        save_checkpoint(config.CLAP_MATRIX, clap_vecs)
    if do_base and base_vecs:
        save_checkpoint(config.BASELINE_MATRIX, base_vecs)
    if do_base and descriptors:
        config.DESCRIPTORS.write_text(json.dumps(descriptors))
    if do_mel and contours:
        config.MELODY_INDEX.write_text(json.dumps(contours))


def _finalise(clap_vecs, base_vecs, contours, descriptors,
              do_clap, do_base, do_mel) -> None:
    """Write the shared track-id ordering used by the API."""
    _checkpoint(clap_vecs, base_vecs, contours, descriptors,
                do_clap, do_base, do_mel)
    reference = clap_vecs if do_clap and clap_vecs else base_vecs
    if reference:
        config.TRACK_IDS_PATH.write_text(json.dumps(sorted(reference)))
    print(f"\nclap={len(clap_vecs)}  baseline={len(base_vecs)}  melody={len(contours)}")


if __name__ == "__main__":
    main()
