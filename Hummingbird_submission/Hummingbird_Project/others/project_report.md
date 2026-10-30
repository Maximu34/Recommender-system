# HUMMINGBIRD: A COLD-START CONTENT-BASED MUSIC RECOMMENDATION SYSTEM USING JOINT AUDIO–LANGUAGE EMBEDDINGS AND QUERY-BY-HUMMING

## PROJECT REPORT

### MTech Integrated CSE (Business Analytics)

### Submitted for Project Based Component

### CSE4077 — Recommender Systems

**By**

**Rajaa Sasidharan — 23MIA1174**

**B. L. Jainth Vaishnav — 23MIA1022**

Slot: A1+TA1

**Faculty Name: Dr S Vigneshwari (54147)**

### School of Computer Science and Engineering

### October-2026

---

## TABLE OF CONTENTS

| S. No. | Title | Page |
|---|---|---|
| | Abstract | iii |
| | List of Figures | iv |
| | List of Tables | v |
| | List of Symbols and Abbreviations | vi |
| **1** | **Introduction** | 1 |
| 1.1 | Motivation | 1 |
| 1.2 | Need and Importance of Recommender Systems | 2 |
| 1.3 | Innovative Content in the Project | 3 |
| 1.4 | Block Schematic | 4 |
| 1.4.1 | Module Description | 5 |
| 1.4.2 | Cost of the Project | 7 |
| 1.4.3 | Advantages and Disadvantages | 8 |
| **2** | **Literature Survey** | 10 |
| 2.1 | Study of Various Approaches in Recommender Systems | 10 |
| 2.2 | Existing Approaches and Frameworks | 12 |
| 2.3 | Research Gap | 16 |
| **3** | **Methodology** | 18 |
| 3.1 | Design of the Project | 18 |
| 3.1.1 | Data / Input Description | 18 |
| 3.1.2 | Model / Framework Description | 21 |
| 3.1.3 | Algorithms / Mathematical Models | 24 |
| 3.1.4 | Evaluation Metrics | 28 |
| **4** | **Results and Discussion** | 30 |
| 4.1 | Results | 30 |
| 4.2 | Discussion | 32 |
| 4.3 | Screenshots / Output / Figures / Tables | 35 |
| 4.4 | Ablation Study | 37 |
| 4.5 | Comparison with Existing Approaches | 39 |
| | Conclusion and Future Scope | 41 |
| | References | 43 |
| | Acknowledgement | 48 |
| | Appendix 1 — Directory Structure | 49 |
| | Appendix 2 — Project Presentation | 50 |
| | Appendix 3 — Research Paper and Reports | 50 |

---

## ABSTRACT

**Background.** Music recommendation at commercial scale is dominated by
collaborative filtering, which infers preference from the listening behaviour
of large user populations. Two situations defeat this approach and both occur
constantly. A newly released or sparsely played recording carries no
interaction history and therefore cannot be recommended at all, which is the
cold-start problem; and a listener who remembers only how a song *sounds* — a
fragment of its melody, or an impression of its texture and mood — holds
information that is acoustic rather than lexical and cannot express it to a
keyword search. A system that analyses the audio signal itself is the only
approach that addresses both, since it depends on no user base whatsoever.

**Methods.** A content-based recommendation system named Hummingbird was
designed and implemented. Four query modalities are unified behind a single
application programming interface. A 512-dimensional joint audio–language
embedding produced by the Contrastive Language–Audio Pretraining (CLAP) model
is used to retrieve acoustically similar recordings by cosine similarity;
because audio and text occupy one shared space, free-text mood queries are
served by the same index with no additional model. A hummed or sung query is
converted to a key-invariant semitone contour by probabilistic YIN pitch
tracking and matched by subsequence dynamic time warping, vectorised so that
every catalogue melody is scored in a single pass. Typed titles and remembered
lyric fragments are resolved by a weighted full-text index with a live metadata
fallback and on-demand background embedding. A hand-crafted feature baseline
comprising Mel-frequency cepstral coefficients, chroma, spectral contrast and
tempo was implemented as a controlled comparison arm. A catalogue of 1,404
recordings was assembled from the ListenBrainz popularity feed and a curated
list, each title verified against the iTunes Search API.

**Results.** Evaluated by genre-agreement precision@k with every recording used
in turn as a seed, the learned embedding attained a precision@5 of 0.337
against 0.276 for the hand-crafted baseline and 0.132 for a matched random
control, a lift of 2.55 times over chance. On coarse genre families the
corresponding figures were 0.537, 0.462 and 0.265. Query-by-humming reached 8
of 25 in the top 10 at 0.93 s median latency, a figure reported as an upper
bound because it was measured on synthesised rather than human queries.

**Discussion.** Two findings beyond the headline comparison are reported. A
publicly released music-specialised CLAP checkpoint was diagnosed as degenerate
on this task, placing 94% of every embedding's energy along one shared
direction, scoring exactly at chance on coarse genre agreement and returning an
identical ranking for four distinct text prompts; a single controlled
checkpoint substitution raised precision@5 from 0.172 to 0.315. Separately,
anisotropy correction — a standard remedy in the text-embedding literature —
was found to degrade retrieval monotonically, indicating that the dominant
shared direction carries task-relevant signal and that anisotropy is better
treated as a diagnostic symptom than as a defect. The margin between the two
engines was further shown to depend on experimental conditions, narrowing from
15% to 7% when metadata errors were corrected and widening to 22% as the
catalogue grew, the latter because the hand-crafted baseline deteriorated
rather than because the embedding improved.

**Future Direction.** The genre-agreement proxy should be replaced by a human
listening study; dedicated polyphonic melody extraction should replace
monophonic pitch tracking for the humming component; approximate
nearest-neighbour indexing becomes necessary beyond approximately 100,000
recordings; and contrastive fine-tuning on music-specific pairs is the
indicated route to a larger margin over the baseline.

**Keywords:** content-based music recommendation; cold-start problem;
contrastive language–audio pretraining; query by humming; subsequence dynamic
time warping; music information retrieval; embedding anisotropy

---

## LIST OF FIGURES

| Figure | Title | Page |
|---|---|---|
| 1.1 | Block schematic of the Hummingbird system | 4 |
| 1.2 | Module interaction overview | 6 |
| 3.1 | Catalogue composition by genre | 20 |
| 3.2 | CLAP audio embedding pipeline | 22 |
| 3.3 | Pitch contour extraction for an indexed clip and a hum | 25 |
| 3.4 | Subsequence DTW alignment within a longer reference | 26 |
| 4.1 | Genre-agreement precision@5 by engine | 31 |
| 4.2 | Effect of catalogue growth on the gap between engines | 33 |
| 4.3 | Web client — song search with similar recordings | 35 |
| 4.4 | Web client — free-text mood search | 35 |
| 4.5 | Web client — query-by-humming panel | 36 |
| 4.6 | Interactive API documentation | 36 |
| 4.7 | Anisotropy ablation — precision against correction strength | 38 |

---

## LIST OF TABLES

| Table | Title | Page |
|---|---|---|
| 1.1 | Advantages and disadvantages of the proposed system | 8 |
| 1.2 | Cost of the project, itemised | 7 |
| 2.1 | Families of recommender system approach | 11 |
| 2.2 | Existing frameworks, models and datasets surveyed | 13 |
| 2.3 | Metadata resolution failures before artist verification | 17 |
| 3.1 | Catalogue composition and coverage | 19 |
| 3.2 | Composition of the 87-dimensional baseline vector | 23 |
| 3.3 | Evaluation metrics and their interpretation | 28 |
| 4.1 | Genre-agreement precision@k on the full catalogue | 30 |
| 4.2 | Effect of catalogue correction and growth on the engine gap | 32 |
| 4.3 | Anisotropy correction ablation | 37 |
| 4.4 | Checkpoint comparison under a single controlled change | 38 |
| 4.5 | Comparison with existing approaches | 39 |

---

## LIST OF SYMBOLS AND ABBREVIATIONS

### Symbols

| Symbol | Meaning |
|---|---|
| *T* | The catalogue, a finite set of recordings |
| *N* | Number of recordings in the catalogue |
| *d* | Embedding dimension (512 for CLAP, 87 for the baseline) |
| *k* | Number of recommendations returned |
| *M* | The *N* × *d* matrix of L2-normalised embeddings |
| *t<sub>s</sub>* | A seed recording |
| *q* | A query, typed or free-text |
| *c* | A pitch contour, in median-subtracted semitones |
| *R* | The *N* × *W* padded matrix of reference contours |
| *ℓ* | Vector of true contour lengths |
| *n* | Number of frames in a query contour |
| *W* | Width of the padded contour matrix |
| *σ* | Global tempo scaling factor |
| *λ* | Diversity parameter in maximal marginal relevance |
| *D* | Running cost matrix in the DTW recurrence |

### Abbreviations

| Abbreviation | Expansion |
|---|---|
| AAC | Advanced Audio Coding |
| API | Application Programming Interface |
| BM25 | Best Match 25, a probabilistic ranking function |
| BPM | Beats Per Minute |
| CF | Collaborative Filtering |
| CLAP | Contrastive Language–Audio Pretraining |
| CLIP | Contrastive Language–Image Pretraining |
| CNN | Convolutional Neural Network |
| CQT | Constant-Q Transform |
| CORS | Cross-Origin Resource Sharing |
| DTW | Dynamic Time Warping |
| FTS | Full-Text Search |
| HTS-AT | Hierarchical Token-Semantic Audio Transformer |
| JSON | JavaScript Object Notation |
| LRCLIB | An open, keyless lyrics database |
| MFCC | Mel-Frequency Cepstral Coefficients |
| MIDI | Musical Instrument Digital Interface |
| MIR | Music Information Retrieval |
| MMR | Maximal Marginal Relevance |
| MRR | Mean Reciprocal Rank |
| MSD | Million Song Dataset |
| P@k | Precision at k |
| PCA | Principal Component Analysis |
| pYIN | Probabilistic YIN, a fundamental frequency estimator |
| RMS | Root Mean Square |
| SQL | Structured Query Language |
| YIN | A fundamental frequency estimator for speech and music |
| ZCR | Zero-Crossing Rate |

---

# CHAPTER 1 — INTRODUCTION

## 1.1 Motivation

The project began from a concrete and easily reproduced frustration: a listener
who wants "more songs that sound like this one" has no reliable way of asking
for them. Streaming services answer a closely related but different question —
"what do people who played this also play?" — and the two diverge sharply
whenever the recording in question is new, obscure, or simply not popular
enough to have accumulated co-listening data.

Two failure modes motivated the design, and both were verified to occur in
practice before any code was written.

The first is the **cold-start problem**. Collaborative filtering predicts
preference from patterns of co-consumption across a large user base. Its
accuracy where interaction data is abundant is well established, but a
recording that has just been released, or that belongs to the long tail of
sparsely played material, has no such data attached to it. A purely behavioural
model therefore has no basis on which to recommend it at all. The effect
compounds: recommendations are drawn from what is already popular, popularity
accrues to what is recommended, and the long tail becomes progressively less
discoverable.

The second is a **query-formulation problem**, and it is the one that gives the
project its name. Catalogue search assumes the listener can supply a title, an
artist or a lyric. Very often that assumption fails. A listener may retain only
a melodic fragment — a tune stuck in the head with no words attached — or only
a general impression of instrumentation, energy and mood. Neither is
expressible as a keyword, because both are acoustic rather than lexical. A
system that cannot accept a hummed query or a description such as "something
slow with a piano for a rainy evening" simply cannot serve that listener.

A content-based system that analyses the audio signal directly addresses both
failures at once, and does so without requiring a single user account. This is
not a workaround for having no users; it is a design position. The system is
cold-start by construction, and every recording becomes recommendable the
moment its audio has been analysed.

A third motivation was methodological, and emerged during implementation rather
than before it. An early version of the system returned plainly absurd results
— a Michael Jackson track as the nearest neighbour of a Dave Brubeck jazz
standard, at a cosine similarity of 0.992 — while every summary statistic
looked healthy. Diagnosing that failure, and discovering that the published
model checkpoint itself was at fault, shaped the project's insistence that an
embedding space must be verified before it is trusted. That insistence produced
two of the three findings reported in Chapter 4.

## 1.2 Need and Importance of Recommender Systems

Recommender systems have become the primary mechanism by which users encounter
items in catalogues too large to browse. In music the scale is extreme: major
streaming services hold tens of millions of recordings, of which any individual
listener will ever hear a vanishingly small fraction. Without automated
recommendation, discovery collapses to whatever is editorially promoted, and
the economics of the catalogue collapse with it.

Three broad families of technique are established in the literature, and each
has a characteristic failure.

**Collaborative filtering** infers preference from the behaviour of similar
users or the co-consumption of similar items. It requires no understanding of
the item whatsoever, which is both its strength and its limitation: it works
equally well for films, books and music, and it fails identically for all three
when interaction data is absent. Cold-start handling has been treated as an
open problem rather than a solved one throughout the field's development, and
metrics appropriate to the cold-start case had to be defined separately from
the standard accuracy measures.

**Content-based filtering** describes items by their own attributes and
recommends items similar to those a user has liked. For music this means
analysing the audio, the metadata, or both. Its advantage is precisely that it
has no cold-start exclusion — a recording can be described from its first
second of existence. Its historical disadvantage was that hand-crafted audio
descriptors captured only the aspects of the signal their designers chose to
encode, with the weighting between those aspects fixed by hand rather than
learned.

**Hybrid and context-aware systems** combine the two, or condition on listening
situation, time of day, activity and location. These generally perform best in
production, but they inherit the data requirements of their collaborative
component.

The importance of the content-based family has grown rather than diminished
with the advent of learned audio representations. The decisive result in this
direction trained a convolutional network to predict the latent item factors of
a collaborative model directly from audio spectrograms, so that recordings with
no usage data could be placed in the same latent space as recordings with it.
That established audio content analysis as the principal mechanism for
addressing the music cold-start problem rather than as a secondary signal.

The present project adopts the same premise but takes it further: no
collaborative model is assumed to exist at all. This is the situation of any
new service, any academic prototype, and any catalogue of genuinely new
material — and it is therefore worth knowing how far content alone can be
pushed.

## 1.3 Innovative Content in the Project

Five elements distinguish this project from a routine integration of existing
components.

**1. Four query modalities unified behind one catalogue and one backend.** A
seed recording, a free-text description of a desired sound, a typed title or
remembered lyric, and a hummed melody are all served from the same system. The
free-text path is not a separate tag classifier: it exploits the fact that the
CLAP audio and text encoders share one embedding space, so a typed description
and an audio clip are directly comparable and mood search requires no
additional training whatsoever.

**2. Vectorised subsequence dynamic time warping.** Scoring catalogue melodies
one at a time was measured at approximately 43 ms each, which exceeds any
interactive budget past a few hundred recordings. By choosing a step pattern
whose every permitted move advances the query index by exactly one frame, each
row of the cost matrix depends only on the previous row, and all reference
contours can be packed into one padded matrix and advanced simultaneously. The
only remaining interpreted loop is over the query's roughly sixty frames.
End-to-end hum latency fell from 2.86 s to 0.53 s.

**3. A controlled comparison against a properly standardised baseline.** The
hand-crafted arm is not a straw man. It is z-scored per dimension, without
which cosine similarity is decided entirely by whichever component has the
largest numerical range — a correction that by itself moved precision@5 from
0.138 to 0.245. A random control is reported beside every precision figure,
because in a catalogue dominated by one genre a random recommender scores well
by accident and absolute precision alone proves nothing.

**4. Diagnosis of a degenerate published checkpoint.** The music-specialised
CLAP checkpoint selected initially — on the reasonable assumption that a
music-trained model suits a music task — proved to place 94% of every
embedding's energy along a single shared direction, to score exactly at chance
on coarse genre agreement, and to return one identical ranking for four
unrelated text prompts. A single controlled substitution of the checkpoint,
holding clips and code constant, moved precision@5 from 0.172 to 0.315.

**5. A controlled negative result.** Anisotropy correction, which is standard
practice in the sentence-embedding literature, degrades retrieval monotonically
on this task. The finding is reported rather than suppressed, because it
indicates that the dominant shared direction carries task-relevant signal here
and that anisotropy should be treated as a diagnostic symptom rather than as a
defect to be corrected on reflex.

## 1.4 Block Schematic

**Figure 1.1 — Block schematic of the Hummingbird system.**

```
┌─────────────────────── OFFLINE INDEXING ──────────────────────┐
│                                                                │
│  Catalogue assembly                                            │
│  ListenBrainz popularity feed + curated singable list          │
│                         │                                      │
│                         ▼                                      │
│  Metadata resolution  (iTunes Search API)                      │
│  artist-token verification → preview URL, genre, artwork       │
│                         │                                      │
│                         ▼                                      │
│  Excerpt download — 30 s clips, cached locally                 │
│                         │                                      │
│        ┌────────────────┼────────────────┐                     │
│        ▼                ▼                ▼                     │
│  CLAP encoder    Baseline features   pYIN contour              │
│  10 s windows    MFCC + chroma +     semitones,                │
│  mean-pooled     contrast + tempo    median-subtracted         │
│       │                │                   │                   │
│       ▼                ▼                   ▼                   │
│  embeddings       embeddings          melody index             │
│  512-d .npy        87-d .npy          1,346 contours           │
└───────┬────────────────┬───────────────────┬──────────────────┘
        │                │                   │
        ▼                ▼                   ▼
┌─────────────────── ONLINE QUERY SERVICE (FastAPI) ────────────┐
│                                                                │
│  typed title / lyric ──► weighted full-text index              │
│                          title ≫ artist ≫ lyrics               │
│                              │                                 │
│                              ▼ (no title hit)                  │
│                          live iTunes lookup                    │
│                          + background embedding                │
│                              │                                 │
│  free-text mood ──► CLAP text encoder ──┐                      │
│                                          │                     │
│  hummed audio ──► pYIN ──► subsequence DTW over all melodies   │
│                                          │                     │
│                                          ▼                     │
│                          cosine similarity (one matmul)        │
│                          + optional MMR re-ranking             │
│                                          │                     │
│                                          ▼                     │
│                          ranked recommendations (JSON)         │
└────────────────────────────────┬───────────────────────────────┘
                                 │
                                 ▼
          Web client (React + Vite)  ·  Mobile client (Expo)
                                 │
                                 ▼
          audio streamed directly from Apple's preview CDN
```

The schematic separates two concerns that are often conflated. Everything above
the horizontal division happens once, offline, and produces three artefacts on
disk: two embedding matrices and one melody index. Everything below happens per
request and touches only those artefacts and the metadata store. No model
inference occurs on the request path except for free-text mood queries, where
the CLAP text encoder must embed the user's words, and for the on-demand
indexing of a recording the catalogue did not previously contain.

### 1.4.1 Module Description

**Figure 1.2 — Module interaction overview.** The ten modules below map
directly onto source files; the mapping is given in Appendix 1.

**Module 1 — Catalogue Builder (`build_catalog.py`).** Assembles the candidate
list from the ListenBrainz popular-recordings endpoint, which is keyless, and
from a hand-curated file of songs the project team can sing from memory. Each
title is resolved through the iTunes Search API to obtain a 30-second preview
URL, a genre label and cover artwork. Resolution is verified rather than
assumed: a candidate is accepted only if its artist name shares at least one
normalised token with the requested artist. The module additionally caps
over-represented genres and removes non-musical material.

**Module 2 — Preview Fetcher (`fetch_previews.py`).** Downloads and caches the
30-second excerpts concurrently, skipping clips already present so that the
step is resumable. The local cache is 1.5 GB for the present catalogue and is
used solely for offline feature extraction; it is never redistributed.

**Module 3 — Lyrics Fetcher (`fetch_lyrics.py`).** Retrieves lyrics from
LRCLIB, a free and keyless lyrics database, distinguishing genuinely
instrumental recordings from those merely absent from the source. Lyrics are
stored for search only and are never returned to clients.

**Module 4 — Audio Decoder (`audio.py`).** Decodes all audio through PyAV,
which bundles its own codecs. This is a necessary rather than a stylistic
choice: iTunes previews are AAC, browser recordings are Opus, the standard
Python audio library reads neither, and no system-wide codec installation can
be assumed on a target machine.

**Module 5 — Embedding Builder (`embed.py`, `build_index.py`).** Computes the
512-dimensional CLAP embedding for each excerpt by dividing it into consecutive
whole 10-second windows, embedding each independently, mean-pooling the
results, and L2-normalising. The build is checkpointed and resumable.

**Module 6 — Feature Extractor (`features.py`).** Computes the 87-dimensional
hand-crafted baseline vector and the human-readable descriptors — tempo,
estimated key, brightness and energy — that drive the "why is this similar?"
panel in the user interface.

**Module 7 — Melody Indexer (`melody.py`).** Extracts a key-invariant pitch
contour per recording using pYIN, filters out recordings whose voiced fraction
is too low to be hummable, and packs all surviving contours into a single
padded matrix for simultaneous scoring.

**Module 8 — Storage Layer (`store.py`, `store_sqlite.py`,
`store_postgres.py`).** Presents one interface over two interchangeable
backends. SQLite with FTS5 is the default and requires no credentials, so every
measurement in this report reproduces from a fresh copy of the project.
PostgreSQL with a weighted `tsvector` is the deployment backend. Both were
verified to return identical search results.

**Module 9 — Query Service (`main.py`, `itunes.py`, `snippets.py`).** The
FastAPI application exposing `/search`, `/find`, `/similar/{id}`,
`/similar-by-text`, `/hum`, `/track/{id}` and `/health`. It serves JSON only.

**Module 10 — Clients (`web/`, `mobile/`).** A React and Vite web application
and an Expo React Native mobile application, both consuming the same API and
both playing audio directly from the rights holder's preview endpoint.

### 1.4.2 Cost of the Project

A design constraint adopted at the outset was that no component may require
paid infrastructure or an authenticated third-party key. The constraint was met
in full; the total monetary cost of the project is **₹0**.

**Table 1.2 — Cost of the project, itemised.**

| Component | Provider / technology | Licence or tier | Cost |
|---|---|---|---|
| Popular-recordings feed | ListenBrainz | Open API, no key required | ₹0 |
| Metadata, previews, genre | iTunes Search API | Public, no key required | ₹0 |
| Lyrics | LRCLIB | Open API, no key required | ₹0 |
| Audio embedding model | `laion/clap-htsat-unfused` | Open weights, Hugging Face | ₹0 |
| Feature extraction | librosa | ISC licence | ₹0 |
| Audio decoding | PyAV | BSD licence | ₹0 |
| Backend framework | FastAPI, uvicorn | MIT licence | ₹0 |
| Metadata store (local) | SQLite with FTS5 | Public domain | ₹0 |
| Metadata store (hosted) | Supabase | Free tier | ₹0 |
| Backend hosting | Render | Free tier | ₹0 |
| Frontend hosting | Vercel | Hobby tier | ₹0 |
| Web client | React, Vite, TypeScript | MIT licence | ₹0 |
| Mobile client | Expo, React Native | MIT licence | ₹0 |
| Audio delivery | Apple preview CDN | Public, CORS-enabled | ₹0 |
| Compute for indexing | Project team's laptop | Owned hardware | ₹0 |
| **Total** | | | **₹0** |

Two decisions were load-bearing in achieving this. First, **no audio is
hosted**: the API returns the rights holder's own preview URL, which was
verified to send permissive cross-origin headers and to honour range requests,
so clips stream and seek directly from Apple's content delivery network. This
eliminates object storage, audio bandwidth, and any question of
redistribution. Second, **embeddings are precomputed** and the deployment
image excludes PyTorch entirely, which keeps the deployed artefact inside the
size limits of free hosting tiers.

The non-monetary cost is compute time. Indexing the full catalogue of 1,403
playable excerpts required 159 minutes on the project laptop, at approximately
0.2 recordings per second, and the preview cache occupies 1.5 GB of local disk.

### 1.4.3 Advantages and Disadvantages

**Table 1.1 — Advantages and disadvantages of the proposed system.**

| Advantages | Disadvantages |
|---|---|
| **No cold-start exclusion.** Every recording is recommendable as soon as its audio is analysed; a recording absent from the catalogue entirely is admitted at query time and becomes searchable within seconds. | **Genre agreement is a proxy metric.** Two acoustically dissimilar recordings sharing a label count as a hit, and two similar recordings with different labels count as a miss. A human listening study is the appropriate instrument and has not yet been conducted. |
| **No user data required.** The system holds no accounts, no listening history and no personal data, which removes an entire class of privacy obligation. | **Catalogue scale.** The reported figures come from 1,404 recordings, orders of magnitude below a commercial catalogue; conclusions are indicative rather than definitive. |
| **Mood search comes free.** Because audio and text share one embedding space, free-text queries need no tag vocabulary, no classifier and no additional training. | **Humming accuracy is modest.** 8 of 25 in the top 10 is the weakest component, and that figure is an upper bound measured on synthesised rather than human queries. |
| **Four query modalities, one backend.** Seed recording, free text, typed title or lyric, and hummed melody are served from one catalogue and one API. | **Analysis uses 30-second excerpts.** Structural variation outside the excerpt — a quiet intro, a key change, an extended outro — is not represented in the embedding. |
| **Interactive humming latency.** Vectorised subsequence DTW scores all catalogue melodies in one pass, at 0.53 s end to end. | **Cover versions outrank originals.** A typed title carries no artist, so a popular cover can displace the original; popularity-weighted disambiguation is not yet implemented. |
| **Zero monetary cost and fully reproducible.** Every data source is keyless and every dependency is open source; the default storage backend needs no credentials, so all measurements reproduce from a fresh copy. | **Catalogue composition is biased.** The popularity feed reflects one platform's userbase; a curated list and genre capping mitigate this but the catalogue is not a representative sample of recorded music. |
| **Explainable results.** Interpretable descriptors — tempo, key, brightness, energy — are stored alongside each recording and surfaced in the interface. | **Dependence on third-party availability.** Previews, metadata and lyrics come from external services that may rate-limit or withdraw access; the system distinguishes transport failure from genuine absence but cannot remedy it. |

---

# CHAPTER 2 — LITERATURE SURVEY

## 2.1 Study of Various Approaches in Recommender Systems

Recommendation from interaction data has been studied extensively, and the
conditions under which it fails are well characterised. The cold-start
situation — a user or item for which no interaction history exists — was
formalised together with metrics appropriate to it by Schein et al. [2], who
demonstrated that purely behavioural models cannot rank items they have never
observed being consumed. Celma [4] examined the consequence at catalogue scale,
showing that systems optimised on aggregate behaviour concentrate exposure on a
small head of popular items and leave the long tail effectively invisible.
Surveys of the field have repeatedly identified cold-start handling and the
incorporation of content and context as open problems rather than settled ones
[1], [5], [6].

**Table 2.1 — Families of recommender system approach.**

| Family | Basis of prediction | Cold start | Representative work |
|---|---|---|---|
| Collaborative filtering | Co-consumption across users | Fails entirely for new items | Schein et al. [2] |
| Content-based | Item's own attributes or signal | No exclusion | van den Oord et al. [3] |
| Context-aware | Situation, time, activity, location | Inherits CF limitations | Kaminskas and Ricci [6] |
| Hybrid | Combination of the above | Partially mitigated | Schedl et al. [1] |
| Music-context | Web text, tags, social data | Depends on text availability | Knees and Schedl [5] |

The most influential response within the music domain was presented by van den
Oord et al. [3], in which a convolutional network was trained to predict the
latent item factors of a collaborative filtering model directly from audio
spectrograms. Recordings without usage data could then be embedded into the
same latent space as recordings with it. That work established audio content
analysis as the principal mechanism by which the music cold-start problem is
addressed, and the present system follows the same premise, differing in that
no collaborative model is assumed to exist at all.

## 2.2 Existing Approaches and Frameworks

### 2.2.1 Hand-crafted audio descriptors

The descriptor vocabulary of content-based music retrieval was largely
established before the deep-learning period. Mel-frequency cepstral
coefficients, originally developed for speech recognition, were adapted to
music modelling by Logan [14], who examined which of the assumptions
underlying their use in speech remained valid for music. Chroma features, which
collapse spectral energy onto the twelve pitch classes and thereby describe
harmonic content independently of octave and timbre, were introduced by
Fujishima for real-time chord recognition [15]. Spectral contrast, which
measures the difference between spectral peaks and valleys within sub-bands and
so distinguishes harmonic from noise-like content, was proposed for music
classification by Jiang et al. [16].

Tzanetakis and Cook [7] combined timbral, rhythmic and pitch-content features
into what became the reference formulation of automatic genre classification,
and in doing so established genre agreement as a conventional proxy metric for
music similarity. Mature open-source implementations of this descriptor family
are available in Essentia [17] and librosa [18], the latter being used here.

A methodological point concerning these features proved decisive in
implementation. The components of a concatenated descriptor vector occupy very
different numerical ranges — cepstral coefficients extend to the hundreds while
chroma values are bounded in [0, 1] — so a distance computed over the raw
concatenation is dominated by whichever component has the largest scale.
Per-dimension standardisation is a precondition for a fair baseline rather than
an optional refinement.

### 2.2.2 Learned audio representations

Representation learning displaced hand-crafted descriptors for most audio
tasks. The release of AudioSet, a large ontology-structured and human-labelled
collection of audio events [20], made supervised pretraining at scale
practical. Hershey et al. [19] examined convolutional architectures on that
collection and showed that the resulting embeddings transferred to downstream
tasks, and Kong et al. [21] extended this with pretrained audio neural networks
for general audio pattern recognition. Chen et al. [22] subsequently introduced
a hierarchical token-semantic audio transformer that improved both accuracy and
computational efficiency, and that architecture serves as the audio encoder of
the CLAP checkpoints employed in this work. In parallel, self-supervised
contrastive objectives were shown to produce useful representations without
labels, the general formulation being established by contrastive predictive
coding [23].

### 2.2.3 Joint audio–language embedding

The decisive development for the present system is the construction of a shared
embedding space for audio and natural language. CLIP [12] demonstrated for
images that training an image encoder and a text encoder jointly on paired data
with a contrastive objective yields a space supporting zero-shot classification
by text prompt. Elizalde et al. [11] transferred the approach to audio under
the name CLAP, and Wu et al. [10] scaled it substantially, adding feature
fusion for variable-length inputs and keyword-to-caption augmentation to expand
the available training pairs; the publicly released LAION-CLAP checkpoints from
the latter work are those used here.

Within the music domain specifically, MuLan [24] learned a joint embedding of
music audio and free-form text from a very large corpus of weakly paired
examples, and MusCALL [25] applied contrastive audio–language learning to music
retrieval. Multimodal combinations of audio with text and images have likewise
been shown to improve genre classification over audio alone [26]. These results
collectively establish that a single contrastively trained space can serve both
audio-similarity and text-query retrieval, which is the property the present
system exploits to obtain mood search without a second model.

### 2.2.4 Query by humming

The retrieval of a recording from a sung or hummed rendition was proposed by
Ghias et al. [8], who converted a hummed query to a sequence of relative pitch
transitions and matched it approximately against a database of melodies. The
central difficulty identified then remains central now: an untrained singer
renders a melody with errors of absolute pitch, local timing and global tempo,
so matching must be invariant to transposition and tolerant of temporal
distortion. A comparative evaluation of the main families of search technique
was later conducted on a common testbed by Dannenberg et al. [35].

Reliable pitch tracking is the first requirement. The YIN estimator [30]
established an autocorrelation-based method with substantially reduced octave
error, and the probabilistic variant pYIN [31] replaced YIN's fixed threshold
with a distribution over candidate thresholds, producing multiple pitch
candidates per frame that are then decoded by a hidden Markov model. Melody
extraction from genuinely polyphonic material is harder still and has been
addressed by tracking and characterising pitch contours [32]. The matching step
is conventionally dynamic time warping, whose formulation for speech
recognition by Sakoe and Chiba [33] remains the reference; the subsequence
variant required here, in which alignment may begin and end anywhere in the
reference, is treated systematically by Müller [34]. A distinct but related
task is exact identification from a short noisy excerpt, solved by audio
fingerprinting [9], which is deliberately intolerant of variation and therefore
unsuitable for similarity-based recommendation.

**Table 2.2 — Existing frameworks, models and datasets surveyed.**

| Work | Contribution | Relevance to this project |
|---|---|---|
| van den Oord et al. [3] | Latent factors predicted from audio | Establishes the content-based premise |
| Radford et al. [12] | CLIP joint image–text space | The contrastive formulation adopted |
| Wu et al. [10] | LAION-CLAP, feature fusion | The checkpoint actually used |
| Elizalde et al. [11] | CLAP originating work | Cited as the method's origin |
| Chen et al. [22] | HTS-AT transformer | CLAP's audio branch |
| Huang et al. [24] | MuLan music–text embedding | Route to music-specific fine-tuning |
| Manco et al. [25] | MusCALL contrastive music retrieval | Confirms text-to-music retrieval |
| Hershey et al. [19] | CNN architectures for audio | Transferable audio embeddings |
| Kong et al. [21] | PANNs | Large-scale audio pretraining |
| Gemmeke et al. [20] | AudioSet | Pretraining corpus |
| Logan [14] | MFCC for music | Baseline component |
| Fujishima [15] | Chroma | Baseline component |
| Jiang et al. [16] | Spectral contrast | Baseline component |
| Tzanetakis and Cook [7] | Genre classification | Source of the evaluation proxy |
| McFee et al. [18] | librosa | Feature extraction library used |
| Bogdanov et al. [17] | Essentia | Alternative feature library |
| Ghias et al. [8] | Query by humming | The humming task definition |
| de Cheveigné and Kawahara [30] | YIN | Pitch tracking foundation |
| Mauch and Dixon [31] | pYIN | Pitch tracker actually used |
| Salamon and Gómez [32] | Polyphonic melody extraction | Indicated future improvement |
| Sakoe and Chiba [33] | DTW | Alignment foundation |
| Müller [34] | Subsequence DTW | The variant implemented |
| Dannenberg et al. [35] | QBH comparative evaluation | Benchmarking context |
| Wang [9] | Audio fingerprinting | Contrast: exact vs similar |
| Ethayarajh [36] | Anisotropy measurement | Diagnostic adopted |
| Gao et al. [37] | Representation degeneration | Explains the cone effect |
| Li et al. [38] | Isotropy transformation | The remedy that failed here |
| Liang et al. [39] | Modality gap | Multimodal space geometry |
| Radovanović et al. [40] | Hubness | High-dimensional retrieval risk |
| Carbonell and Goldstein [41] | MMR | Diversification implemented |
| Ziegler et al. [42] | Topic diversification | Alternative diversification |
| Robertson and Zaragoza [43] | BM25 | Lexical ranking used |
| Johnson et al. [44] | FAISS | Indicated at larger scale |
| Berenzweig et al. [27] | Acoustic vs subjective similarity | Evaluation validity |
| Bertin-Mahieux et al. [28] | Million Song Dataset | Comparable evaluation |
| Defferrard et al. [29] | FMA dataset | Comparable evaluation |
| Sturm [13] | The "horse" critique | Motivates the random control |
| Schedl et al. [1] | MRS challenges survey | Problem framing |
| Knees and Schedl [5] | Music similarity survey | Problem framing |
| Kaminskas and Ricci [6] | Context-aware music IR | Problem framing |
| Schein et al. [2] | Cold-start metrics | Problem framing |
| Celma [4] | Long tail | Problem framing |
| Oramas et al. [26] | Multimodal genre classification | Multimodal precedent |
| van den Oord et al. [23] | Contrastive predictive coding | Objective foundation |

### 2.2.5 Embedding geometry and evaluation

Two geometric pathologies of high-dimensional learned representations proved
directly relevant. Anisotropy — the concentration of embeddings within a narrow
cone rather than their distribution across the space — was measured in
contextual word representations by Ethayarajh [36], who found high average
cosine similarity between unrelated inputs. Gao et al. [37] analysed the
training dynamics that produce this degeneration, and Li et al. [38] proposed
transforming the distribution towards isotropy, reporting improved semantic
textual similarity. A related phenomenon specific to multimodal contrastive
models is the modality gap, in which audio and text embeddings occupy separated
regions of the nominally shared space [39]. Hubness is the second pathology: a
small number of points appear in the nearest-neighbour lists of
disproportionately many queries, distorting retrieval independently of
representation quality [40].

Evaluation of music similarity without ground-truth similarity judgements is
itself a research problem. Berenzweig et al. [27] compared acoustic similarity
measures against subjective human judgements and quantified the gap between
them. Public datasets with usable metadata, notably the Million Song Dataset
[28] and the Free Music Archive dataset [29], have made comparable evaluation
possible. Genre agreement remains the most widely used proxy, and Sturm [13]
demonstrated that systems can achieve strong figures on such proxies while
responding to confounds rather than to musical content. Lexical retrieval over
titles, artists and lyrics is a probabilistic ranking problem for which BM25 and
its field-weighted extensions are standard [43]; ranked similarity lists tend
towards redundancy, for which maximal marginal relevance [41] and topic
diversification [42] are the established remedies; and beyond the present scale
exhaustive cosine computation becomes impractical, requiring approximate
nearest-neighbour indexing [44].

## 2.3 Research Gap

The components surveyed above are individually mature. Three gaps were
identified and each is addressed by this project.

**Gap 1 — Integration without verification.** What is not commonly reported is
a single cold-start system in which one embedding index serves both
audio-similarity and free-text retrieval while a separate melodic index serves
hummed queries. More importantly, published checkpoints are routinely adopted
on the basis of their name and stated training domain, without any check that
the resulting embedding space separates anything at all. The magnitude of the
error observed here when that check was omitted — a checkpoint scoring exactly
at chance — indicates that the omission is not harmless.

**Gap 2 — Precision reported without a control.** Absolute precision figures
are frequently quoted in a catalogue whose genre distribution alone can account
for most of the score. In a catalogue that is 40% one genre, a random
recommender attains 0.40 by accident. Sturm [13] showed that systems can score
well on such proxies while responding to confounds. Every figure in Chapter 4
is therefore reported beside a matched random control, and lift over that
control is treated as the primary quantity.

**Gap 3 — Catalogue quality treated as an afterthought.** Metadata resolution
errors corrupt three things simultaneously: the stored embedding describes
audio that is not the recording the row claims to be; the genre label used as
evaluation ground truth belongs to a different recording; and a user who
searches the title is served different music. The third is visible; the second
silently degrades the metric by which the system is judged. Measurement of this
effect is reported in Chapter 4 and summarised below.

**Table 2.3 — Representative metadata resolution failures before artist
verification.**

| Requested | Returned |
|---|---|
| Boulevard of Broken Dreams (Green Day) | Lullaby cover by Sparrow Sleeps, labelled *Children's Music* |
| Nuts RM | White Sand — Migos |
| out of love RM | Call Out My Name — The Weeknd |
| Change pt.2 RM | BUTTERFLY EFFECT — Travis Scott |
| Into the Sun BTS | Into The Sun — Robyn |

---

# CHAPTER 3 — METHODOLOGY

## 3.1 Design of the Project

Let a catalogue be a finite set of recordings *T* = {*t*₁, *t*₂, …, *t<sub>N</sub>*}.
For each recording a short audio excerpt is available, together with metadata
comprising title, artist, album, genre label and, where obtainable, lyrics. No
user, no user identifier and no interaction history is assumed to exist, which
places the system in the permanent cold-start regime.

Three retrieval tasks are defined over this catalogue, plus one lexical task
required for usability.

**Task 1 — acoustic similarity.** Given a seed recording *t<sub>s</sub>* ∈ *T*,
return a ranked list of *k* recordings from *T* \ {*t<sub>s</sub>*} ordered by
perceptual similarity of sound. Similarity is continuous rather than binary, so
the required output is a ranked truncation rather than a set of matches.

**Task 2 — text-conditioned retrieval.** Given a free-text description *q* of a
desired sound, return a ranked list of *k* recordings whose audio corresponds
to that description. No fixed vocabulary of moods or tags is assumed.

**Task 3 — melodic identification.** Given a recording of a human humming,
singing or whistling, identify the recording in *T* from which that melody
originates. The query is monophonic, the reference polyphonic, absolute pitch
arbitrary, tempo approximate, and the query corresponds to an unknown short
interval of the reference.

**Task 4 — lexical lookup.** Given a typed string that may be a title, an
artist name or a remembered lyric fragment, identify the intended recording and
return it *before* its acoustic neighbours. This distinction matters: a user
who types a title expects that title, and routing such a query through a
semantic text encoder returns plausible but incorrect recordings.

### 3.1.1 Data / Input Description

The catalogue is assembled from two sources, deliberately combined.

A **keyless popularity feed** (ListenBrainz) supplies broadly known recordings
across several time windows. A **manually curated list** supplies recordings
the project team can sing from memory. The second source is not decorative:
query-by-humming can only be evaluated on recordings the evaluator already
knows, so their presence in the catalogue is a precondition for the humming
evaluation being valid rather than circular. The curated list additionally
counters the sampling bias of the popularity feed, which reflects the
demographics of one particular listening platform.

Each title is resolved through the iTunes Search API to obtain a 30-second
preview excerpt, a genre label and cover artwork. Resolution is verified by the
artist-token rule described in §1.4.1. Lyrics are obtained from LRCLIB.

**Table 3.1 — Catalogue composition and coverage.**

| Property | Value |
|---|---|
| Total recordings | 1,404 |
| With a playable 30-second excerpt | 1,403 |
| With lyrics | 1,354 (96%) |
| Identified as instrumental | 20 |
| Not present in the lyrics source | 50 |
| In the CLAP embedding index | 1,403 |
| In the baseline embedding index | 1,403 |
| In the melody index | 1,346 |
| Distinct genre labels (fine) | 46 |
| Coarse genre families | 31 |
| Local preview cache | 1.5 GB |

**Figure 3.1 — Catalogue composition by genre.** The principal genres after
capping are Pop (281), Alternative (262), K-Pop (250), Rock (164), Hip-Hop
(102), Hard Rock (66), Electronic (45) and Metal (44), with the remainder
distributed across 38 smaller labels.

Genre capping was applied because an uncapped popularity feed produced a
catalogue that was 39% K-Pop, which would have made genre-agreement precision
largely a measure of that single genre's internal coherence. Recordings whose
voiced fraction falls below 0.25 — percussion-only and ambient material that no
hum could match — are excluded from the melody index but retained for acoustic
similarity.

Two classes of defect were identified and removed during catalogue
construction. Metadata mis-resolution affected 63 of 759 cached lookups (8.3%)
before artist verification was introduced; the examples are given in Table 2.3.
Separately, five non-musical recordings — white noise, rainfall and
tone-generator tracks — were found among 1,409, these ranking highly in
popularity feeds because listeners leave them playing for hours. One such
recording was returned first for a chill lo-fi mood query. The removal rule
matches on artist name alone, deliberately: an initial scan matching title
keywords implicated fourteen recordings, but nine belonged to the bands Sleep
Token and Sleep Theory and were genuine music.

### 3.1.2 Model / Framework Description

Two representations are computed for every excerpt, so that the learned and
hand-crafted approaches may be compared on identical audio under identical
evaluation conditions.

**The learned representation** is produced by the audio encoder of the
LAION-CLAP model [10], specifically the `clap-htsat-unfused` checkpoint, whose
audio branch is the hierarchical token-semantic audio transformer of Chen et
al. [22].

**Figure 3.2 — CLAP audio embedding pipeline.**

```
30 s excerpt
     │
     ▼
divide into consecutive WHOLE 10 s windows        (no padded tail window)
     │
     ▼
embed each window independently                   (is_longer = False)
     │                                            (deterministic truncation)
     ▼
mean-pool the window vectors
     │
     ▼
L2-normalise  →  512-d unit vector
```

Three properties of this procedure are deliberate and each corrects an observed
fault. Only whole windows are used, because appending a zero-padded tail window
caused the stored index to disagree with vectors computed at query time, giving
a cosine of 0.97 where 1.000000 was required. Truncation is deterministic
rather than random, so that embedding the same excerpt twice yields an
identical vector. The feature-fusion input flag is held false, because the
checkpoint in use was not trained with the fusion branch enabled and activating
it routes audio through untrained parameters — disabling it moved mean pairwise
cosine from 0.92 to 0.73.

**The hand-crafted baseline** is an 87-dimensional vector, standardised to zero
mean and unit variance per dimension across the catalogue.

**Table 3.2 — Composition of the 87-dimensional baseline vector.**

| Component | Statistic | Dimensions |
|---|---|---|
| Mel-frequency cepstral coefficients (20) | mean and standard deviation | 40 |
| Constant-Q chroma (12 bins) | mean and standard deviation | 24 |
| Spectral contrast (7 bands) | mean and standard deviation | 14 |
| Spectral centroid | mean and standard deviation | 2 |
| Spectral roll-off | mean and standard deviation | 2 |
| Zero-crossing rate | mean and standard deviation | 2 |
| Root-mean-square energy | mean and standard deviation | 2 |
| Tempo | single estimate | 1 |
| **Total** | | **87** |

Interpretable descriptors — tempo in beats per minute, estimated key by
Krumhansl–Schmuckler profile correlation, spectral centroid as a brightness
proxy, and root-mean-square energy — are additionally stored so that the
interface can state why two recordings were judged similar.

**Similarity search.** All embeddings are L2-normalised and held in memory as a
dense matrix *M* ∈ ℝ^(*N*×*d*). Cosine similarity against a query vector
reduces to a single matrix–vector product, sub-millisecond at this catalogue
size. Approximate nearest-neighbour indexing [44] was therefore not adopted, as
it would introduce a dependency and an approximation for no measurable latency
benefit below approximately 10⁵ recordings.

**Text-conditioned retrieval.** Since the CLAP audio and text encoders share
one embedding space, a free-text query is embedded by the text encoder and used
directly as the query vector against the same audio matrix.

**Lexical retrieval.** Two storage backends are implemented behind one
interface and verified to agree: SQLite with FTS5 using BM25 field weights of
10.0, 4.0 and 1.0 for title, artist and lyrics; and PostgreSQL using a
generated weighted `tsvector` with weight classes A, B and C. Field weighting
is necessary and not cosmetic: without it, a query naming an artist returns
that artist before a recording whose *title* is the query string.

### 3.1.3 Algorithms / Mathematical Models

#### Algorithm 1 — Unified query resolution

```
Algorithm 1  RESOLVE-QUERY
Input :  query q; mode m ∈ {TITLE, MOOD, HUM}; result count k;
         diversity parameter λ
Output:  seed recording s (may be null); ranked list R of k recordings

 1  if m = TITLE then
 2      H ← FULLTEXT-SEARCH(q)              // weighted: title ≫ artist ≫ lyrics
 3      titleHit ← ∃ h ∈ H : MATCHED-FIELD(h, q) = title
 4      if H = ∅ or ¬titleHit then
 5          try
 6              L ← LIVE-LOOKUP(q)
 7              if L ≠ null and ∀w ∈ TOKENS(q): w ∈ TOKENS(TITLE(L)) then
 8                  s ← INSERT-TRACK(L)
 9                  spawn EMBED-AND-INDEX(s)        // background task
10                  return (s, first 3 elements of H)
11          catch Unavailable                        // rate limited, not absent
12              if H = ∅ then return (null, ∅) with transport-failure flag
13      s ← first element of H
14  else if m = MOOD then
15      v ← CLAP-TEXT-ENCODE(q)
16      return (null, RANK(v, k, λ))
17  else                                             // m = HUM
18      c ← EXTRACT-CONTOUR(q, monophonic = true)
19      s ← MELODY-MATCH(c)                          // Algorithm 2
20
21  v ← EMBEDDING(s)
22  if v = null then return (s, ∅) with indexing-in-progress flag
23  return (s, RANK(v, k, λ))
24
25  procedure RANK(v, k, λ)
26      v ← v / ‖v‖₂
27      sim ← M · v
28      C ← indices of the 3k highest entries of sim
29      if λ = 0 then return first k elements of C
30      R ← ∅
31      while |R| < k do                             // maximal marginal relevance
32          c* ← argmax_{c ∈ C∖R} [ (1−λ)·sim[c] − λ·max_{r ∈ R} (M[c] · M[r]) ]
33          R ← R ∪ {c*}
34      return R
```

The ordering of lines 1–13 encodes a requirement established during
development. A lexical hit must be preferred whenever the typed string matches
a title, and the live fallback must be consulted when it does not — but a
transport failure at line 11 must not discard a usable local result. That
precise failure caused a correct lyric search ("caught in a landslide") to
return nothing while the external interface was rate limited.

#### Algorithm 2 — Vectorised subsequence DTW

**Figure 3.3 — Pitch contour extraction**, applied identically to an indexed
clip and to a hum so that the two are comparable:

```
audio → pYIN f0 → voiced frames → bridge short unvoiced gaps
      → 5-frame median filter → convert to MIDI semitones
      → subtract median (key invariance) → resample to fixed rate
```

Frequencies are converted to semitones by

&nbsp;&nbsp;&nbsp;&nbsp;*s*(*t*) = 69 + 12 · log₂( *f*₀(*t*) / 440 )

and the key-invariant contour is *c*(*t*) = *s*(*t*) − median(*s*).

**Figure 3.4 — Subsequence DTW alignment.** A six-second hum aligns with a
short stretch somewhere inside a thirty-second reference; the alignment is
therefore free to begin and end at any position in the reference.

```
Algorithm 2  MELODY-MATCH
Input :  query contour c ∈ ℝⁿ; reference matrix R ∈ ℝ^(N×W) right-padded
         with PAD = 10⁶; true lengths ℓ ∈ ℕᴺ; result count k;
         tempo scales S = {0.7, 0.85, 1.0, 1.2, 1.5}
Output:  k recordings of lowest alignment cost

 1  best ← (∞, ∞, …, ∞)
 2  for each σ ∈ S do
 3      c′ ← RESAMPLE(c, round(n · σ))
 4      n′ ← length(c′)
 5      D ← |R − c′[0]|                      // row 0: free start anywhere
 6      for i ← 1 to n′ − 1 do
 7          E ← |R − c′[i]|                  // local distance, all refs at once
 8          A ← SHIFT-RIGHT(D, 1), col 0 ← PAD        // move (i−1, j−1)
 9          B ← SHIFT-RIGHT(D, 2), cols 0,1 ← PAD     // move (i−1, j−2)
10          D ← E + min(D, A, B)             // elementwise over N × W
11      valid ← [ j < ℓ[r] ]
12      cost ← min over valid j of D[r, j] / n′       // free end anywhere
13      cost[r] ← ∞ wherever ℓ[r] < n′/2    // reference too short to contain query
14      best ← min(best, cost)
15  return the k recordings with smallest best
```

Two design choices make Algorithm 2 tractable.

First, **every permitted move advances the query index *i* by exactly one
frame**. Row *i* of the cost matrix therefore depends only on row *i*−1, never
on another cell of row *i* itself. Had a horizontal move (*i*, *j*−1) been
admitted, each row would depend on its own earlier columns, the inner loop
would be forced to proceed cell by cell, and the computation could not be
expressed as array operations.

Second, **all reference contours are packed into one padded matrix**, so line
10 advances the recurrence for every catalogue recording simultaneously. The
only remaining interpreted loop is over the query's frames, typically about
sixty. Scoring recordings individually was measured at approximately 43 ms
each, which exceeds an interactive budget at a few hundred recordings; the
vectorised formulation reduced end-to-end hum latency from 2.86 s to 0.53 s.
Padding is filled with a value large enough that a padded cell can never win
the minimum at line 10, and line 11 restricts the free-end minimisation to each
reference's true length.

### 3.1.4 Evaluation Metrics

*(The supplied template numbers this subsection 3.1.3 a second time; it is
given as 3.1.4 here for clarity.)*

The principal metric is **genre-agreement precision@k**. Each catalogue
recording is used in turn as a seed, and the proportion of its top-*k*
neighbours sharing the seed's genre label is averaged over all seeds:

&nbsp;&nbsp;&nbsp;&nbsp;P@*k* = (1/*N*) · Σ<sub>*i*=1..*N*</sub> (1/*k*) · |{ *j* ∈ top-*k*(*i*) : genre(*j*) = genre(*i*) }|

Scores are computed twice: against the 46 raw metadata labels ("fine") and
against 31 coarse genre families, since the fine labels distinguish categories
that are not acoustically distinct.

**Table 3.3 — Evaluation metrics and their interpretation.**

| Metric | Definition | Why it is reported |
|---|---|---|
| P@5, P@10 (fine) | Genre agreement over 46 raw labels | Strictest label agreement |
| P@5, P@10 (coarse) | Genre agreement over 31 families | Tolerates label fragmentation |
| Random control | *k* recordings drawn uniformly | Establishes the chance baseline |
| Lift | P@*k* ÷ random P@*k* | The primary quantity |
| Top-10 recall (humming) | Correct recording in the top 10 | Melodic identification accuracy |
| Median latency | Wall-clock per hum query | Interactivity |
| Mean pairwise cosine | Average similarity over all pairs | Detects a collapsed space |
| Anisotropy | Norm of the mean embedding vector | Detects a degenerate space |

The random control is the column that decides interpretation. In a catalogue
that is 40% one genre, a random recommender attains 0.40 by accident, so
absolute precision alone proves nothing and **lift over the control is treated
as primary**. The limitations of genre agreement as a proxy are acknowledged in
§1.4.3 and §4.2, and a human listening study is identified as the appropriate
instrument.

---

# CHAPTER 4 — RESULTS AND DISCUSSION

## 4.1 Results

All figures below were measured on the full catalogue of 1,404 recordings
across 46 genre labels, with every recording used in turn as a seed, except
where a smaller catalogue is stated explicitly.

**Table 4.1 — Genre-agreement precision@k on the full catalogue.**

| Engine | P@5 fine | lift | P@10 fine | P@5 coarse | lift | P@10 coarse |
|---|---|---|---|---|---|---|
| CLAP `clap-htsat-unfused` | **0.337** | **2.55×** | 0.321 | **0.537** | **2.03×** | 0.522 |
| Baseline (MFCC/chroma, z-scored) | 0.276 | 2.08× | 0.255 | 0.462 | 1.74× | 0.447 |
| Random control | 0.132 | 1.00× | 0.129 | 0.265 | 1.00× | 0.261 |

**Figure 4.1 — Genre-agreement precision@5 by engine**, fine and coarse,
with the random control shown for both.

Both engines clearly exceed the random control, establishing that genuine
acoustic structure is being retrieved rather than the catalogue's genre prior.
The learned embedding leads the hand-crafted baseline by 22% relative on fine
labels and 16% on coarse families, and exceeds chance by a factor of 2.55.

**Query-by-humming.** 8 of 25 queries placed the correct recording in the top
10 against a 479-melody index, at 0.93 s median latency. This figure is an
**upper bound**, not a performance estimate: it was measured on synthesised
"perfect hums" derived from the reference contours themselves, free of the
pitch and timing error a human introduces. The melody index has since grown to
1,346 recordings, which can only make the task harder.

**Lexical search.** Of 1,404 recordings, 1,354 (96%) carry lyrics. Recordings
are locatable by title, artist, or a remembered line, with the matched line
returned so the user can see why a recording was retrieved. The live fallback
measurably extends coverage: a recording absent from the catalogue is resolved
externally, returned immediately, embedded in the background, and available to
similarity queries within seconds — demonstrated with a J-Pop recording not
present minutes earlier which, once embedded, returned four acoustically
plausible rock and alternative neighbours at cosine 0.95–0.96.

## 4.2 Discussion

### 4.2.1 How the margin between engines moved

The behaviour of the gap between the two engines under changing conditions is
more informative than the headline figure.

**Table 4.2 — Effect of catalogue correction and growth on the engine gap**,
precision@5 on fine genre labels.

| Condition | CLAP | Baseline | Random | CLAP lead | CLAP lift |
|---|---|---|---|---|---|
| 529 recordings, uncorrected metadata | 0.295 | 0.256 | 0.122 | 15% | 2.42× |
| 529 recordings, corrected metadata | 0.332 | 0.310 | 0.154 | 7% | 2.16× |
| 1,404 recordings, corrected metadata | 0.337 | 0.276 | 0.132 | 22% | 2.55× |

**Figure 4.2 — Effect of catalogue growth on the gap between engines.**

Three conditions have been measured. On the 529-recording catalogue with
uncorrected metadata the learned embedding led by 15%. Correcting the metadata
narrowed the gap to 7%, indicating that a substantial part of the embedding's
apparent advantage had been an artefact of noisy ground truth. On the
1,404-recording catalogue the gap widened again to 22% — but by a different
mechanism: the embedding's absolute precision was essentially unchanged (0.332
to 0.337) whereas the baseline's *fell* (0.310 to 0.276).

The interpretation offered is that the hand-crafted descriptors scale less well
than the learned embedding. A fixed 87-dimensional vector of spectral and
rhythmic summary statistics is adequate for separating a few hundred recordings
across a handful of broad genres, but as the catalogue triples and the label
set broadens to 46 genres, the number of recordings sharing similar summary
statistics while sounding quite different grows faster than the descriptor's
capacity to distinguish them.

Two cautions attach. First, the random control fell from 0.154 to 0.132 between
the two catalogue sizes, reflecting the wider genre spread of the larger
catalogue, so part of the increase in *lift* is attributable to the control
becoming harder rather than to either engine improving. The baseline's fall in
absolute precision, however, cannot be explained that way. Second, a single
pair of catalogue sizes does not establish a scaling law, and the claim is
stated as the direction of an observed effect rather than as a quantified
relationship.

### 4.2.2 Catalogue quality as a precondition for valid evaluation

Introducing artist-token verification caused 71 cached resolutions to be
discarded and re-fetched, 731 verified answers being retained so that
re-resolution cost minutes rather than the hour a full refetch would have
required. On the 529-recording catalogue then in use, the correction raised
precision@5 for both engines — CLAP from 0.295 to 0.332 and the baseline from
0.256 to 0.310. The random control, however, rose in parallel from 0.122 to
0.154, because removing mis-resolved oddities left a catalogue of narrower
genre diversity. **Lift over the random control therefore fell slightly even as
absolute precision improved.** This is reported in preference to quoting
whichever figure is more favourable, and illustrates concretely why the control
column is not optional.

### 4.2.3 Qualitative behaviour

Qualitative behaviour is consistent with the metric. A jazz seed returns jazz;
a grunge seed returns alternative rock of comparable era and distortion; a
piano-led ballad returns other piano-led ballads across nominally different
genres — a case where the genre proxy *understates* retrieval quality. Text
queries behave as the shared embedding space predicts, with "jazz saxophone and
piano", "heavy distorted guitar" and "sad slow piano ballad" each returning
appropriate recordings without any tag vocabulary having been defined.

## 4.3 Screenshots / Output / Figures / Tables

The figures below were captured from the running system. The sidebar in each
shows the live index state: 1,404 recordings held, 1,403 embedded, 1,346 in the
melody index.

**Figure 4.3 — Web client, song search with similar recordings.** The query
"bohemian" resolves to Bohemian Rhapsody by Queen, shown as the matched
recording, with its acoustic neighbours ranked beneath: Someone Like You
(0.94), To Love a Boy (0.93), Let It Be (0.92) and others. Each row carries
the reason for the match in interpretable terms — "similar tempo (134 BPM)",
"both major · similar brightness" — and each is playable in place.

**Figure 4.4 — Web client, free-text mood search.** The query "chill lo-fi
beats" returns Boards of Canada at the top (0.56), followed by Pink Floyd,
an instrumental cover and Daft Punk. No tag vocabulary was defined; the
ranking comes from the CLAP text encoder operating in the same space as the
audio. The absence of ambient-noise tracks confirms the non-music filter of
§3.1.1 is effective, this query having previously returned a white-noise
recording first.

**Figure 4.5 — Web client, query-by-humming panel.** The recording interface,
showing the readiness indicator, the live level meter that animates while
recording, and the capture control. Recording is limited to ten seconds and
requires microphone permission, which browsers grant only on localhost or
over HTTPS.

**Figure 4.6 — Interactive API documentation.** The automatically generated
OpenAPI documentation at `/docs`, listing all eight endpoints — `/health`,
`/search`, `/find`, `/similar/{track_id}`, `/similar-by-text`, `/hum`,
`/track/{track_id}` and `/audio/{track_id}` — with their request and response
schemas and a "Try it out" control for each.

**Sample retrieval output.** The following were produced by the running system:

| Seed | Top neighbours returned |
|---|---|
| Take Five (Jazz) | Fly Me to the Moon, Superstition, Under the Bridge |
| Smells Like Teen Spirit | Everlong, Back In Black, Mr. Brightside |
| Bohemian Rhapsody | Someone Like You, Let It Be, Perfect (all piano ballads) |
| "jazz saxophone and piano" | Take Five |
| "heavy distorted guitar" | Back In Black, Seven Nation Army, Everlong |
| "sad slow piano ballad" | Hallelujah, Bohemian Rhapsody, Let It Be |
| Gurenge (not in catalogue) | Bring Me to Life, In the End, Helena, Hysteria |

The final row demonstrates the live fallback end to end: the recording was
fetched from the external metadata service, embedded on demand, and returned
acoustically plausible neighbours at cosine 0.95–0.96 within seconds.

## 4.4 Ablation Study

Two ablations were conducted, and both produced results that contradicted the
expectation held before measurement.

### 4.4.1 Checkpoint substitution

The first embedding index returned Billie Jean as the nearest neighbour of Take
Five at cosine 0.992, with essentially all pairs scoring near 0.99. High
similarity across unrelated material is the signature of a collapsed space.
Four distinct faults were identified by measurement.

**Table 4.4 — Checkpoint comparison and the faults corrected.**

| # | Fault | Correction | Effect |
|---|---|---|---|
| 1 | Baseline features never standardised | z-score every dimension | P@5 0.138 → 0.245 |
| 2 | `is_longer` set true, routing audio through an untrained fusion branch | hold the flag false | mean pairwise cosine 0.92 → 0.73 |
| 3 | Random truncation — the same clip embedded twice gave different vectors | deterministic mean-pooled windows | reproducibility restored |
| 4 | **`larger_clap_music` is degenerate on this task** | substitute `clap-htsat-unfused` | **P@5 0.172 → 0.315** |

The fourth fault dominated. The music-specialised checkpoint was selected
initially on the reasonable assumption that a music-trained model would suit a
music task. Measurement showed that **94% of every embedding's energy lay along
a single shared direction**, that the checkpoint scored *exactly at chance* on
coarse genre agreement, and that all four distinct text prompts returned an
identical ranking — the clearest possible demonstration that the space
separated nothing. Substituting the general checkpoint as a single controlled
change, with identical excerpts and identical code, moved precision@5 from
0.172 to 0.315 and text discrimination from one distinct ranking out of four to
four out of four.

The practical lesson is that a published checkpoint's name and stated training
domain are not evidence of its fitness, and that high cosine similarity figures
can conceal a space with no discriminative structure. A standing diagnostic —
mean-vector norm, pairwise similarity distribution, and distinctness of
rankings across unrelated text prompts — was implemented and is the mechanism
by which the fault was finally localised.

### 4.4.2 Anisotropy correction

On the working checkpoint, anisotropy remains high at 0.853. The
text-embedding literature [36], [37], [38] would suggest correcting it. Four
variants were evaluated.

**Table 4.3 — Anisotropy correction ablation**, 529-recording catalogue.

| Variant | P@5 fine | P@5 coarse |
|---|---|---|
| As produced by the model | **0.315** | **0.476** |
| Mean-centred | 0.299 | 0.468 |
| Mean-centred, top-1 principal component removed | 0.290 | 0.420 |
| Mean-centred, top-2 principal components removed | 0.251 | 0.355 |

**Figure 4.7 — Anisotropy ablation.** Precision falls monotonically as
correction is strengthened.

Retrieval degrades monotonically. The dominant shared direction therefore
carries task-relevant signal in this setting rather than constituting nuisance
variance, and the remedy transferred from the sentence-embedding literature is
actively harmful here. Anisotropy is nonetheless worth *measuring*: it is
precisely the statistic that exposed the degenerate checkpoint of §4.4.1. The
conclusion drawn is that anisotropy should be treated as a diagnostic symptom
rather than as a defect to be corrected reflexively, and embeddings are
consequently used as the model produces them.

## 4.5 Comparison with Existing Approaches

**Table 4.5 — Comparison with existing approaches.**

| Criterion | Collaborative filtering | Audio fingerprinting [9] | Hand-crafted content [7], [14]–[16] | **Hummingbird (proposed)** |
|---|---|---|---|---|
| Requires interaction data | Yes | No | No | **No** |
| Cold-start coverage | None for new items | Full | Full | **Full** |
| Returns *similar* recordings | Yes | No — exact match only | Yes | **Yes** |
| Accepts a hummed query | No | No — needs the exact recording | No | **Yes** |
| Accepts free-text mood | No | No | Only with a trained tag model | **Yes, with no extra model** |
| Explains the match | Rarely | N/A | Partially | **Yes — tempo, key, brightness, energy** |
| Retrieval quality (P@5 here) | Not applicable | Not applicable | 0.276 | **0.337** |
| Monetary cost | Infrastructure + data | Infrastructure | Compute only | **₹0** |

Relative to collaborative filtering, the proposed system requires no
interaction data and therefore has no cold-start exclusion. Relative to audio
fingerprinting [9], which identifies an exact recording from an exact excerpt,
the present system retrieves *similar* recordings and accepts an imprecise sung
query. Relative to systems built solely on hand-crafted descriptors [7], [14],
[15], [16], a measurable improvement is obtained — 0.337 against 0.276 — and
free-text mood retrieval is obtained essentially without additional cost, which
a descriptor-based system cannot provide at all without a separately trained
tag model.

The honest qualification is that the improvement over a *properly standardised*
hand-crafted baseline is real but not transformative at small catalogue sizes,
and that the project's more durable contributions are the two diagnostic
findings of §4.4 rather than the precision margin.

---

# CONCLUSION AND FUTURE SCOPE

## Conclusion

A content-based music recommendation system operating without any user
interaction data has been designed, implemented and evaluated. Four query
modalities — a seed recording, a free-text description of a desired sound, a
typed title or remembered lyric, and a hummed melody — are served from a single
catalogue of 1,404 recordings and a single backend. The system is cold-start by
construction: a recording becomes recommendable as soon as its audio has been
analysed, and a recording absent from the catalogue is admitted at query time,
analysed in the background, and available to subsequent similarity queries
within seconds. Total monetary cost is ₹0.

Three findings constitute the substantive contribution.

**First**, a joint audio–language embedding was confirmed to outperform a
well-standardised hand-crafted descriptor baseline, attaining precision@5 of
0.337 against 0.276 at 2.55 times the random control. The margin was found to
depend strongly on experimental conditions: it fell from 15% to 7% once errors
in the evaluation ground truth were corrected, and widened to 22% as the
catalogue grew from 529 to 1,404 recordings — the latter because the baseline's
absolute precision fell while the embedding's held, suggesting that fixed
summary descriptors scale less well than a learned representation.

**Second**, a publicly released music-specialised CLAP checkpoint was diagnosed
as degenerate on this task: 94% of embedding energy along one shared direction,
coarse genre agreement at chance, and four distinct text prompts producing one
identical ranking. A single controlled checkpoint substitution nearly doubled
precision@5. Since a checkpoint's name and declared training domain gave no
indication of this, routine diagnosis of an embedding space before it is
trusted is argued to be necessary practice.

**Third**, a controlled negative result was obtained: anisotropy correction
degraded retrieval monotonically, from 0.315 to 0.251 in precision@5 as
correction was strengthened. A remedy well supported in the sentence-embedding
literature does not transfer to this task.

A methodological position follows from all three. Each was obtained by
measurement against a control, each would have been invisible to inspection of
summary similarity figures alone, and in two of the three cases the measurement
contradicted a reasonable prior expectation.

## Limitations

The limitations are stated plainly and are reproduced from §1.4.3: genre
agreement is a proxy and the human listening study has not been run; the
catalogue of 1,404 recordings is orders of magnitude below commercial scale;
query-by-humming is the weakest component and its reported figure is an upper
bound on synthesised queries; analysis uses 30-second excerpts so structure
outside the excerpt is unrepresented; cover versions outrank originals for
typed titles; and the catalogue's composition reflects the bias of its
popularity source.

## Future Scope

1. **Human evaluation.** A listening study over 20 seed recordings and their
   top-5 recommendations, rated on a five-point scale by multiple raters with
   inter-rater agreement reported, would replace the genre proxy with direct
   measurement of the quantity of interest. This is the single most valuable
   outstanding item.
2. **Melodic representation.** Replacing monophonic pitch tracking of
   polyphonic mixtures with dedicated melody extraction [32], and evaluating on
   hums recorded by people who know the recordings rather than on synthesised
   contours, should address the weakest component.
3. **Catalogue scale and indexing.** Extension towards 10⁵ recordings would
   require approximate nearest-neighbour indexing [44] in place of exhaustive
   cosine search, and would permit hubness effects [40] to be measured rather
   than assumed negligible.
4. **Fine-tuning on music.** The embedding is used entirely off the shelf.
   Contrastive fine-tuning on music-specific pairs, following MuLan [24] and
   MusCALL [25], is the obvious route to a larger margin over the baseline,
   provided the resulting space is subjected to the diagnostic procedure of
   §4.4.1.
5. **Hybrid recommendation.** Where interaction data becomes available, the
   content embedding can be combined with collaborative signal in the manner of
   van den Oord et al. [3], retaining cold-start coverage while benefiting from
   behavioural data for established recordings.
6. **Cover-version disambiguation.** Popularity-weighted ranking of lexical
   matches would address the limitation noted in §4.5.
7. **Full-track analysis.** Embedding complete recordings rather than
   30-second excerpts, with segment-level indexing, would capture structural
   variation currently invisible to the system.

---

# REFERENCES

[1] Schedl M., Zamani H., Chen C.-W., Deldjoo Y., Elahi M., "Current challenges
and visions in music recommender systems research", *International Journal of
Multimedia Information Retrieval*, vol. 7, no. 2, 2018, pp. 95–116.

[2] Schein A. I., Popescul A., Ungar L. H., Pennock D. M., "Methods and metrics
for cold-start recommendations", *Proceedings of the 25th Annual International
ACM SIGIR Conference on Research and Development in Information Retrieval*,
11–15 August 2002, Tampere, Finland, 2002, pp. 253–260.

[3] van den Oord A., Dieleman S., Schrauwen B., "Deep content-based music
recommendation", *Advances in Neural Information Processing Systems (NIPS)*,
vol. 26, 2013, pp. 2643–2651.

[4] Celma Ò., *Music Recommendation and Discovery: The Long Tail, Long Fail,
and Long Play in the Digital Music Space*, Springer, Berlin, 2010.

[5] Knees P., Schedl M., "A survey of music similarity and recommendation from
music context data", *ACM Transactions on Multimedia Computing, Communications,
and Applications*, vol. 10, no. 1, 2013, pp. 1–21.

[6] Kaminskas M., Ricci F., "Contextual music information retrieval and
recommendation: State of the art and challenges", *Computer Science Review*,
vol. 6, no. 2–3, 2012, pp. 89–119.

[7] Tzanetakis G., Cook P., "Musical genre classification of audio signals",
*IEEE Transactions on Speech and Audio Processing*, vol. 10, no. 5, 2002,
pp. 293–302.

[8] Ghias A., Logan J., Chamberlin D., Smith B. C., "Query by humming: Musical
information retrieval in an audio database", *Proceedings of the Third ACM
International Conference on Multimedia*, 5–9 November 1995, San Francisco, CA,
USA, 1995, pp. 231–236.

[9] Wang A., "An industrial-strength audio search algorithm", *Proceedings of
the 4th International Conference on Music Information Retrieval (ISMIR)*,
26–30 October 2003, Baltimore, MD, USA, 2003, pp. 7–13.

[10] Wu Y., Chen K., Zhang T., Hui Y., Berg-Kirkpatrick T., Dubnov S.,
"Large-scale contrastive language-audio pretraining with feature fusion and
keyword-to-caption augmentation", *Proceedings of the IEEE International
Conference on Acoustics, Speech and Signal Processing (ICASSP)*, 4–10 June
2023, Rhodes Island, Greece, 2023, pp. 1–5.

[11] Elizalde B., Deshmukh S., Al Ismail M., Wang H., "CLAP: Learning audio
concepts from natural language supervision", *Proceedings of the IEEE
International Conference on Acoustics, Speech and Signal Processing (ICASSP)*,
4–10 June 2023, Rhodes Island, Greece, 2023, pp. 1–5.

[12] Radford A., Kim J. W., Hallacy C., Ramesh A., Goh G., Agarwal S., Sastry
G., Askell A., Mishkin P., Clark J., Krueger G., Sutskever I., "Learning
transferable visual models from natural language supervision", *Proceedings of
the 38th International Conference on Machine Learning (ICML)*, 18–24 July 2021,
Virtual, 2021, pp. 8748–8763.

[13] Sturm B. L., "A simple method to determine if a music information
retrieval system is a 'horse'", *IEEE Transactions on Multimedia*, vol. 16,
no. 6, 2014, pp. 1636–1644.

[14] Logan B., "Mel frequency cepstral coefficients for music modeling",
*Proceedings of the 1st International Symposium on Music Information Retrieval
(ISMIR)*, 23–25 October 2000, Plymouth, MA, USA, 2000.

[15] Fujishima T., "Realtime chord recognition of musical sound: A system using
Common Lisp Music", *Proceedings of the International Computer Music Conference
(ICMC)*, 22–27 October 1999, Beijing, China, 1999, pp. 464–467.

[16] Jiang D.-N., Lu L., Zhang H.-J., Tao J.-H., Cai L.-H., "Music type
classification by spectral contrast feature", *Proceedings of the IEEE
International Conference on Multimedia and Expo (ICME)*, 26–29 August 2002,
Lausanne, Switzerland, 2002, pp. 113–116.

[17] Bogdanov D., Wack N., Gómez E., Gulati S., Herrera P., Mayor O., Roma G.,
Salamon J., Zapata J., Serra X., "Essentia: An audio analysis library for music
information retrieval", *Proceedings of the 14th International Society for
Music Information Retrieval Conference (ISMIR)*, 4–8 November 2013, Curitiba,
Brazil, 2013, pp. 493–498.

[18] McFee B., Raffel C., Liang D., Ellis D. P. W., McVicar M., Battenberg E.,
Nieto O., "librosa: Audio and music signal analysis in Python", *Proceedings of
the 14th Python in Science Conference (SciPy)*, 6–12 July 2015, Austin, TX,
USA, 2015, pp. 18–24.

[19] Hershey S., Chaudhuri S., Ellis D. P. W., Gemmeke J. F., Jansen A., Moore
R. C., Plakal M., Platt D., Saurous R. A., Seybold B., Slaney M., Weiss R. J.,
Wilson K., "CNN architectures for large-scale audio classification",
*Proceedings of the IEEE International Conference on Acoustics, Speech and
Signal Processing (ICASSP)*, 5–9 March 2017, New Orleans, LA, USA, 2017,
pp. 131–135.

[20] Gemmeke J. F., Ellis D. P. W., Freedman D., Jansen A., Lawrence W., Moore
R. C., Plakal M., Ritter M., "Audio Set: An ontology and human-labeled dataset
for audio events", *Proceedings of the IEEE International Conference on
Acoustics, Speech and Signal Processing (ICASSP)*, 5–9 March 2017, New Orleans,
LA, USA, 2017, pp. 776–780.

[21] Kong Q., Cao Y., Iqbal T., Wang Y., Wang W., Plumbley M. D., "PANNs:
Large-scale pretrained audio neural networks for audio pattern recognition",
*IEEE/ACM Transactions on Audio, Speech, and Language Processing*, vol. 28,
2020, pp. 2880–2894.

[22] Chen K., Du X., Zhu B., Ma Z., Berg-Kirkpatrick T., Dubnov S., "HTS-AT: A
hierarchical token-semantic audio transformer for sound classification and
detection", *Proceedings of the IEEE International Conference on Acoustics,
Speech and Signal Processing (ICASSP)*, 23–27 May 2022, Singapore, 2022,
pp. 646–650.

[23] van den Oord A., Li Y., Vinyals O., "Representation learning with
contrastive predictive coding", *arXiv preprint arXiv:1807.03748*, 2018.

[24] Huang Q., Jansen A., Lee J., Ganti R., Li J. Y., Ellis D. P. W., "MuLan: A
joint embedding of music audio and natural language", *Proceedings of the 23rd
International Society for Music Information Retrieval Conference (ISMIR)*, 4–8
December 2022, Bengaluru, India, 2022, pp. 559–566.

[25] Manco I., Benetos E., Quinton E., Fazekas G., "Contrastive audio-language
learning for music", *Proceedings of the 23rd International Society for Music
Information Retrieval Conference (ISMIR)*, 4–8 December 2022, Bengaluru, India,
2022, pp. 690–697.

[26] Oramas S., Barbieri F., Nieto O., Serra X., "Multimodal deep learning for
music genre classification", *Transactions of the International Society for
Music Information Retrieval*, vol. 1, no. 1, 2018, pp. 4–21.

[27] Berenzweig A., Logan B., Ellis D. P. W., Whitman B., "A large-scale
evaluation of acoustic and subjective music-similarity measures", *Computer
Music Journal*, vol. 28, no. 2, 2004, pp. 63–76.

[28] Bertin-Mahieux T., Ellis D. P. W., Whitman B., Lamere P., "The Million
Song Dataset", *Proceedings of the 12th International Society for Music
Information Retrieval Conference (ISMIR)*, 24–28 October 2011, Miami, FL, USA,
2011, pp. 591–596.

[29] Defferrard M., Benzi K., Vandergheynst P., Bresson X., "FMA: A dataset for
music analysis", *Proceedings of the 18th International Society for Music
Information Retrieval Conference (ISMIR)*, 23–27 October 2017, Suzhou, China,
2017, pp. 316–323.

[30] de Cheveigné A., Kawahara H., "YIN, a fundamental frequency estimator for
speech and music", *Journal of the Acoustical Society of America*, vol. 111,
no. 4, 2002, pp. 1917–1930.

[31] Mauch M., Dixon S., "pYIN: A fundamental frequency estimator using
probabilistic threshold distributions", *Proceedings of the IEEE International
Conference on Acoustics, Speech and Signal Processing (ICASSP)*, 4–9 May 2014,
Florence, Italy, 2014, pp. 659–663.

[32] Salamon J., Gómez E., "Melody extraction from polyphonic music signals
using pitch contour characteristics", *IEEE Transactions on Audio, Speech, and
Language Processing*, vol. 20, no. 6, 2012, pp. 1759–1770.

[33] Sakoe H., Chiba S., "Dynamic programming algorithm optimization for spoken
word recognition", *IEEE Transactions on Acoustics, Speech, and Signal
Processing*, vol. 26, no. 1, 1978, pp. 43–49.

[34] Müller M., *Fundamentals of Music Processing: Audio, Analysis, Algorithms,
Applications*, Springer, Cham, 2015.

[35] Dannenberg R. B., Birmingham W. P., Pardo B., Hu N., Meek C., Tzanetakis
G., "A comparative evaluation of search techniques for query-by-humming using
the MUSART testbed", *Journal of the American Society for Information Science
and Technology*, vol. 58, no. 5, 2007, pp. 687–701.

[36] Ethayarajh K., "How contextual are contextualized word representations?
Comparing the geometry of BERT, ELMo, and GPT-2 embeddings", *Proceedings of
the 2019 Conference on Empirical Methods in Natural Language Processing and the
9th International Joint Conference on Natural Language Processing
(EMNLP-IJCNLP)*, 3–7 November 2019, Hong Kong, China, 2019, pp. 55–65.

[37] Gao J., He D., Tan X., Qin T., Wang L., Liu T.-Y., "Representation
degeneration problem in training natural language generation models",
*Proceedings of the 7th International Conference on Learning Representations
(ICLR)*, 6–9 May 2019, New Orleans, LA, USA, 2019.

[38] Li B., Zhou H., He J., Wang M., Yang Y., Li L., "On the sentence
embeddings from pre-trained language models", *Proceedings of the 2020
Conference on Empirical Methods in Natural Language Processing (EMNLP)*, 16–20
November 2020, Online, 2020, pp. 9119–9130.

[39] Liang V. W., Zhang Y., Kwon Y., Yeung S., Zou J. Y., "Mind the gap:
Understanding the modality gap in multi-modal contrastive representation
learning", *Advances in Neural Information Processing Systems (NeurIPS)*,
vol. 35, 2022, pp. 17612–17625.

[40] Radovanović M., Nanopoulos A., Ivanović M., "Hubs in space: Popular
nearest neighbors in high-dimensional data", *Journal of Machine Learning
Research*, vol. 11, 2010, pp. 2487–2531.

[41] Carbonell J., Goldstein J., "The use of MMR, diversity-based reranking for
reordering documents and producing summaries", *Proceedings of the 21st Annual
International ACM SIGIR Conference on Research and Development in Information
Retrieval*, 24–28 August 1998, Melbourne, Australia, 1998, pp. 335–336.

[42] Ziegler C.-N., McNee S. M., Konstan J. A., Lausen G., "Improving
recommendation lists through topic diversification", *Proceedings of the 14th
International Conference on World Wide Web (WWW)*, 10–14 May 2005, Chiba,
Japan, 2005, pp. 22–32.

[43] Robertson S., Zaragoza H., "The probabilistic relevance framework: BM25
and beyond", *Foundations and Trends in Information Retrieval*, vol. 3, no. 4,
2009, pp. 333–389.

[44] Johnson J., Douze M., Jégou H., "Billion-scale similarity search with
GPUs", *IEEE Transactions on Big Data*, vol. 7, no. 3, 2021, pp. 535–547.

---

# ACKNOWLEDGEMENT

The authors express their sincere gratitude to **Dr S Vigneshwari**, School of
Computer Science and Engineering, Vellore Institute of Technology, Chennai, for
her guidance throughout the Project Based Component of CSE4077 — Recommender
Systems. Her direction on framing the work as a recommender system problem, and
on the standard of evidence expected of its evaluation, shaped the project
substantially.

The authors thank the School of Computer Science and Engineering for providing
the academic environment and resources that made this work possible.

The authors further acknowledge the open-source and open-data communities whose
freely available work made a zero-cost project of this scope feasible: the
LAION team for the publicly released CLAP checkpoints; the maintainers of
librosa, PyAV, FastAPI, React and SQLite; the MetaBrainz Foundation for the
ListenBrainz API; and the contributors to LRCLIB. The authors also thank their
classmates who contributed songs to the curated list used to validate the
query-by-humming component.

---

# APPENDIX 1 — DIRECTORY STRUCTURE

The project directory is zipped and uploaded to LMS in the following structure.

```
Project Root/
│
├── README.txt
│     Project Title : Hummingbird — A Cold-Start Content-Based Music
│                     Recommendation System Using Joint Audio–Language
│                     Embeddings and Query-by-Humming
│     Authors       : Rajaa Sasidharan (23MIA1174)
│                     B. L. Jainth Vaishnav (23MIA1022)
│     Project Mentor: Dr S Vigneshwari
│     Course        : CSE4077 — Recommender Systems, Slot A1+TA1
│
├── Source Codes/
│   ├── backend/
│   │   ├── app/        config.py, models.py, store.py, store_sqlite.py,
│   │   │               store_postgres.py, audio.py, embed.py, features.py,
│   │   │               melody.py, itunes.py, snippets.py, main.py
│   │   └── scripts/    install_gate.py, build_catalog.py, fetch_previews.py,
│   │                   fetch_lyrics.py, build_index.py, evaluate.py,
│   │                   diagnose_embeddings.py, eval_humming.py,
│   │                   precompute_moods.py, migrate_to_supabase.py
│   ├── web/            React + Vite + TypeScript client
│   └── mobile/         Expo React Native client
│
├── Figures/
│   ├── fig_1_1_block_schematic.png
│   ├── fig_3_1_catalogue_composition.png
│   ├── fig_4_1_precision_by_engine.png
│   ├── fig_4_2_catalogue_growth.png
│   ├── fig_4_3_web_song_search.png
│   ├── fig_4_4_web_mood_search.png
│   ├── fig_4_5_web_humming_panel.png
│   ├── fig_4_6_api_documentation.png
│   └── fig_4_7_anisotropy_ablation.png
│
├── Tables/
│   ├── evaluation.json          all precision@k results
│   ├── catalogue_summary.csv    genre distribution and coverage
│   └── ablation_results.csv     checkpoint and anisotropy ablations
│
├── others/
│   ├── README.md                project overview
│   ├── RUN.md                   how to run the system locally
│   ├── DEPLOY.md                deployment notes
│   └── requirements.txt         Python dependencies
│
└── DemoLink.txt                 link to the project demonstration video
```

> **Note.** The course template states that open repositories such as GitHub
> and Zenodo are to be used only after the mentor's approval. The project is
> therefore submitted as a zipped directory, and no public repository has been
> created.

---

# APPENDIX 2 — PROJECT PRESENTATION

The complete project presentation is submitted separately as
`Hummingbird_presentation.pptx` (15 slides, 16:9), covering the problem
statement, literature survey, research gap, system architecture, both
algorithms, evaluation methodology, results, the two ablation findings, and
conclusions with future scope.

---

# APPENDIX 3 — RESEARCH PAPER AND REPORTS

**A. Research Paper.** The research paper written by the team is submitted as
`Hummingbird_paper.docx`, structured in the standard research format: Abstract,
Introduction, Literature Review (44 references), Materials and Methods (problem
description, proposed framework, algorithms), Results and Discussion, and
Conclusion and Future Work.

**B. AI Report.** To be generated via Turnitin and attached as PDF.
Requirement: below 5%.

**C. Plagiarism Report.** To be generated via Turnitin and attached as PDF.
Requirement: below 10%.
