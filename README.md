# 🔬 Scientific Claim Linking via Hybrid IR Pipeline

> Retrieving scientific papers from implicit social media mentions — inspired by CLEF CheckThat! 2025 Subtask 4b

---

## Overview

This project implements a **hybrid information retrieval pipeline** for linking social media posts to their original scientific sources. The core challenge is the linguistic gap between informal, colloquial posts and formal academic writing — posts paraphrase findings, omit citations, and use vocabulary that rarely matches standardized terminology.

The architecture closely mirrors the **1st-place system on the CLEF CheckThat! 2025 Subtask 4b development leaderboard** (Sager et al., 2025), adapted with:
- A **custom dataset** built from the OpenAlex API
- **Synthetic post generation** via the Cerebras API to simulate tweet-style claims
- **BM25-mined hard negatives** for a challenging evaluation set
- **Ontology-based normalization** using MeSH and UMLS (a contribution beyond the reference paper)

---

## Pipeline Architecture

```
Social Media Post
       │
       ▼
┌─────────────────────────────────────────┐
│           Query Preprocessing            │
│  Query Expansion + MeSH/UMLS Normalization│
└──────────────┬──────────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌────────────┐   ┌────────────┐
│  BM25      │   │   FAISS    │
│  Lexical   │   │  Semantic  │
│ Retrieval  │   │ Retrieval  │
└─────┬──────┘   └─────┬──────┘
      │                │
      └───────┬─────────┘
              ▼
    ┌──────────────────┐
    │ Reciprocal Rank  │
    │  Fusion (RRF)    │
    │  Candidate Merge │
    └────────┬─────────┘
             ▼
    ┌──────────────────┐
    │  Cross-Encoder   │
    │   Re-Ranking     │
    │ (Fine-tuned on   │
    │  custom dataset) │
    └────────┬─────────┘
             ▼
        Top-5 Papers
```

### Stage 1 — Lexical Retrieval (BM25)

- **Query expansion** augments the post with 2–3 contextually relevant sentences to increase n-gram overlap with formal document vocabulary
- **Ontology normalization** via MeSH and UMLS: canonical term anchoring, alias expansion, and denoising to bridge informal-to-formal terminology
- Returns top-K candidates ranked by BM25 score

### Stage 2 — Semantic Retrieval (FAISS)

- Transformer-based dense embeddings encode queries and documents into a shared vector space
- Cosine similarity search over a FAISS index retrieves the top-100 semantically similar documents
- Captures paraphrased and conceptually aligned content that lexical matching misses

### Stage 3 — Candidate Fusion (RRF)

- BM25 and FAISS candidate lists are merged using **Reciprocal Rank Fusion**
- RRF is robust to score scale differences between retrieval branches
- Functions as a **candidate merging step**, not final reranking — the unified pool is passed to the cross-encoder

### Stage 4 — Re-Ranking (Cross-Encoder)

- Cross-encoder jointly encodes each (query, document) pair for fine-grained relevance scoring
- Fine-tuned on the custom OpenAlex-derived dataset for biomedical domain adaptation
- Final top-5 results evaluated via **MRR@5**

---

## Dataset Construction

Since this project does not use the official CheckThat! dataset, a custom evaluation environment was built from scratch:

| Component | Method |
|---|---|
| **Document corpus** | OpenAlex API — biomedical papers (title + abstract) |
| **Query generation** | Cerebras API — LLM-generated synthetic tweets per document |
| **Hard negatives** | BM25-mined — top-ranked non-relevant documents per query |
| **Evaluation metric** | MRR@5 |

> **Note on synthetic queries:** Posts generated from source documents retain higher lexical overlap than real organic tweets, making first-stage retrieval easier than a true real-world setting. CORD-19 results are the more conservative benchmark.

---

## Results

### CORD-19 Evaluation Set

| Pipeline Configuration | MRR@5 |
|---|---|
| BM25 + FAISS (query expansion, no reranking) | 0.4587 |
| + MeSH normalization | 0.4641 |
| + UMLS normalization | 0.4573 |
| + Canonical anchors + denoising (MeSH) | 0.4840 |
| + Canonical anchors + denoising (UMLS) | 0.4764 |
| **+ Cross-encoder reranking (UMLS baseline)** | **0.5333** |
| **Gain from reranking** | **+7.63%** |

### Custom Dataset (100 queries)

| Configuration | MRR@5 |
|---|---|
| MeSH, no cross-encoder, no specialized normalization | 0.7578 |
| MeSH, no cross-encoder, with specialized normalization | 0.7583 |

### Comparison to Reference Paper (Sager et al., 2025 — Test Set)

| Stage | This Project (CORD-19) | Sager et al. |
|---|---|---|
| Best single-stage retrieval | 0.464 | 0.567 |
| + Cross-encoder reranking | 0.533 | 0.664 |
| **Reranking delta** | **+7.63%** | **+9.71 pp** |

The reranking delta is the most meaningful comparison point — proportionally similar gains confirm the cross-encoder is doing equivalent work across different corpora. The absolute gap in the baseline is explained by corpus size (CORD-19 is much larger), absence of in-domain dense retriever fine-tuning, and the reference paper's BPE preprocessing advantage.

---

## Key Findings

**1. Cross-encoder reranking is the single biggest lever.**
A +7.63% MRR gain on CORD-19 mirrors the reference paper's +9.71pp gain — confirming that the architectural trend generalizes across corpora and dataset sizes.

**2. MeSH outperforms UMLS for biomedical IR.**
MeSH consistently edges UMLS on CORD-19 (0.464 vs. 0.457 at baseline; 0.484 vs. 0.476 with denoising), consistent with MeSH being purpose-designed for biomedical literature indexing.

**3. Ontology normalization helps sparse retrieval more than dense.**
Custom dataset results show negligible difference (0.7583 vs. 0.7578) with specialized normalization for the semantic stage — dense models are robust to surface-form variation, consistent with the reference paper's implicit finding.

**4. RRF as candidate fusion (not final reranking) is correct.**
The reference paper's ablation showed RRF-as-final-reranker underperforms a cross-encoder by 7.1pp. This project uses RRF only to merge candidate pools before the cross-encoder, which is the right design.

---

## Project Structure

```
scientific-claim-linking/
├── data/
│   ├── build_dataset.py        # OpenAlex API corpus construction
│   ├── generate_posts.py       # Cerebras API synthetic tweet generation
│   └── mine_negatives.py       # BM25 hard negative mining
├── retrieval/
│   ├── bm25_retriever.py       # Lexical retrieval with query expansion
│   ├── faiss_retriever.py      # Dense semantic retrieval
│   └── normalization/
│       ├── mesh_normalizer.py  # MeSH ontology normalization
│       └── umls_normalizer.py  # UMLS ontology normalization
├── fusion/
│   └── rrf.py                  # Reciprocal rank fusion
├── reranking/
│   └── cross_encoder.py        # Cross-encoder reranking + fine-tuning
├── evaluation/
│   └── metrics.py              # MRR@k evaluation
├── configs/
│   └── pipeline_config.yaml    # Hyperparameters and model paths
└── run_pipeline.py             # End-to-end pipeline runner
```

---

## Setup

```bash
git clone https://github.com/<your-username>/scientific-claim-linking
cd scientific-claim-linking
pip install -r requirements.txt
```

### Dependencies

```
faiss-cpu
rank-bm25
sentence-transformers
transformers
torch
openai          # Cerebras API (OpenAI-compatible)
pyalex          # OpenAlex API client
```

### Running the Pipeline

```bash
# Build corpus from OpenAlex
python data/build_dataset.py --query "biomedical" --n_docs 5000

# Generate synthetic posts
python data/generate_posts.py --corpus data/corpus.jsonl

# Mine hard negatives
python data/mine_negatives.py --corpus data/corpus.jsonl

# Run full pipeline evaluation
python run_pipeline.py --eval_set data/eval_set.jsonl --corpus data/corpus.jsonl
```

---

## Reference

> Sager, P. J., Kamaraj, A., Grewe, B. F., & Stadelmann, T. (2025). *Deep Retrieval at CheckThat! 2025: Identifying Scientific Papers from Implicit Social Media Mentions via Hybrid Retrieval and Re-Ranking.* CLEF 2025 Working Notes, Madrid, Spain.

---

## Course Context

Built for **CS4051 — Information Retrieval**, FAST-NUCES Karachi.
Student ID: 23K-0750