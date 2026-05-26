from sentence_transformers import CrossEncoder

ce_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def cross_encoder_reranking(idx_list,texts,query):

    pairs = [(query,texts[i]) for i in idx_list]
    scores = ce_model.predict(pairs)

    reranked_idx = [idx for score,idx in sorted(zip(scores,idx_list),reverse=True)]
    return reranked_idx