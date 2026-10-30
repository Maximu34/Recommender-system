# Hummingbird: A Cold-Start Music Recommendation System Combining Joint Audio–Language Embeddings with Subsequence Dynamic Time Warping for Query-by-Humming

---

## Authors

**Rajaa Sasidharan**<sup>1</sup>, **B. L. Jainth Vaishnav**<sup>1</sup>

<sup>1</sup> School of Computer Science and Engineering, Vellore Institute of
Technology, Chennai, Tamil Nadu, India

Corresponding author e-mail: attackpirates.226@gmail.com

> *Note for the authors: these details were taken from the course submission
> template (CSE4077 — Recommender Systems, Project Based Component, Dr S
> Vigneshwari). Confirm the spelling of both names and decide which author is
> to be listed as corresponding before submission.*

---

## Abstract

Music recommendation at scale is dominated by collaborative filtering, which
infers taste from the listening behaviour of large user populations. Such
methods fail in two situations that occur constantly in practice: a newly
released or obscure recording has no interaction history and therefore cannot
be recommended, and a listener who remembers only how a song *sounds* — a
fragment of its melody, or an impression of its texture and mood — has no way
of expressing that query to a text-based catalogue search. The first situation
is the cold-start problem; the second is an interface problem that keyword
search cannot solve, because the information the listener holds is acoustic
rather than lexical.

A content-based recommendation system, named Hummingbird, is presented in this
paper to address both situations from the audio signal alone. Three retrieval
paths are unified behind a single application programming interface. First, a
512-dimensional joint audio–language embedding produced by the Contrastive
Language–Audio Pretraining (CLAP) model is used to retrieve acoustically
similar recordings by cosine similarity; because audio and text share one
embedding space, free-text mood queries such as "sad slow piano ballad" are
served by the same index without additional training. Second, a hummed or sung
query is converted to a key-invariant semitone contour by probabilistic YIN
pitch tracking and matched against indexed melodies using subsequence dynamic
time warping, vectorised so that all catalogue melodies are scored in a single
pass. Third, typed titles and remembered lyric fragments are resolved by a
weighted full-text index, with a live metadata fallback and on-demand embedding
for recordings absent from the catalogue. A hand-crafted feature baseline
comprising Mel-frequency cepstral coefficients, chroma, spectral contrast and
tempo is implemented as a controlled comparison arm.

Evaluation was performed on a catalogue of 1,404 recordings spanning 46 genre
labels, using genre-agreement precision@k against a matched random control,
every recording being used in turn as a seed. The learned embedding attained a
precision@5 of 0.337 — a lift of 2.55× over the random control's 0.132 —
against 0.276 for the hand-crafted baseline, a relative advantage of 22%; on
coarse genre families the corresponding figures were 0.537, 0.265 and 0.462.
The learned representation was further found to scale better than the
hand-crafted one: on a 529-recording subset the two were separated by only 7%,
and the margin widened to 22% as the catalogue grew, the baseline's absolute
precision falling while the embedding's held. Two findings beyond the headline
comparison are reported. A
music-specialised CLAP checkpoint was found to be degenerate on this task,
placing 94% of every embedding's energy along a single shared direction,
scoring at chance on coarse genre agreement and returning identical rankings
for four distinct text prompts; a single controlled checkpoint substitution
raised precision@5 from 0.172 to 0.315. Further, anisotropy correction — a
standard remedy in the text-embedding literature — was found to degrade
retrieval monotonically, indicating that the dominant shared direction carries
task-relevant signal and that anisotropy is better treated as a diagnostic
symptom than as a defect to be removed.

**Keywords:** content-based music recommendation; cold-start problem;
contrastive language–audio pretraining; query by humming; subsequence dynamic
time warping; audio embeddings; music information retrieval; embedding
anisotropy

---

## 1. Introduction

The quantity of recorded music available through streaming services has grown
beyond the point at which manual curation or exhaustive browsing is feasible,
and automatic recommendation has consequently become the primary means by which
listeners encounter unfamiliar material [1]. The commercially dominant
technique is collaborative filtering, in which preference is predicted from
patterns of co-consumption across a large user base. Its effectiveness is well
established where interaction data is abundant, but its dependence on that data
is also its principal structural weakness [2].

Two failure modes follow directly from that dependence, and both are
encountered routinely rather than as edge cases.

The first is the cold-start problem. A recording that has just been released,
or that belongs to the long tail of sparsely consumed material, carries little
or no interaction history, and a purely behavioural model therefore has no
basis on which to recommend it [2], [4]. The effect is self-reinforcing:
recommendations are drawn from what is already popular, popularity accrues to
what is recommended, and the long tail is rendered progressively less
discoverable [4]. It has been shown that predicting latent factors directly
from audio content allows recordings with no usage data to be placed in the
same recommendation space as established ones, which makes content analysis the
natural remedy rather than a mere supplement [3].

The second is a query-formulation problem. Catalogue search assumes that the
listener can supply a title, an artist name or a lyric. Frequently that
assumption does not hold. A listener may retain only a melodic fragment, or
only a general impression of instrumentation, texture and mood. Neither is
expressible as a keyword, and both are acoustic in nature. Query-by-humming
systems were proposed to address the melodic case as early as 1995 [8], and
audio fingerprinting solved the related but distinct task of identifying an
exact recording from a short noisy excerpt [9]. Fingerprinting, however, is
deliberately intolerant of variation: it identifies *that* recording and not
one that merely resembles it, which makes it unsuitable for similarity-based
recommendation.

Content-based approaches to music similarity have a long history. Early systems
described audio with hand-crafted descriptors — Mel-frequency cepstral
coefficients borrowed from speech processing [14], chroma vectors capturing
pitch-class distribution [15], and spectral contrast measures distinguishing
harmonic from noise-like spectra [16] — and classified or compared recordings on
those descriptors [7]. Such features remain interpretable and cheap to compute,
and mature implementations are freely available [17], [18]. Their limitation is
that each descriptor encodes a single chosen aspect of the signal, and the
weighting between aspects must be fixed by hand.

Learned audio representations changed that position. Networks trained on
large-scale weakly labelled audio collections [20] produce general-purpose
embeddings that transfer across downstream tasks [19], [21], and transformer
architectures have since improved both accuracy and efficiency on
audio classification [22]. A further development is directly relevant to the
present work: contrastive training against natural-language descriptions, as
introduced for images by CLIP [12] and extended to audio by CLAP [10], [11],
yields a *joint* embedding space in which audio clips and text occupy the same
coordinate system. A free-text description and an audio clip thereby become
directly comparable, and a text-driven mood query requires no separate model.

Despite the availability of these components, their combination into a single
usable system is not straightforward, and several of the difficulties are
empirical rather than architectural. Published checkpoints of nominally
identical architectures differ sharply in retrieval quality. Embedding spaces
can appear healthy by summary statistics while separating nothing. Measured
precision can be inflated by errors in the evaluation ground truth rather than
by genuine retrieval quality. It has been argued at length that music
information retrieval results are frequently accepted without sufficient
examination of whether the system is responding to the intended signal or to an
artefact of the dataset [13].

Accordingly, the contributions of this paper are stated as follows.

1. A unified content-based recommendation system is described in which
   acoustic-similarity retrieval, free-text mood retrieval, lexical title and
   lyric search, and query-by-humming are served from one backend and one
   catalogue, with no reliance on user interaction data.
2. A vectorised formulation of subsequence dynamic time warping over a padded
   melody matrix is presented, by which all catalogue melodies are scored
   simultaneously, reducing hum-matching latency from 2.86 s to 0.53 s.
3. A controlled comparison of a learned joint audio–language embedding against
   a standardised hand-crafted feature baseline is reported on
   genre-agreement precision@k, with a matched random control included so that
   absolute precision cannot be mistaken for retrieval skill.
4. A diagnosis of embedding-space degeneracy in a publicly released
   music-specialised CLAP checkpoint is reported, together with the controlled
   substitution that corrected it.
5. A negative result is reported: anisotropy correction degrades retrieval
   monotonically on the working checkpoint, contradicting the expectation
   transferred from the text-embedding literature.

The remainder of this paper is organised as follows. Section 2 reviews related
work. Section 3 states the problem formally and describes the proposed
framework and its algorithms. Section 4 reports results and discusses them.
Section 5 concludes and identifies directions for extension.

---

## 2. Literature Review

### 2.1 Collaborative filtering and the cold-start problem

Recommendation from interaction data has been studied extensively, and the
conditions under which it fails are well characterised. The cold-start
situation — a user or item for which no interaction history exists — was
formalised together with metrics appropriate to it by Schein et al. [2], who
demonstrated that purely behavioural models cannot rank items they have never
observed being consumed. Celma [4] examined the consequence at catalogue scale,
showing that recommendation systems optimised on aggregate behaviour
concentrate exposure on a small head of popular items and leave the long tail
effectively invisible. Surveys of the field have repeatedly identified
cold-start handling and the incorporation of content and context as open
problems rather than settled ones [1], [5], [6].

The most influential response within the music domain was presented by van den
Oord et al. [3], in which a convolutional network was trained to predict the
latent item factors of a collaborative filtering model directly from audio
spectrograms. Recordings without usage data could then be embedded into the
same latent space as recordings with it. That work established audio content
analysis as the principal mechanism by which the music cold-start problem is
addressed, and the present system follows the same premise, differing in that
no collaborative model is assumed to exist at all.

### 2.2 Hand-crafted audio descriptors

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
are available in Essentia [17] and librosa [18], the latter being used in the
present work.

A methodological point concerning these features is relevant to the results
reported in Section 4. The components of a concatenated descriptor vector
occupy very different numerical ranges — cepstral coefficients extend to the
hundreds while chroma values are bounded in [0, 1] — and a distance computed
over the raw concatenation is therefore dominated by whichever component has
the largest scale. Per-dimension standardisation is consequently a
precondition for a fair baseline rather than an optional refinement.

### 2.3 Learned audio representations

Representation learning displaced hand-crafted descriptors for most audio
tasks. The release of AudioSet, a large ontology-structured and
human-labelled collection of audio events [20], made supervised pretraining at
scale practical. Hershey et al. [19] examined convolutional architectures on
that collection and showed that the resulting embeddings transferred to
downstream tasks, and Kong et al. [21] extended this with pretrained audio
neural networks trained for general audio pattern recognition. Chen et al. [22]
subsequently introduced a hierarchical token-semantic audio transformer that
improved both classification accuracy and computational efficiency, and that
architecture serves as the audio encoder of the CLAP checkpoints employed in
this work.

In parallel, self-supervised contrastive objectives were shown to produce
useful representations without labels. Contrastive predictive coding [23]
established the general formulation of learning by discriminating true future
or paired observations from negatives drawn within a batch, which underlies the
contrastive audio–text objectives discussed next.

### 2.4 Joint audio–language embedding

The decisive development for the present system is the construction of a shared
embedding space for audio and natural language. CLIP [12] demonstrated for
images that training an image encoder and a text encoder jointly on paired data
with a contrastive objective yields a space supporting zero-shot
classification by text prompt. Elizalde et al. [11] transferred the approach to
audio under the name CLAP, and Wu et al. [10] scaled it substantially, adding
feature fusion for variable-length inputs and keyword-to-caption augmentation to
expand the available training pairs; the publicly released LAION-CLAP
checkpoints from the latter work are those used here.

Within the music domain specifically, MuLan [24] learned a joint embedding of
music audio and free-form text from a very large corpus of weakly paired
examples, and MusCALL [25] applied contrastive audio–language learning to
music retrieval, demonstrating text-to-music and music-to-text retrieval.
Multimodal combinations of audio with text and images have likewise been shown
to improve genre classification over audio alone [26]. These results collectively
establish that a single contrastively trained space can serve both
audio-similarity and text-query retrieval, which is the property the present
system exploits to obtain mood search without a second model.

### 2.5 Query by humming

The retrieval of a recording from a sung or hummed rendition was proposed by
Ghias et al. [8], who converted a hummed query to a sequence of relative pitch
transitions and matched it approximately against a database of melodies. The
central difficulty identified then remains the central difficulty now: an
untrained singer renders a melody with errors of absolute pitch, local timing
and global tempo, so the matching procedure must be invariant to transposition
and tolerant of temporal distortion. A comparative evaluation of the main
families of search technique for this task was later conducted on a common
testbed by Dannenberg et al. [35].

Reliable pitch tracking is the first requirement. The YIN estimator [30]
established an autocorrelation-based method with substantially reduced octave
error, and the probabilistic variant pYIN [31] replaced YIN's fixed threshold
with a distribution over candidate thresholds, producing multiple pitch
candidates per frame that are then decoded by a hidden Markov model; the latter
is used in the present work for both query and reference. Melody extraction
from genuinely polyphonic material is harder still, and has been addressed by
tracking and characterising pitch contours [32].

The matching step is conventionally dynamic time warping, whose formulation for
speech recognition by Sakoe and Chiba [33] remains the reference. For the
present task plain end-to-end warping is inappropriate, since a short hum
corresponds to a brief passage located somewhere within a longer reference. The
required variant is subsequence dynamic time warping, in which the alignment is
permitted to begin and end at any position in the reference; the formulation
and its step-pattern design are treated systematically by Müller [34].

### 2.6 Embedding geometry: anisotropy and hubness

Two geometric pathologies of high-dimensional learned representations are
relevant to the diagnostic findings reported in Section 4.

Anisotropy — the concentration of embeddings within a narrow cone rather than
their distribution across the space — was measured in contextual word
representations by Ethayarajh [36], who found high average cosine similarity
between unrelated inputs. Gao et al. [37] analysed the training dynamics that
produce this degeneration, and Li et al. [38] proposed transforming the
resulting distribution towards isotropy, reporting improved semantic textual
similarity. The expectation transferred from this literature is that correcting
anisotropy improves retrieval; Section 4 reports that on the present task it
does not. A related phenomenon specific to multimodal contrastive models is the
modality gap, in which audio and text embeddings occupy separated regions of
the nominally shared space [39].

Hubness is the second pathology: in high-dimensional spaces a small number of
points appear in the nearest-neighbour lists of disproportionately many
queries, which distorts retrieval independently of representation quality
[40]. Both pathologies motivate the position taken in this work that an
embedding index must be diagnosed before it is trusted, a position consistent
with broader criticism of insufficiently examined music information retrieval
results [13].

### 2.7 Retrieval, diversification and evaluation

Lexical retrieval over titles, artists and lyrics is a probabilistic ranking
problem for which BM25 and its field-weighted extensions are standard [43]. The
ranked list returned by a similarity search tends towards redundancy, since
near-duplicates of the seed occupy the top positions; maximal marginal
relevance [41] and topic diversification [42] are the established remedies, and
the former is implemented here as an optional re-ranking stage. At catalogue
sizes beyond the present scale, exhaustive cosine computation becomes
impractical and approximate nearest-neighbour indexing is required [44].

Evaluation of music similarity without ground-truth similarity judgements is
itself a research problem. Berenzweig et al. [27] compared acoustic similarity
measures against subjective human judgements and quantified the gap between
them. Public datasets with usable metadata, notably the Million Song Dataset
[28] and the Free Music Archive dataset [29], have made comparable evaluation
possible. Genre agreement remains the most widely used proxy, and its weakness
is understood: two recordings sharing a broad genre label may sound entirely
unalike. Sturm [13] demonstrated that systems can achieve strong figures on
such proxies while responding to confounds rather than to musical content,
which is the reason a random control is reported alongside every precision
figure in Section 4.

### 2.8 Summary of the identified gap

The components surveyed above are individually mature. What is not commonly
reported is their integration into a single cold-start system in which one
embedding index serves both audio-similarity and text-mood retrieval while a
separate melodic index serves hummed queries, evaluated with an explicit random
control, and accompanied by the diagnostic evidence that the embedding space in
use is not degenerate. The frequency with which published checkpoints are
adopted without such verification, together with the magnitude of the error
observed here when verification was omitted, is the practical gap this work
addresses.

---

## 3. Materials and Methods

### 3.1 Problem Description

Let a catalogue be a finite set of recordings $T = \{t_1, t_2, \ldots, t_N\}$.
For each recording a short audio excerpt $a_i$ is available, together with
metadata comprising title, artist, album, genre label and, where obtainable,
lyrics. No user, no user identifier and no interaction history is assumed to
exist. The system must therefore operate entirely on content, which places it
in the permanent cold-start regime described in Section 2.1.

Three retrieval tasks are defined over this catalogue.

**Task 1 — acoustic similarity.** Given a seed recording $t_s \in T$, return a
ranked list of $k$ recordings from $T \setminus \{t_s\}$ ordered by perceptual
similarity of sound: instrumentation, texture, energy and mood. Similarity is
continuous rather than binary, so the required output is a ranked truncation
rather than a set of matches.

**Task 2 — text-conditioned retrieval.** Given a free-text description $q$ of a
desired sound, such as "heavy distorted guitar", return a ranked list of $k$
recordings whose audio corresponds to that description. No fixed vocabulary of
moods or tags is assumed.

**Task 3 — melodic identification.** Given a recording $h$ of a human humming,
singing or whistling a melody, identify the recording in $T$ from which that
melody originates. The query is monophonic, the reference is polyphonic, the
absolute pitch is arbitrary, the tempo is approximate, and the query
corresponds to an unknown short interval of the reference.

A fourth, lexical task is also required for the system to be usable: given a
typed string that may be a title, an artist name or a remembered lyric
fragment, the intended recording must be identified and returned *before* its
acoustic neighbours. This distinction matters in practice, because a user who
types a title expects that title, and routing such a query through a semantic
text encoder returns plausible but incorrect recordings.

Two constraints are imposed by the deployment context. First, no component may
require paid infrastructure or an authenticated third-party key. Second, audio
must not be redistributed; only metadata and references to the rights holder's
own preview endpoint may be served.

### 3.2 Proposed Framework

The proposed framework is organised as an offline indexing pipeline and an
online query service, as shown in Figure 1.

**Figure 1.** Architecture of the proposed system.

```
OFFLINE INDEXING                              ONLINE QUERY SERVICE
─────────────────────────                     ──────────────────────────────
catalogue assembly                            typed title / lyric
  (popularity feed + curated list)              │
        │                                        ├─► weighted full-text index
        ▼                                        │     (title ≫ artist ≫ lyrics)
metadata resolution ──► preview URL,             │          │
  (artist verification)   genre, artwork         │          ▼
        │                                        │   live metadata fallback
        ▼                                        │   + on-demand embedding
excerpt download (30 s)                          │          │
        │                                        ▼          ▼
        ├──► CLAP audio encoder ──► 512-d ──┐  seed recording
        │      (10 s windows, mean-pooled)   │       │
        │                                    │       ▼
        ├──► baseline features ──► 87-d ─────┼─► cosine similarity
        │      (MFCC/chroma/contrast/tempo)  │   + optional MMR re-ranking
        │                                    │       │
        └──► pYIN contour ──► melody index ──┤       ▼
                                             │   ranked recommendations
free-text mood query                         │
        │                                    │
        └──► CLAP text encoder ──► 512-d ────┘
                                             
hummed query ──► pYIN contour ──► subsequence DTW ──► identified recording
```

#### 3.2.1 Catalogue assembly

The catalogue is assembled from two sources. A keyless popularity feed supplies
broadly known recordings, and a manually curated list supplies recordings that
the evaluators are able to sing from memory. The second source is not
decorative: query-by-humming can only be evaluated on recordings the evaluator
already knows, so the presence of such recordings in the catalogue is a
precondition for the humming evaluation being valid rather than circular. The
curated list additionally counters the sampling bias of the popularity feed,
which reflects the demographics of one particular listening platform.

Each title is resolved through a keyless metadata search interface to obtain a
30-second preview excerpt, a genre label and cover artwork. Resolution is
verified rather than assumed: the first returned result is accepted only if its
artist name shares at least one normalised token with the requested artist. The
necessity of this check is quantified in Section 4.1.

#### 3.2.2 Audio representation

Two representations are computed for every excerpt, so that the learned and
hand-crafted approaches may be compared on identical audio under identical
evaluation conditions.

The **learned representation** is produced by the audio encoder of the
LAION-CLAP model [10], specifically the `clap-htsat-unfused` checkpoint, whose
audio branch is the hierarchical token-semantic audio transformer of Chen et
al. [22]. Each excerpt is divided into consecutive non-overlapping windows of
10 s; windows are embedded independently and the resulting 512-dimensional
vectors are averaged, after which the mean vector is $L_2$-normalised. Three
properties of this procedure are deliberate. Only whole windows are used, since
appending a zero-padded tail window caused the stored index to disagree with
vectors computed at query time. Truncation is deterministic rather than
random, so that embedding the same excerpt twice yields the identical vector.
The feature-fusion input flag is held false, because the checkpoint in use was
not trained with the fusion branch enabled and activating it routes audio
through untrained parameters.

The **hand-crafted baseline** is an 87-dimensional vector formed by
concatenating the per-dimension mean and standard deviation of 20 Mel-frequency
cepstral coefficients (40 values), of a 12-bin constant-Q chroma (24 values)
and of 7-band spectral contrast (14 values), together with the mean and
standard deviation of spectral centroid, spectral roll-off, zero-crossing rate
and root-mean-square energy (8 values), and a single tempo estimate. Every
dimension is standardised to zero mean and unit variance across the catalogue
before any distance is computed, for the reason given in Section 2.2.

Interpretable descriptors — tempo in beats per minute, estimated key by the
Krumhansl–Schmuckler profile correlation method, spectral centroid as a
brightness proxy, and root-mean-square energy — are additionally stored so that
the user interface can state why two recordings were judged similar.

#### 3.2.3 Similarity search and diversification

All embeddings are $L_2$-normalised and held in memory as a dense matrix
$M \in \mathbb{R}^{N \times d}$. Cosine similarity against a query vector
reduces to a single matrix–vector product, which is sub-millisecond at the
present catalogue size. Approximate nearest-neighbour indexing [44] was
therefore not adopted, as it would introduce a dependency and an approximation
for no measurable latency benefit below approximately $10^5$ recordings.

Because audio similarity is dominated by near-duplicates — alternative mixes,
live versions and the same artist's adjacent releases — an optional maximal
marginal relevance re-ranking stage [41] is provided, trading a controllable
quantity of relevance for diversity in the returned list.

#### 3.2.4 Text-conditioned retrieval

Since the CLAP audio and text encoders share one embedding space, a free-text
query is embedded by the text encoder and used directly as the query vector
against the same audio matrix. No separate tag vocabulary, classifier or
training step is required. For deployment without the model weights present, a
small set of text vectors for common mood prompts is precomputed offline and
served from disk.

#### 3.2.5 Lexical retrieval with live fallback

Typed queries are resolved by a full-text index with field weighting such that
a title match outranks an artist match, which in turn outranks a lyric match.
Two storage backends are implemented behind one interface and verified to agree:
an embedded engine using FTS5 with BM25 field weights of 10.0, 4.0 and 1.0 for
title, artist and lyrics respectively, and a server engine using a generated
weighted `tsvector` with weight classes A, B and C. Field weighting is
necessary and not cosmetic: without it, a query naming an artist returns that
artist's name before a recording whose *title* is the query string.

When no title match is found locally, the query is forwarded to the live
metadata interface. A live result is accepted as the intended recording only if
every token of the query appears in the returned title, this threshold being
stricter than the artist check of Section 3.2.1 because a live result is
presented to the user as the song requested. An accepted live result is
returned immediately and its excerpt is embedded in a background task, so that
the recording becomes part of the similarity index for subsequent queries.
Transport failure is distinguished from genuine absence, so that a rate-limited
lookup is not reported to the user as a non-existent recording.

#### 3.2.6 Melodic representation and matching

An identical contour-extraction procedure is applied to indexed excerpts and to
hummed queries, so that the two are comparable. Fundamental frequency is
estimated per frame by pYIN [31] with a hop of 512 samples. Voiced frames are
retained and the voiced fraction is recorded, this fraction being the criterion
by which percussion-only and ambient material — which no hum could ever match —
is excluded from the melody index. Frequencies are converted to MIDI semitones,
short unvoiced gaps arising from breaths and consonants are bridged by linear
interpolation, a 5-frame median filter suppresses isolated estimation errors,
and the median semitone value is subtracted to render the contour invariant to
transposition. The contour is finally resampled to a fixed frame rate so that
query and reference share a time base.

For a hummed query the pitch search is restricted to 80–600 Hz at coarser
resolution, which is appropriate for a single voice and substantially faster;
indexed polyphonic excerpts require the full search range.

Matching uses subsequence dynamic time warping [34] with a step pattern whose
three permitted moves — $(i-1, j)$, $(i-1, j-1)$ and $(i-1, j-2)$ — all advance
the query index by exactly one frame. This restriction is what makes the
procedure fast enough to be interactive, and the reasoning is given with the
algorithm in Section 3.3.2. The first row of the cost matrix is initialised to
the raw local distances, which permits the alignment to begin anywhere in the
reference, and the returned cost is the minimum over the final row, which
permits it to end anywhere. Each query is additionally evaluated at five global
tempo scalings, $\{0.7, 0.85, 1.0, 1.2, 1.5\}$, and the best cost retained, so
that a singer taking the melody uniformly faster or slower is accommodated.

### 3.3 Algorithm

#### 3.3.1 Algorithm 1: Unified query resolution

```
Algorithm 1  RESOLVE-QUERY
Input :  query q (typed string, free text, or audio recording)
         query mode m ∈ {TITLE, MOOD, HUM}
         result count k, diversity parameter λ
Output:  seed recording s (may be null), ranked list R of k recordings

 1  if m = TITLE then
 2      H ← FULLTEXT-SEARCH(q)                       // weighted: title ≫ artist ≫ lyrics
 3      titleHit ← ∃ h ∈ H such that MATCHED-FIELD(h, q) = title
 4      if H = ∅ or ¬titleHit then
 5          try
 6              L ← LIVE-LOOKUP(q)                   // external metadata interface
 7              if L ≠ null and ∀w ∈ TOKENS(q): w ∈ TOKENS(TITLE(L)) then
 8                  s ← INSERT-TRACK(L)
 9                  spawn EMBED-AND-INDEX(s)          // background task
10                  return (s, first 3 elements of H) // neighbours follow once embedded
11          catch Unavailable                          // rate limited, not absent
12              if H = ∅ then return (null, ∅) with transport-failure flag
13      s ← first element of H
14  else if m = MOOD then
15      v ← CLAP-TEXT-ENCODE(q)                       // same space as audio
16      return (null, RANK(v, k, λ))
17  else                                              // m = HUM
18      (c, voiced) ← EXTRACT-CONTOUR(q, monophonic = true)
19      s ← argmin over t ∈ MelodyIndex of DTW-COST(c, t)     // Algorithm 2
20
21  v ← EMBEDDING(s)
22  if v = null then return (s, ∅) with indexing-in-progress flag
23  return (s, RANK(v, k, λ))
24
25  procedure RANK(v, k, λ)
26      v ← v / ‖v‖₂
27      sim ← M · v                                   // one matrix–vector product
28      C ← indices of the 3k highest entries of sim  // candidate pool
29      if λ = 0 then return first k elements of C
30      R ← ∅                                          // maximal marginal relevance
31      while |R| < k do
32          c* ← argmax over c ∈ C∖R of
33                   (1 − λ)·sim[c] − λ·max over r ∈ R of (M[c] · M[r])
34          R ← R ∪ {c*}
35      return R
```

The ordering of lines 1–13 encodes a requirement established during
development. A lexical hit must be preferred whenever the typed string matches
a title, and the live fallback must be consulted when it does not — but a
transport failure at line 11 must not be allowed to discard a usable local
result, which is the behaviour that caused a correct lyric search to return
nothing while the external interface was rate limited.

#### 3.3.2 Algorithm 2: Vectorised subsequence DTW over all melodies

```
Algorithm 2  MELODY-MATCH
Input :  query contour c ∈ ℝⁿ (semitones, median-subtracted)
         reference matrix R ∈ ℝ^(N×W)  (N contours, right-padded with PAD = 10⁶)
         true lengths ℓ ∈ ℕᴺ, result count k
         tempo scales S = {0.7, 0.85, 1.0, 1.2, 1.5}
Output:  k recordings of lowest alignment cost

 1  best ← (∞, ∞, …, ∞)                               // one entry per recording
 2  for each σ ∈ S do
 3      c' ← RESAMPLE(c, round(n · σ))                 // global tempo variation
 4      n' ← length(c')
 5      D ← |R − c'[0]|                                // row 0: free start anywhere
 6      for i ← 1 to n' − 1 do
 7          E ← |R − c'[i]|                            // local distance, all refs at once
 8          A ← SHIFT-RIGHT(D, 1), with column 0 ← PAD        // move (i−1, j−1)
 9          B ← SHIFT-RIGHT(D, 2), with columns 0,1 ← PAD     // move (i−1, j−2)
10          D ← E + min(D, A, B)                       // elementwise over N×W
11      mask ← [ j < ℓ[r] ] for all r, j                // ignore padding
12      cost ← min over valid j of D[r, j] / n'         // free end anywhere
13      cost[r] ← ∞ wherever ℓ[r] < n'/2                // reference too short to contain query
14      best ← min(best, cost)
15  return the k recordings with smallest best
```

Two design choices in Algorithm 2 are responsible for its tractability.

First, every permitted move advances the query index $i$ by exactly one frame.
Row $i$ of the cost matrix therefore depends only on row $i-1$, never on
another cell of row $i$ itself. Had a horizontal move $(i, j-1)$ been admitted,
each row would depend on its own earlier columns, the inner loop would be
forced to proceed cell by cell in sequence, and the computation could not be
expressed as array operations.

Second, all reference contours are packed into one padded matrix, so that line
10 advances the recurrence for every catalogue recording simultaneously. The
only remaining interpreted loop is over the query's frames, of which there are
typically about sixty. Scoring recordings individually was measured at
approximately 43 ms each, which exceeds an interactive budget at a few hundred
recordings; the vectorised formulation reduced end-to-end hum latency from
2.86 s to 0.53 s. Padding is filled with a value large enough that a padded
cell can never win the minimum at line 10, and line 11 additionally restricts
the free-end minimisation to each reference's true length.

### 3.4 Implementation and Experimental Setup

The backend is implemented in Python using FastAPI, serving JSON only; audio is
streamed to the client directly from the rights holder's own preview endpoint,
so that no audio is redistributed and no object storage is required. Audio
decoding uses PyAV, which bundles its own decoders and therefore handles the
AAC excerpts and browser-recorded Opus without a system-level codec
installation. Feature extraction uses librosa [18]. Embeddings are stored as
dense arrays on disk and loaded into memory at startup. Metadata is stored
behind an interface with two interchangeable implementations, an embedded
engine used for all reported measurements and a hosted server engine used for
deployment, verified to return identical search results. Client applications
were implemented for the browser and for mobile.

Evaluation is reported as genre-agreement precision@k: each catalogue recording
is used in turn as a seed, and the proportion of its top-$k$ neighbours sharing
the seed's genre label is averaged over all seeds. Scores are computed against
the raw metadata labels ("fine") and against coarse genre families, since the
fine labels distinguish categories that are not acoustically distinct. A random
control — $k$ recordings drawn uniformly from the catalogue — is reported for
every configuration, and lift over that control is treated as the primary
quantity. The control is necessary because absolute precision is determined
largely by the catalogue's genre distribution: in a catalogue that is 40% one
genre, a random recommender attains 0.40 by accident.

---

## 4. Results and Discussion

Unless stated otherwise, all figures in this section were measured on the full
catalogue of 1,404 recordings, of which 1,403 carry a playable excerpt, with
every recording used in turn as a seed. Where a figure is quoted from the
earlier 529-recording catalogue — which is the case for the ablation of Section
4.4 and for the comparisons that trace the effect of catalogue growth — the
catalogue size is given explicitly alongside it.

### 4.1 Catalogue quality as a precondition for valid evaluation

Metadata resolution was found to be a substantial and initially invisible source
of error. Across 759 cached resolutions performed without artist verification,
63 — that is, **8.3%** — returned a recording whose artist name shared no token
with the requested artist. Representative failures are given in Table 1.

**Table 1.** Representative metadata resolution failures before artist
verification.

| Requested | Returned |
|---|---|
| Boulevard of Broken Dreams (Green Day) | lullaby cover by Sparrow Sleeps, labelled *Children's Music* |
| Nuts RM | White Sand — Migos |
| out of love RM | Call Out My Name — The Weeknd |
| Change pt.2 RM | BUTTERFLY EFFECT — Travis Scott |
| Into the Sun BTS | Into The Sun — Robyn |

The failures were concentrated in one part of the catalogue and were absent
from the curated list, of which 73 of 74 entries resolved to the correct
artist. Each mis-resolved entry corrupts three things simultaneously: the stored
embedding describes audio that is not the recording the row claims to be; the
genre label used as evaluation ground truth belongs to a different recording;
and a user who searches the title is served different music. The third is a
visible defect, but the second is the more damaging, because it silently
degrades the metric by which the system is judged.

Introducing the artist-token verification of Section 3.2.1 caused 71 cached
resolutions to be discarded and re-fetched, 731 verified answers being retained
so that the re-resolution cost minutes rather than the hour a full refetch
would have required. On the 529-recording catalogue then in use, the correction
raised measured precision@5 for both engines — the learned embedding from 0.295
to 0.332 and the baseline from 0.256 to 0.310. The random control, however,
rose in parallel, from 0.122 to 0.154, because removing mis-resolved oddities
left a catalogue of narrower genre diversity. **Lift over the random control
therefore fell slightly even as absolute precision improved.** This is reported
in preference to quoting whichever of the two figures is more favourable, and it
illustrates concretely why the control column is not optional.

A second class of catalogue defect was identified subsequently. Non-musical
recordings — white-noise, rainfall and tone-generator tracks — rank highly in
popularity feeds because listeners leave them playing for hours, and one such
recording was returned first for a chill lo-fi mood query. Five such entries
were identified in 1,409 and removed. The removal rule was deliberately matched
on artist name alone: an initial scan matching title keywords implicated
fourteen recordings, but nine of those belonged to the bands Sleep Token and
Sleep Theory and were genuine music. The initial count was therefore an
overstatement, and the stricter artist-only rule removed the five genuine
cases while leaving both bands intact.

### 4.2 Retrieval accuracy

Genre-agreement precision on the full catalogue of 1,404 recordings and 46
genre labels is reported in Table 2, with every recording used as a seed.

**Table 2.** Genre-agreement precision@k on the 1,404-recording catalogue. Lift
is relative to the random control.

| Engine | P@5 (fine) | lift | P@10 (fine) | P@5 (coarse) | lift | P@10 (coarse) |
|---|---|---|---|---|---|---|
| CLAP `clap-htsat-unfused` | **0.337** | **2.55×** | 0.321 | **0.537** | **2.03×** | 0.522 |
| Baseline (MFCC/chroma, standardised) | 0.276 | 2.08× | 0.255 | 0.462 | 1.74× | 0.447 |
| Random control | 0.132 | 1.00× | 0.129 | 0.265 | 1.00× | 0.261 |

Both engines clearly exceed the random control, which establishes that genuine
acoustic structure is being retrieved rather than the catalogue's genre prior.
The learned embedding leads the hand-crafted baseline by 22% relative on fine
labels and 16% on coarse families, and exceeds the control by a factor of 2.55.

The behaviour of that margin under catalogue growth is the more informative
result, and it is summarised in Table 3. Three separate conditions have now
been measured. On the 529-recording catalogue with uncorrected metadata the
learned embedding led the baseline by 15%. On the same catalogue with metadata
corrected, the gap narrowed to 7%, indicating that a substantial part of the
embedding's apparent advantage had been an artefact of noisy ground truth. On
the 1,404-recording catalogue the gap widened again to 22% — but by a different
mechanism: the embedding's absolute precision was essentially unchanged
(0.332 to 0.337) whereas the baseline's *fell* (0.310 to 0.276).

**Table 3.** Effect of catalogue correction and catalogue growth on the gap
between engines, precision@5 on fine genre labels.

| Condition | CLAP | Baseline | Random | CLAP lead | CLAP lift |
|---|---|---|---|---|---|
| 529 recordings, uncorrected metadata | 0.295 | 0.256 | 0.122 | 15% | 2.42× |
| 529 recordings, corrected metadata | 0.332 | 0.310 | 0.154 | 7% | 2.16× |
| 1,404 recordings, corrected metadata | 0.337 | 0.276 | 0.132 | 22% | 2.55× |

The interpretation offered is that the hand-crafted descriptors scale less well
than the learned embedding. A fixed 87-dimensional vector of spectral and
rhythmic summary statistics is adequate for separating a few hundred recordings
across a handful of broad genres, but as the catalogue triples in size and the
label set broadens to 46 genres, the number of recordings that happen to share
similar summary statistics while sounding quite different grows faster than the
descriptor's capacity to distinguish them. The learned embedding, trained
against natural-language descriptions of a far larger and more varied audio
corpus, does not degrade in the same way.

Two cautions are attached to this interpretation. First, the random control
fell from 0.154 to 0.132 between the two catalogue sizes, reflecting the wider
genre spread of the larger catalogue, so part of the increase in *lift* is
attributable to the control becoming harder rather than to either engine
improving. The baseline's fall in absolute precision, however, cannot be
explained that way. Second, a single pair of catalogue sizes does not establish
a scaling law, and the claim is therefore stated as the direction of an
observed effect rather than as a quantified relationship.

The defensible overall claim is that a contrastively trained audio embedding
outperforms well-standardised hand-crafted descriptors on this task, that the
margin is modest at small catalogue sizes, and that it widens as the catalogue
grows because the baseline deteriorates rather than because the embedding
improves.

Qualitative behaviour is consistent with the metric. A jazz seed returns jazz;
a grunge seed returns alternative rock of comparable era and distortion; a
piano-led ballad returns other piano-led ballads across nominally different
genres, which is a case where the genre proxy *understates* retrieval quality.
Text queries behave as the shared embedding space predicts, with "jazz
saxophone and piano", "heavy distorted guitar" and "sad slow piano ballad"
each returning appropriate recordings without any tag vocabulary having been
defined.

### 4.3 Diagnosis of a degenerate embedding checkpoint

The most consequential finding of this work concerns checkpoint selection
rather than architecture.

The first embedding index built returned Billie Jean as the nearest neighbour
of Take Five at cosine 0.992, with essentially all pairs scoring near 0.99.
High similarity across unrelated material is the signature of a collapsed
space, and four distinct faults were identified by measurement. Three were
implementation errors: the baseline features had never been standardised
(precision@5 0.138 → 0.245 once corrected); the variable-length input flag was
set true, routing audio through a feature-fusion branch the checkpoint had never
trained (mean pairwise cosine 0.92 → 0.73 once disabled); and random truncation
meant that embedding the same excerpt twice produced different vectors,
corrected by deterministic mean-pooled windows.

The fourth fault dominated. The `larger_clap_music` checkpoint — selected
initially on the reasonable assumption that a music-specialised model would
suit a music task — proved degenerate on this task. **94% of every embedding's
energy lay along a single shared direction.** The checkpoint scored *exactly at
chance* on coarse genre agreement, and all four distinct text prompts returned
an identical ranking, which is the clearest possible demonstration that the
space separated nothing. Substituting `clap-htsat-unfused` as a single
controlled change, with identical excerpts and identical code, moved
precision@5 from 0.172 to 0.315 and text discrimination from one distinct
ranking out of four to four out of four.

The practical lesson is that a published checkpoint's name and stated training
domain are not evidence of its fitness, and that high cosine similarity figures
can conceal a space with no discriminative structure. A diagnostic procedure —
mean-vector norm, pairwise similarity distribution, and distinctness of
rankings across unrelated text prompts — was implemented as a standing check
and is the mechanism by which the fault was finally localised.

### 4.4 Anisotropy correction: a controlled negative result

On the working checkpoint, anisotropy remains high at 0.853. The text-embedding
literature would suggest correcting it [36], [37], [38]. Four variants were
therefore evaluated, with results in Table 4.

**Table 4.** Effect of anisotropy correction on retrieval, 529-recording
catalogue.

| Variant | P@5 (fine) | P@5 (coarse) |
|---|---|---|
| As produced by the model | **0.315** | **0.476** |
| Mean-centred | 0.299 | 0.468 |
| Mean-centred, top-1 principal component removed | 0.290 | 0.420 |
| Mean-centred, top-2 principal components removed | 0.251 | 0.355 |

Retrieval degrades monotonically as correction is strengthened. The dominant
shared direction therefore carries task-relevant signal in this setting rather
than constituting nuisance variance, and the remedy transferred from the
sentence-embedding literature is actively harmful here. Anisotropy is
nonetheless worth *measuring*: it is precisely the statistic that exposed the
degenerate checkpoint of Section 4.3. The conclusion drawn is that anisotropy
should be treated as a diagnostic symptom rather than as a defect to be
corrected reflexively, and embeddings are consequently used as the model
produces them.

### 4.5 Query-by-humming performance

Hum matching is the weakest component of the system and is reported as such. An
**upper bound** was measured using synthesised "perfect hums" — monophonic
renditions derived from the reference contours themselves, free of the pitch
and timing error a human introduces. Under those conditions 8 of 25 queries
placed the correct recording in the top 10 against a 479-melody index, at a
median latency of 0.93 s.

This figure is an upper bound and not a performance estimate: genuine human
hums can only score lower. It was measured against a 479-melody index; the
melody index has since grown to 1,346 of the catalogue's 1,403 playable
recordings, the remainder having been excluded by the voiced-ratio filter of
Section 3.2.6 as percussion-only or ambient material that no hum could match.
A larger index can only make the task harder, so the upper bound has not been
re-measured upward.

Reported as such, the figure indicates that the melodic
component is substantially less reliable than the acoustic-similarity
component, and that the limitation is one of matching accuracy rather than of
latency, the latter having been addressed by the vectorisation of Section
3.3.2. A plausible cause is that contours extracted from polyphonic mixtures by
a monophonic pitch tracker are a poor representation of the sung melody, since
the tracker may follow a bass line or an accompanying instrument rather than
the vocal; dedicated polyphonic melody extraction [32] is the indicated
remedy.

### 4.6 Lexical retrieval

Lexical search operates as specified. Of 1,404 catalogue recordings, 1,354 —
that is, 96% — carried lyrics, obtained from a keyless community lyrics
interface; of the remainder, 20 were identified as instrumental and 50 were
simply absent from that source. Recordings are locatable by title, by artist,
or by a remembered line, with the matched line returned so that the user can
see why a recording was retrieved. Field weighting was found to be necessary
rather than
cosmetic: before weights were applied, a query consisting of an artist's name
returned biographical artist matches ahead of a recording whose title was the
query string itself.

The live fallback measurably extends coverage. A recording absent from the
catalogue is resolved through the external metadata interface, returned
immediately, embedded in the background, and is available to
acoustic-similarity queries within seconds — demonstrated with a J-Pop
recording that was not present in the catalogue minutes earlier and that,
once embedded, returned four acoustically plausible rock and alternative
neighbours at cosine 0.95–0.96.

### 4.7 Comparison with existing approaches and limitations

Relative to collaborative filtering, the proposed system requires no
interaction data and therefore has no cold-start exclusion: every recording in
the catalogue is recommendable from the moment its excerpt is analysed, and a
recording absent from the catalogue entirely can be admitted at query time.
Relative to audio fingerprinting [9], which identifies an exact recording from
an exact excerpt, the present system retrieves *similar* recordings and accepts
an imprecise sung query. Relative to systems built solely on hand-crafted
descriptors [7], [14], [15], [16], a measurable if modest improvement is
obtained, and free-text mood retrieval is obtained essentially without
additional cost, which a descriptor-based system cannot provide at all without
a separately trained tag model.

The limitations are stated plainly.

1. **Metric validity.** Genre agreement is a proxy. Two acoustically dissimilar
   recordings sharing a genre label count as a hit, and two similar recordings
   with different labels count as a miss. A human listening study — the
   appropriate instrument — has been designed but not yet conducted, and no
   result from it is claimed here.
2. **Catalogue scale.** The reported figures are drawn from 1,404 recordings,
   which is three orders of magnitude below a commercial catalogue.
   Conclusions at this scale are indicative rather than definitive, and the
   scaling effect reported in Section 4.2 rests on two catalogue sizes only.
3. **Humming accuracy.** As reported in Section 4.5, the melodic component is
   weak, and the figure quoted is an upper bound obtained on synthesised rather
   than human queries.
4. **Excerpt length.** Analysis is performed on 30-second preview excerpts
   rather than complete recordings, so structural variation outside the excerpt
   is not represented.
5. **Cover-version ranking.** A typed title carries no artist, and cover
   versions are consequently observed to outrank originals for some queries.
   Popularity-weighted disambiguation is the indicated fix and is not yet
   implemented.
6. **Catalogue composition.** The popularity feed is biased towards the
   demographics of one platform, and although the curated list and genre capping
   mitigate this, the catalogue is not a representative sample of recorded
   music.

---

## 5. Conclusion and Future Work

A content-based music recommendation system operating without any user
interaction data has been presented, in which four query modalities — a seed
recording, a free-text description of a desired sound, a typed title or
remembered lyric, and a hummed melody — are served from a single catalogue and
a single backend. The system is cold-start by construction: a recording becomes
recommendable as soon as its audio has been analysed, and a recording absent
from the catalogue is admitted at query time, analysed in the background, and
available to subsequent similarity queries within seconds.

Three findings are considered to constitute the substantive contribution.

First, a joint audio–language embedding was confirmed to outperform a
well-standardised hand-crafted descriptor baseline on genre-agreement
precision@k, attaining a precision@5 of 0.337 against 0.276 on a
1,404-recording catalogue, at 2.55 times the random control. The margin was
found to depend strongly on experimental conditions: it fell from 15% to 7%
once errors in the evaluation ground truth were corrected, and widened to 22%
as the catalogue grew from 529 to 1,404 recordings — the latter because the
baseline's absolute precision fell while the embedding's held, which suggests
that fixed summary descriptors scale less well than a learned representation.
The first movement demonstrates that catalogue hygiene is a precondition for,
rather than an adjunct to, valid evaluation; the second is the stronger
argument for preferring the learned representation, since a margin measured at
one catalogue size would have understated it.

Second, a publicly released music-specialised CLAP checkpoint was diagnosed as
degenerate on this task: 94% of embedding energy lay along one shared
direction, coarse genre agreement was at chance, and four distinct text prompts
produced one identical ranking. A single controlled checkpoint substitution
nearly doubled precision@5. Since a checkpoint's name and declared training
domain gave no indication of this, routine diagnosis of an embedding space
before it is trusted is argued to be necessary practice.

Third, a controlled negative result was obtained: anisotropy correction
degraded retrieval monotonically, from 0.315 to 0.251 in precision@5 as
correction was strengthened. The shared direction carries task-relevant signal
in this setting, and a remedy well supported in the sentence-embedding
literature does not transfer to this task. Anisotropy is therefore recommended
as a diagnostic statistic rather than as a target for correction.

A methodological position follows from all three. Each finding was obtained by
measurement against a control and would have been invisible to inspection of
summary similarity figures alone, and in two of the three cases the measurement
contradicted a reasonable prior expectation.

The following extensions are identified.

1. **Human evaluation.** A listening study over 20 seed recordings and their
   top-5 recommendations, rated on a five-point scale by multiple raters with
   inter-rater agreement reported, would replace the genre proxy with direct
   measurement of the quantity of interest. This is the single most valuable
   outstanding item.
2. **Melodic representation.** Replacing monophonic pitch tracking of polyphonic
   mixtures with dedicated melody extraction [32], and evaluating on hums
   recorded by people who know the recordings rather than on synthesised
   contours, should address the weakest component.
3. **Catalogue scale and indexing.** Extension towards $10^5$ recordings would
   require approximate nearest-neighbour indexing [44] in place of exhaustive
   cosine search, and would permit the hubness effects noted in Section 2.6 to
   be measured rather than assumed negligible.
4. **Fine-tuning on music.** The embedding is used entirely off the shelf.
   Contrastive fine-tuning on music-specific pairs, following MuLan [24] and
   MusCALL [25], is the obvious route to a larger margin over the baseline,
   provided the resulting space is subjected to the diagnostic procedure of
   Section 4.3.
5. **Hybrid recommendation.** Where interaction data becomes available, the
   content embedding can be combined with collaborative signal in the manner of
   van den Oord et al. [3], retaining cold-start coverage while benefiting from
   behavioural data for established recordings.
6. **Cover-version disambiguation.** Popularity-weighted ranking of lexical
   matches would address the limitation noted in Section 4.7.

---

## References

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
learning", *Advances in Neural Information Processing Systems (NeurIPS)*, vol.
35, 2022, pp. 17612–17625.

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
