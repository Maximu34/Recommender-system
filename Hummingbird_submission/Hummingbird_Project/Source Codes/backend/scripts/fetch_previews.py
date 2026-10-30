"""Download the 30s preview clip for every catalog track.

Resumable: already-downloaded clips are skipped, so this can be interrupted
and re-run freely. Clips are cached locally for offline feature extraction and
are never redistributed (see the licensing note in the plan).

Usage:
    python -m scripts.fetch_previews
    python -m scripts.fetch_previews --limit 200 --workers 6
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config, store  # noqa: E402

UA = {"User-Agent": "Hummingbird/0.1 (final-year project)"}


def download(track: store.Track) -> tuple[int, str | None, str | None]:
    """Return (track_id, local_path, error)."""
    dest = config.PREVIEWS / f"{track.id}.m4a"
    if dest.exists() and dest.stat().st_size > 10_000:
        return track.id, str(dest), None
    try:
        req = urllib.request.Request(track.preview_url, headers=UA)
        with urllib.request.urlopen(req, timeout=40) as r:
            data = r.read()
        if len(data) < 10_000:
            return track.id, None, f"suspiciously small ({len(data)} bytes)"
        tmp = dest.with_suffix(".part")
        tmp.write_bytes(data)
        tmp.replace(dest)          # atomic: a killed run never leaves a half file
        return track.id, str(dest), None
    except Exception as exc:
        return track.id, None, str(exc)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    config.ensure_dirs()
    conn = store.connect()
    store.init_schema(conn)

    pending = [
        t for t in store.all_tracks(conn)
        if t.preview_url and not (t.local_path and Path(t.local_path).exists())
    ]
    if args.limit:
        pending = pending[: args.limit]

    if not pending:
        print("nothing to download -- every track already has a cached clip")
        return

    print(f"downloading {len(pending)} previews with {args.workers} workers")
    ok = failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(download, t): t for t in pending}
        for i, fut in enumerate(as_completed(futures), 1):
            tid, path, err = fut.result()
            if path:
                store.set_local_path(conn, tid, path)
                ok += 1
            else:
                failed += 1
                if failed <= 5:
                    print(f"  failed {tid}: {err}")
            if i % 50 == 0:
                print(f"  {i}/{len(pending)}  ok={ok} failed={failed}")

    total_mb = sum(p.stat().st_size for p in config.PREVIEWS.glob("*.m4a")) / 1e6
    print(f"\ndone: {ok} downloaded, {failed} failed, cache is {total_mb:.0f} MB")
    conn.close()


if __name__ == "__main__":
    main()
