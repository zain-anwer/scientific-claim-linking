# Specter · Scientific Claim Verifier — Frontend

A lightweight web interface for the Scientific Claim Linking pipeline.
Deployed live at: https://scientific-claim-linking.vercel.app

## What It Does
Takes a social media post or scientific claim as input and displays
the top-ranked research papers retrieved by the multi-stage backend
pipeline (BM25 → SPECTER2/FAISS → Cross-Encoder reranking).

## Tech Stack
- HTML / CSS / JavaScript (vanilla)
- Deployed on Vercel

## Notes
- The frontend communicates with the backend API for query processing.
- No build step required — pure static files.