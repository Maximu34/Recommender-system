# Hummingbird

**A Cold-Start Content-Based Music Recommendation System Using Joint Audio-Language Embeddings and Query-by-Humming**

> [!WARNING]
> **All Rights Reserved — not open source.** This repository is published for academic evaluation only. No permission is granted to use, copy, modify or redistribute any part of it.

### Authors

**Rajaa Sasidharan**<br>
23MIA1174

**B. L. Jainth Vaishnav**<br>
23MIA1022

### Project Mentor

**Dr S Vigneshwari**<br>
(54147)

| | |
|---|---|
| **Course** | CSE4077 – Recommender Systems |
| **Component** | Project Based Component, Slot A1+TA1 |
| **Programme** | M.Tech Integrated CSE (Business Analytics) |
| **School** | School of Computer Science and Engineering |
| **Institution** | Vellore Institute of Technology, Chennai |
| **Date** | October 2026 |

## About

Hummingbird recommends songs that sound like a song you already have. A query may be a song title, a remembered lyric, a free-text description of a mood, or a hummed melody.

Because the system analyses audio rather than listening history, it has no cold-start exclusion. A recording is recommendable as soon as its audio has been analysed. A recording missing from the catalogue is fetched, analysed in the background and made searchable within seconds.

## Key Details

| Item | Description |
|---|---|
| **Catalogue** | 1,404 recordings, 1,403 with audio, 1,346 hummable |
| **Engine** | CLAP joint audio-language embedding (512-d) |
| **Baseline** | MFCC + chroma + spectral contrast + tempo (87-d, z-scored) |
| **Humming** | pYIN pitch contour + vectorised subsequence DTW |

## Results

| Method | Precision@5 |
|---|---|
| **Hummingbird (CLAP)** | **0.337** |
| Baseline (MFCC etc.) | 0.276 |
| Random control | 0.132 |

CLAP gives a **2.55x lift** over the random control.

## How to Run

See `others/RUN.md`. Use two terminals:

| Terminal | Service | Port |
|---|---|---|
| 1 | FastAPI backend | 8000 |
| 2 | Vite web client | 5173 |

## Directory

| Folder / File | Contents |
|---|---|
| `Source Codes/` | Backend (API, models, scripts), web, mobile |
| `Figures/` | All figures appearing in the report |
| `Tables/` | Evaluation results as csv and json |
| `others/` | README, RUN, DEPLOY, requirements, report, paper, slides |
| `DemoLink.txt` | Link to the demonstration video |
