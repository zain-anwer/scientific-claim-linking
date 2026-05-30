from sentence_transformers import CrossEncoder
from pathlib import Path

MODEL_PATH = str(Path(__file__).resolve().parent.parent / 'models/scibert_reranker')

ce_model = CrossEncoder(MODEL_PATH)

def cross_encoder_reranking(idx_list,texts,query):

    idx_list = idx_list[:25]
    pairs = [(query,texts[i]) for i in idx_list]
    scores = ce_model.predict(pairs)

    reranked_idx = [idx for score,idx in sorted(zip(scores,idx_list),reverse=True)]
    scores = [score for score,idx in sorted(zip(scores,idx_list),reverse=True)]
    return reranked_idx,scores