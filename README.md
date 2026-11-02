# Hummingbird

A Cold-Start Content-Based Music Recommendation System Using
Joint Audio-Language Embeddings and Query-by-Humming

## Authors
- B. L. Jainth Vaishnav (23MIA1022)
- Rajaa Sasidharan (23MIA1174)

## Project Mentor
Dr S Vigneshwari (54147)

## Course
CSE4077 - Recommender Systems, Project Based Component, Slot A1+TA1
M.Tech Integrated CSE (Business Analytics)
School of Computer Science and Engineering, VIT Chennai
October 2026

## About
Hummingbird recommends songs that sound like a song you already have.
A query can be a song title, a lyric, a free-text mood, or a hummed melody.
It uses CLAP audio-language embeddings and pYIN + subsequence DTW for humming.
New songs are analysed in the background, so there is no cold-start exclusion.

## Results (Precision@5)
- Hummingbird (CLAP): 0.337
- Baseline (MFCC etc.): 0.276
- Random control: 0.132

## How to Run
See others/RUN.md
1. Terminal 1: FastAPI backend (port 8000)
2. Terminal 2: Vite web client (port 5173)

## Folder Structure
- Source Codes/ : backend, web, mobile code
- Figures/      : all figures used in the report
- Tables/       : csv and json result files
- others/       : RUN, DEPLOY, requirements, report, paper, slides
- DemoLink.txt  : link to the demo video

## Licence
All rights reserved. For academic evaluation only.
