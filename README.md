PROJECT TITLE
    Hummingbird - A Cold-Start Content-Based Music Recommendation System
    Using Joint Audio-Language Embeddings and Query-by-Humming

AUTHORS
    Rajaa Sasidharan        23MIA1174
    B. L. Jainth Vaishnav   23MIA1022

PROJECT MENTOR
    Dr S Vigneshwari (54147)

COURSE
    CSE4077 - Recommender Systems
    Project Based Component, Slot A1+TA1
    MTech Integrated CSE (Business Analytics)
    School of Computer Science and Engineering
    Vellore Institute of Technology, Chennai

DATE
    October 2026

ABOUT
    Hummingbird recommends songs that sound like a song you already have.
    A query may be a song title, a remembered lyric, a free-text description
    of a mood, or a hummed melody. Because the system analyses audio rather
    than listening history, it has no cold-start exclusion: a recording is
    recommendable as soon as its audio has been analysed, and a recording
    missing from the catalogue is fetched, analysed in the background and
    made searchable within seconds.

    Catalogue   1,404 recordings, 1,403 with audio, 1,346 hummable
    Engine      CLAP joint audio-language embedding (512-d)
    Baseline    MFCC + chroma + spectral contrast + tempo (87-d, z-scored)
    Humming     pYIN pitch contour + vectorised subsequence DTW
    Result      Precision@5 of 0.337 against 0.276 for the baseline and
                0.132 for a random control (2.55x lift)

HOW TO RUN
    See others/RUN.md. Two terminals: the FastAPI backend on port 8000 and
    the Vite web client on port 5173.

DIRECTORY
    Source Codes/   backend (API, models, scripts), web, mobile
    Figures/        all figures appearing in the report
    Tables/         evaluation results as csv and json
    others/         README, RUN, DEPLOY, requirements, report, paper, slides
    DemoLink.txt    link to the demonstration video
