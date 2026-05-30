# specter2 model weights and stuff --> increase startup time
# scispacy linker library --> increase startup time
# scibert_finetuned --> saved
# bio


# backend FASTAPI code

# -------------------------- FASTAPI RELATED IMPORTS ------------------------------ #

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import pandas as pd
import httpx
from pathlib import Path
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# -------------------------- INTERNAL LOGIC RELATED IMPORTS ----------------------- #

from preprocessing.query_expansion import query_expansion
from postprocessing.reciprocal_rank_fusion import reciprocal_rank_fusion
from postprocessing.reranking import cross_encoder_reranking
from postprocessing.fact_checking import claim_verification
from utils.bm25_search import get_top_bm25_results
from utils.semantic_search import get_top_semantic_results

# loading data from the csv

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data/cleaned_metadata.zip"

df = pd.read_csv(CSV_PATH)
corpus      = df["id"].tolist()
texts       = df["embedding_string"].tolist()
titles      = df["title"].tolist()
abstracts   = df["abstract"].tolist()
urls        = df["url"].tolist()

RERANK_TOP_N = 30   # cross encoder sees top 50 from RRF
RETURN_N     = 20   # endpoint returns top 20 after reranking

app = FastAPI(
    title="Scientific Claim Retrieval API",
    description="BM25 + semantic search + SciBERT reranking over scientific literature.",
    version="1.0.0",
)

# cross origin request setup 

app.add_middleware(
    CORSMiddleware,
    # allowing any domain to call API for now
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# payload schemas 

class QueryRequest(BaseModel):
    post: str

class PaperResult(BaseModel):
    rank:     int
    title:    str
    abstract: str
    url:      str
    stance:   str       # "supports" | "neutral" | "refutes"
    score:    float

class QueryResponse(BaseModel):
    query:   str
    results: list[PaperResult]

# API endpoints

@app.get("/")
async def health():

    hf_url = "https://huggingface.co"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(hf_url)
        hf_ok = resp.status_code == 200
    except Exception:
        hf_ok = False

    if not hf_ok:
        raise HTTPException(
            status_code=503,
            detail="HuggingFace Hub unreachable — model registry may be unavailable.",
        )

    return {"status": "ok", "huggingface": "reachable"}


@app.post("/query", response_model=QueryResponse)
def query_results(body: QueryRequest):
    
    post = body.post.strip()
    
    if not post:
        raise HTTPException(status_code=422, detail="Post text must not be empty.")

    # retrieval through both indexes
    expanded = query_expansion(post)
    list1 = get_top_bm25_results(expanded, 100)
    list2 = get_top_semantic_results(post, 100)

    # combining results through RFF
    idx_list = reciprocal_rank_fusion(list1, list2)

    # reranking through cross encoder
    reranked_idx, reranked_scores = cross_encoder_reranking(
        idx_list[:RERANK_TOP_N], texts, post
    )

    truth_values = []
    for idx in reranked_idx:
        truth_values.append(claim_verification(post,titles[idx],abstracts[idx])[0])

    results = []
    for rank, (idx, score) in enumerate(zip(reranked_idx[:RETURN_N], reranked_scores[:RETURN_N]), start=1):
        results.append(PaperResult(
            rank     = rank,
            title    = titles[idx],
            abstract = abstracts[idx],
            url      = urls[idx],
            stance   = truth_values[rank - 1],
            score    = round(float(score), 4),
        ))

    return QueryResponse(query=post, results=results)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)