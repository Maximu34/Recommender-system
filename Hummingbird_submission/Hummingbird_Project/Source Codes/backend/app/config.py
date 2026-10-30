"""Shared paths and tunables.

Every script and module resolves its files through here so that the layout is
defined in exactly one place.
"""

import os
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """Minimal .env reader.

    Avoids a python-dotenv dependency for what is a handful of KEY=value lines.
    Real environment variables always win, so a deployed instance's settings are
    never overridden by a stray file in the image.
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

# backend/app/config.py -> backend/app -> backend -> project root
ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "data"
PREVIEWS = DATA / "previews"
DB_PATH = DATA / "catalog.db"

# Embedding matrices. Row i of each matrix corresponds to TRACK_IDS_PATH[i].
CLAP_MATRIX = DATA / "embeddings_clap.npy"
BASELINE_MATRIX = DATA / "embeddings_baseline.npy"
TRACK_IDS_PATH = DATA / "track_ids.json"

# Melody contours for query-by-humming: {track_id: [semitone, ...]}
MELODY_INDEX = DATA / "melody_index.json"

# Interpretable per-track descriptors (tempo/key/brightness/energy) used by the
# "why is this similar?" panel. Precomputed so the API never runs librosa.
DESCRIPTORS = DATA / "descriptors.json"

CURATED_LIST = DATA / "curated_songs.txt"

# Precomputed CLAP text embeddings for the mood presets, so a deployed
# instance can serve the mood tiles without shipping torch and a 586 MB
# checkpoint. See scripts/precompute_moods.py.
MOOD_VECTORS = DATA / "mood_vectors.json"

# --- storage -------------------------------------------------------------
_load_dotenv(ROOT / "backend" / ".env")

# "sqlite" (default) or "postgres". SQLite is deliberately the default: the
# evaluation scripts must run with no network and no credentials, so the
# measured results in the README stay reproducible from a fresh clone.
DB_BACKEND = os.environ.get("DB_BACKEND", "sqlite")

# Supabase connection string, e.g.
#   postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
# Set it in backend/.env (gitignored) or as a real environment variable.
# It must never be committed.
POSTGRES_URL = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")

# --- serving -------------------------------------------------------------
# Comma-separated origins, or "*". Only affects a web build -- a native app is
# not a browser and ignores CORS entirely (see the note in main.py).
ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if o.strip()
]

# --- Audio ---------------------------------------------------------------
CLAP_SR = 48_000  # CLAP expects 48 kHz
MELODY_SR = 16_000  # ample for pitch tracking, and much faster than 48 kHz

# --- Model ---------------------------------------------------------------
# laion/larger_clap_music was tried first and is degenerate on this task:
# 94% of every embedding is one shared direction, it scores at chance on
# coarse genre agreement, and all four text prompts return the same ranking.
# clap-htsat-unfused is the general checkpoint and behaves correctly.
# See scripts/diagnose_embeddings.py for the measurements.
CLAP_MODEL = "laion/clap-htsat-unfused"

# CLAP's audio tower takes a fixed-length window. Clips are split into
# windows of this many seconds and mean-pooled (see app/embed.py), which
# is deterministic -- unlike the extractor's default random 10s crop.
CLAP_WINDOW_S = 10

# --- Humming -------------------------------------------------------------
# Keep a track in the melody index only if pYIN finds a sustained pitch in at
# least this fraction of frames. Filters out beat-only and ambient tracks that
# humming could never match (see plan, R1).
MIN_VOICED_RATIO = 0.25
MELODY_HZ = 10  # contour resampled to this many points per second

# pYIN search range for *indexing*, in Hz. Roughly C2-C6: wide enough for the
# lead line of a full mix. Narrowing it here collapses the voiced ratio on
# polyphonic audio (measured: 0.24 -> 0.06), so it stays wide.
FMIN = 65.0
FMAX = 1047.0

# pYIN settings for a *hum query*. A hum is monophonic and sits in a much
# narrower band, so the search space can shrink: measured 6.4x faster per
# query (3.16s -> 0.49s) with identical top-1 accuracy. pYIN is ~96% of hum
# latency, so this is the difference between a snappy and a sluggish search.
HUM_FMIN = 80.0
HUM_FMAX = 600.0
HUM_RESOLUTION = 0.25


def ensure_dirs() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    PREVIEWS.mkdir(parents=True, exist_ok=True)
