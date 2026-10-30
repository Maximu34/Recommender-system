# Hummingbird

*Hum it, or name it, and find what sounds like it.*

Give it a song — by **typing the title** or by **humming the tune** — and it
returns songs that *sound like* it: similar feel, texture, mood and
instrumentation.

This is a **content-based audio similarity** recommender. It analyses the
audio itself rather than using collaborative filtering ("people who liked X
also liked Y"), which is the only approach that works with no user base — a
cold-start system by design.

---

## How it works

```
Expo app (phone)                 FastAPI backend            Apple CDN
  type a title ───────────────►  /search    metadata only
  tap a song ─────────────────►  /similar   CLAP embedding
  describe a mood ────────────►  /similar-by-text
  hum into the mic ───────────►  /hum       pYIN + subsequence DTW
  play a result ──────────────────────────────────────────► preview_url
```

The backend serves **JSON only**. Audio streams straight from Apple's CDN using
the `preview_url` the API returns, so there is no object storage to host, no
audio bandwidth, and no re-distribution of Apple's clips. `/audio/{id}` still
exists for local development and for tracks with no preview URL.

Metadata lives behind a storage backend chosen by `DB_BACKEND`: **SQLite** by
default (no network, no credentials, so the measured results below stay
reproducible from a fresh clone) or **Postgres/Supabase** for a deployed
instance. Embeddings are deliberately not in either: they load from `.npy` into
memory, where cosine search is one matmul and sub-millisecond at this scale.
A database round-trip per query would be slower for no benefit until roughly
100k tracks.

Two engines, evaluated against each other:

| Engine | What it is |
|---|---|
| **CLAP** (`laion/clap-htsat-unfused`) | A learned 512-d embedding that puts audio *and* text in one shared space — which is why mood search comes almost free. The music-specialised `larger_clap_music` checkpoint was tried first and rejected; see below. |
| **Baseline** | Classic hand-crafted MIR features: MFCC, chroma, spectral contrast, tempo. The comparison arm for the report. |

---

## Setup

### 1. Backend

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
```

Installing torch from the CPU index first avoids pulling a multi-gigabyte
CUDA build that this project never uses.

### 2. Run the install gate — do this before anything else

```bash
cd backend && ../.venv/Scripts/python.exe -m scripts.install_gate
```

It verifies the things that are cheap to check now and painful to discover in
demo week: that the ML stack imports on Python 3.13, that an **AAC/m4a**
preview actually decodes (libsndfile cannot read AAC and there is no system
ffmpeg — PyAV is what makes this work), that a hum recording decodes, that
CLAP embeds, and that subsequence DTW prefers a real excerpt over a decoy. It
also prints the LAN address to point the phone at.

### 3. Build the catalog

```bash
cd backend
../.venv/Scripts/python.exe -m scripts.build_catalog --target 2000
../.venv/Scripts/python.exe -m scripts.fetch_previews
../.venv/Scripts/python.exe -m scripts.build_index --limit 100   # start small
../.venv/Scripts/python.exe -m scripts.build_index               # then everything
```

Every step is resumable — interrupt and re-run freely.

### 4. Serve

```bash
cd backend && ../.venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`--host 0.0.0.0` matters: the phone connects over the LAN, so binding to
localhost only would leave the app unable to reach it.

### 5. Mobile app

```bash
cd mobile && npm install && npx expo start
```

Set `API_BASE` to the address the install gate printed, then scan the QR code
with Expo Go.

---

## The catalog

Built from **ListenBrainz** popular recordings (keyless API) plus
`data/curated_songs.txt`, with each title resolved through the keyless
**iTunes Search API** for a 30s preview and a genre label.

The curated list is not filler. Humming only works on songs you already know,
so the songs you and your classmates can sing from memory are exactly the
songs that need to be in the catalog — that is what makes the humming
evaluation valid rather than circular. It also corrects the sampling bias in
ListenBrainz popularity, which reflects that site's own userbase.

Preview clips are cached locally for offline feature extraction and are never
redistributed.

---

## Results (529-track catalog)

Genre-agreement precision@5, every track used as a seed, against both the raw
iTunes labels ("fine") and coarse families:

| Engine | P@5 fine | lift | P@5 coarse | lift |
|---|---|---|---|---|
| **CLAP** `clap-htsat-unfused` | **0.332** | **2.16x** | **0.498** | **1.97x** |
| Baseline (MFCC/chroma, z-scored) | 0.310 | 2.02x | 0.467 | 1.85x |
| Random control | 0.154 | 1.00x | 0.252 | 1.00x |

These replace an earlier run whose ground truth was partly wrong: 9.4% of
catalog entries were the wrong recording, so their genre labels belonged to a
different song (see below). Cleaning that raised absolute precision for both
engines -- CLAP 0.295 to 0.332, baseline 0.256 to 0.310 -- but the random
control rose too, from 0.122 to 0.154, because removing mis-resolved oddities
left a less genre-diverse catalog. **The lift therefore fell slightly even as
the numbers improved**, which is worth stating plainly rather than quoting
whichever figure flatters the system.

The more interesting change is that **the gap between the two engines nearly
closed**: CLAP led the baseline by 15% on the dirty catalog and by 7% on the
clean one. Some of the learned embedding's apparent advantage was an artifact
of noisy labels. A 2019-era audio embedding modestly outperforming
hand-crafted MFCC and chroma features is a more defensible claim than the
earlier numbers suggested.

**Query by humming:** an upper bound measured with synthesized "perfect hums"
(see `eval_humming.py`), 8/25 top-10 against a 479-track melody index at 0.93s
median latency. Modest, and the weakest part of the system.

**Search:** 529 tracks, 501 with lyrics. Findable by title, artist, or a
remembered line -- "caught in a landslide" returns Bohemian Rhapsody and shows
the line that matched.

### The checkpoint was the bug

The first CLAP index returned Billie Jean as the nearest neighbour of Take
Five at 0.992, and every pair scored ~0.99. Four bugs were found by
measurement, and the last one dominated:

1. **Baseline features were never standardized.** MFCCs run to the hundreds
   while chroma sits in [0, 1], so cosine was decided by one column.
   P@5 0.138 -> 0.245.
2. **CLAP was fed `is_longer=True`**, routing audio through a feature-fusion
   branch this checkpoint (`enable_fusion=False`) never trained. Mean pairwise
   cosine 0.92 -> 0.73 when disabled.
3. **`truncation="rand_trunc"`** meant a *random* 10s crop, so embedding the
   same track twice gave different vectors. Replaced with deterministic
   mean-pooled windows.
4. **`laion/larger_clap_music` is degenerate on this task.** 94% of every
   embedding was one shared direction; it scored *exactly at chance* on coarse
   genre agreement, and all four text prompts returned an identical ranking.
   Swapping to `laion/clap-htsat-unfused` -- one controlled change, same
   clips, same code -- moved P@5 from 0.172 to 0.315 and text discrimination
   from 1/4 to 4/4 distinct rankings.

The lesson worth writing up: high cosine similarity numbers hid a space that
was not separating anything. `diagnose_embeddings.py` exists to catch that.

A useful negative result: on the working checkpoint, anisotropy is still 0.853,
but correcting it makes things *worse*, not better.

| variant | P@5 fine | P@5 coarse |
|---|---|---|
| as-is | **0.315** | **0.476** |
| mean-centered | 0.299 | 0.468 |
| centered, top-1 PC removed | 0.290 | 0.420 |
| centered, top-2 PCs removed | 0.251 | 0.355 |

So the shared direction carries signal here. Anisotropy is worth *measuring*
as a symptom -- it is what exposed the bad checkpoint -- but it is not a
defect to correct on reflex. Embeddings are used as the model produces them.

### What it retrieves now

```
Take Five (Jazz)            -> Fly Me to the Moon (Jazz), Superstition, Under the Bridge
Smells Like Teen Spirit     -> Everlong, Back In Black, Mr. Brightside
Bohemian Rhapsody           -> Someone Like You, Let It Be, Perfect   (piano ballads)

"jazz saxophone and piano"  -> Take Five
"heavy distorted guitar"    -> Back In Black, Seven Nation Army, Everlong
"sad slow piano ballad"     -> Hallelujah, Bohemian Rhapsody, Let It Be
```

Caveat worth stating plainly: 71 tracks across 16 genres is too small for
these numbers to be conclusive. Scaling the catalog is the next step.

## Evaluation

```bash
cd backend && ../.venv/Scripts/python.exe -m scripts.evaluate
../.venv/Scripts/python.exe -m scripts.diagnose_embeddings   # is the space degenerate?
../.venv/Scripts/python.exe -m scripts.eval_humming --n 20   # needs the server running
```

Reports **genre-agreement precision@k** for CLAP, the baseline, and a
**random control**. The control is the column that matters: in a catalog that
is 40% Pop, a random recommender scores ~0.40 by accident, so precision alone
proves nothing.

Genre is a proxy — two very different-sounding Rock tracks both count as a
hit — which is why the plan pairs it with a small human study (20 seeds ×
top-5, rated 1–5). Humming is scored separately by Top-10 recall and MRR over
hums recorded by people who know the songs.

---

## Design decisions worth defending

- **Expo / React Native, not Flutter** — Node is installed here, Flutter and
  `adb` are not. Expo Go runs the app on a real phone over Wi-Fi with no
  Android Studio or USB debugging setup.
- **PyAV for all audio decoding** — iTunes previews are AAC; libsndfile
  cannot read AAC and ffmpeg is not installed. PyAV ships ffmpeg inside its
  wheel, so it decodes m4a, mp3 and wav with no system install. This also
  means the hum endpoint accepts whatever format the phone records.
- **Title search never touches CLAP** — typing a song title is a SQLite FTS5
  metadata lookup. Routing it through a text encoder would return
  semantically plausible *wrong* songs instead of the song that was asked for.
  Mood search is the separate `/similar-by-text` endpoint.
- **numpy brute force, not FAISS/Qdrant** — at a few thousand tracks, cosine
  search is one matrix multiply. An ANN index would add a dependency and a
  thing to defend, for no measurable gain.
- **Subsequence DTW, not plain DTW** — a 6-second hum matches a short stretch
  somewhere inside a 30-second clip, so the alignment must be free to start
  and end anywhere in the reference.
- **Results are top-20, not "all" matching songs** — similarity is continuous,
  so every song matches to some degree; a ranked cut-off is the correct output.

---

## Layout

```
backend/app/       config, store (SQLite+FTS5), audio (PyAV), embed (CLAP),
                   features (baseline+descriptors), melody (pYIN+DTW), main (API)
backend/scripts/   install_gate, build_catalog, fetch_previews, build_index, evaluate
mobile/            Expo app
data/              previews, catalog.db, .npy matrices  (gitignored)
report/            figures and results
```
