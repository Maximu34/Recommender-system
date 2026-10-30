"""Day-1 experiment for risk R1: does the cached 30s window contain the hook?

iTunes previews are a fixed ~30s window whose start offset is undocumented.
If the indexed window misses the part of the song people actually hum, the
humming feature fails at close to 0% recall *silently* -- the code works, the
answers are just always wrong. Measure it before building on it.

This script does the measurable half automatically (how much sustained,
hummable melody pYIN can find in each clip) and prepares a listening sheet for
the half only a human can judge (is this the bit I would hum?).

Usage:
    python -m scripts.hook_check --n 10
    # then open report/hook_check.csv, play each clip, fill in hook_present
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import audio as audio_io, config, melody, store  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10, help="clips to examine")
    ap.add_argument("--curated-only", action="store_true", default=True,
                    help="only songs from the curated list (you must know them)")
    args = ap.parse_args()

    conn = store.connect()
    store.init_schema(conn)
    tracks = [t for t in store.all_tracks(conn, with_audio=True)
              if t.local_path and Path(t.local_path).exists()]
    conn.close()

    if args.curated_only:
        curated = [t for t in tracks if t.source == "curated"]
        if curated:
            tracks = curated

    if not tracks:
        print("no cached clips -- run build_catalog.py and fetch_previews.py first")
        return

    tracks = tracks[: args.n]
    out_path = config.ROOT / "report" / "hook_check.csv"
    out_path.parent.mkdir(exist_ok=True)

    print(f"examining {len(tracks)} clips\n")
    rows = []
    for t in tracks:
        try:
            y = audio_io.load_audio(t.local_path, config.MELODY_SR)
            contour, voiced = melody.extract_contour(y, config.MELODY_SR)
            pitch_range = float(np.ptp(contour)) if len(contour) else 0.0
            passes = voiced >= config.MIN_VOICED_RATIO and len(contour) > 8
        except Exception as exc:
            print(f"  {t.title[:34]:36s} FAILED: {exc}")
            continue

        rows.append({
            "track_id": t.id,
            "title": t.title,
            "artist": t.artist,
            "voiced_ratio": round(voiced, 3),
            "pitch_range_semitones": round(pitch_range, 1),
            "in_melody_index": passes,
            "clip_path": t.local_path,
            "hook_present": "",     # <- you fill this in: yes / no
        })
        flag = "keep" if passes else "DROP"
        print(f"  {t.title[:34]:36s} voiced={voiced:.2f} "
              f"range={pitch_range:4.1f}st  [{flag}]")

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    kept = sum(r["in_melody_index"] for r in rows)
    print(f"\n{kept}/{len(rows)} clips pass the voiced-ratio filter "
          f"(>= {config.MIN_VOICED_RATIO})")
    print(f"listening sheet: {out_path}")
    print("\nNow play each clip and fill in 'hook_present' (yes/no).")
    print("If most clips say no, the 30s window is missing the hook: either")
    print("tighten the melody index to clips that pass, or source full-length")
    print("audio for the humming subset (plan, R1).")


if __name__ == "__main__":
    main()
