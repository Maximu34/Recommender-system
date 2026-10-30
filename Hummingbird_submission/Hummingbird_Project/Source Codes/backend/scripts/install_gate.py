"""Week-1 install gate. Run this before writing any more code.

Each check below is cheap now and a demo-week disaster if it is discovered
late. In particular it verifies the two things a naive smoke test misses:

* iTunes previews are **AAC in an m4a container**, which libsndfile cannot
  read and there is no system ffmpeg here -- so decoding must go through PyAV.
* the hum upload path decodes at all, which is what breaks when the phone
  records AAC instead of WAV.

Usage:
    python -m scripts.install_gate
"""

from __future__ import annotations

import json
import socket
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
results: list[tuple[str, str, str]] = []


def check(name: str):
    def wrap(fn):
        try:
            detail = fn()
            results.append((PASS, name, detail or ""))
        except Exception as exc:
            results.append((FAIL, name, f"{type(exc).__name__}: {exc}"))
        return fn
    return wrap


@check("imports: torch / transformers / librosa / soundfile / av / fastapi")
def _imports():
    import av, fastapi, librosa, soundfile, torch, transformers  # noqa: F401
    return (f"torch {torch.__version__}, transformers {transformers.__version__}, "
            f"librosa {librosa.__version__}, av {av.__version__}")


@check("decode an iTunes preview (AAC/m4a, no system ffmpeg)")
def _decode_preview():
    from app import audio as audio_io, config

    url = "https://itunes.apple.com/search?" + urllib.parse.urlencode(
        {"term": "Billie Jean Michael Jackson", "media": "music",
         "entity": "song", "limit": 1})
    with urllib.request.urlopen(url, timeout=25) as r:
        hit = json.load(r)["results"][0]

    with urllib.request.urlopen(hit["previewUrl"], timeout=40) as r:
        data = r.read()

    with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp:
        tmp.write(data)
        path = tmp.name
    try:
        info = audio_io.probe(path)
        y = audio_io.load_audio(path, config.CLAP_SR)
        globals()["_SAMPLE_AUDIO"] = y
        return (f"{info['codec']} in {info['format']}, "
                f"{len(y)/config.CLAP_SR:.1f}s decoded at {config.CLAP_SR} Hz")
    finally:
        Path(path).unlink(missing_ok=True)


@check("CLAP loads and embeds audio + text into one space")
def _clap():
    import numpy as np

    from app import config, embed

    y = globals().get("_SAMPLE_AUDIO")
    if y is None:
        import numpy as np
        t = np.linspace(0, 5, 5 * config.CLAP_SR, endpoint=False)
        y = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

    a = embed.embed_audio([y[: 10 * config.CLAP_SR]])
    t_vec = embed.embed_text(["a calm acoustic guitar melody"])
    if a.shape[1] != t_vec.shape[1]:
        raise AssertionError("audio and text embeddings have different widths")
    norm = float(np.linalg.norm(a[0]))
    if abs(norm - 1.0) > 1e-3:
        raise AssertionError(f"embedding not unit-norm (got {norm:.4f})")
    return f"audio {a.shape}, text {t_vec.shape}, unit-norm ok"


@check("hum path: WAV/PCM upload decodes")
def _hum_decode():
    import numpy as np
    import soundfile as sf

    from app import audio as audio_io, config

    # A 3-second glide, which is roughly what a hum looks like to pYIN.
    sr = config.MELODY_SR
    t = np.linspace(0, 3, 3 * sr, endpoint=False)
    f = np.linspace(220, 330, len(t))
    y = (0.5 * np.sin(2 * np.pi * np.cumsum(f) / sr)).astype(np.float32)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        path = tmp.name
    try:
        sf.write(path, y, sr, subtype="PCM_16")
        back = audio_io.load_audio(path, sr)
        globals()["_HUM_AUDIO"] = back
        return f"wrote + decoded {len(back)/sr:.1f}s PCM wav"
    finally:
        Path(path).unlink(missing_ok=True)


@check("pYIN extracts a pitch contour")
def _pyin():
    from app import config, melody

    y = globals().get("_HUM_AUDIO")
    if y is None:
        raise AssertionError("hum decode check did not run")
    contour, voiced = melody.extract_contour(y, config.MELODY_SR)
    if len(contour) < 4:
        raise AssertionError(f"contour too short ({len(contour)} points)")
    return f"{len(contour)} points, voiced_ratio={voiced:.2f}"


@check("subsequence DTW finds a melody inside a longer clip")
def _dtw():
    import numpy as np

    from app import melody

    rng = np.random.default_rng(0)
    reference = rng.normal(0, 3, 300).astype(np.float32)
    query = reference[120:180].copy()          # a real excerpt
    decoy = rng.normal(0, 3, 300).astype(np.float32)

    good = melody.subsequence_dtw(query, reference)
    bad = melody.subsequence_dtw(query, decoy)
    if not good < bad:
        raise AssertionError(f"excerpt cost {good:.3f} not below decoy {bad:.3f}")
    return f"matching clip {good:.3f} < unrelated clip {bad:.3f}"


@check("LAN address for the phone to reach this backend")
def _lan():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))   # no packets sent; just picks the route
        ip = s.getsockname()[0]
    finally:
        s.close()
    return f"set API_BASE to http://{ip}:8000 in the Expo app"


def main() -> None:
    print("\n=== install gate ===\n")
    width = max(len(n) for _, n, _ in results)
    failed = 0
    for status, name, detail in results:
        mark = {PASS: "[ok]  ", FAIL: "[FAIL]", WARN: "[warn]"}[status]
        print(f"{mark} {name:<{width}}  {detail}")
        failed += status == FAIL
    print()
    if failed:
        print(f"{failed} check(s) failed -- fix these before building further.")
        sys.exit(1)
    print("all checks passed.")


if __name__ == "__main__":
    main()
