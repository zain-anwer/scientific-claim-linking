import numpy as np
import pickle
import faiss
import pandas as pd
from pathlib import Path
from indexer.faiss_indexer import generate_embeddings
from preprocessing.query_expansion import query_expansion
from preprocessing.query_normalization import normalize_query
from sentence_transformers import CrossEncoder


ce_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

BASE_DIR = Path(__file__).resolve().parent
TEST_DIR = BASE_DIR.parent
IDX_PATH = BASE_DIR / 'eval_indexes'

df = pd.read_csv(TEST_DIR / 'test_gold.tsv',sep='\t')

query_set = df['tweet_text'].tolist()
rel_uids = df['cord_uid'].tolist()


df = pd.read_csv(BASE_DIR.parent / 'cleaned_metadata_evaluation.csv')
corpus = df['cord_uid'].tolist()
texts = df['embedding_string'].tolist()

faiss_idx = faiss.read_index(str(IDX_PATH / 'faiss.index'))
with open(IDX_PATH / 'bm25.index.pkl','rb') as f:
    bm25_idx = pickle.load(f)


def get_top_semantic_results(query : str, n : int):

    query_vector = generate_embeddings([query])

    # faiss search already returns indices of embeddings sorted by distance   
    distances, idx_list = faiss_idx.search(query_vector,n)

    return idx_list[0]


def get_top_bm25_results(query : str, n : int):
    
    # query normalization
    query_tokens = normalize_query(query)

    # 1-D numpy array populated with similarity scores of each of the documents
    scores = bm25_idx.get_scores(query_tokens)
    
    # argsort returns the indices of the sorted numbers (prior sort) [::-1] reverses the list
    idx_list = np.argsort(scores)[::-1][:n]

    return idx_list

# smoothing factor of 60 to prevent division by zero 

def cross_encoder_reranking(idx_list,query):

    pairs = [(query,texts[i]) for i in idx_list]
    scores = ce_model.predict(pairs)

    reranked_idx = [idx for score,idx in sorted(zip(scores,idx_list),reverse=True)]
    return reranked_idx

def reciprocal_rank_fusion(idx_list1 : np.ndarray,idx_list2 : np.ndarray,k : int = 60):

    idx_score = {}
    for idx_l in [idx_list1,idx_list2]:
        for i,idx in enumerate(idx_l):
            if idx not in idx_score:
                idx_score[idx] = 1 / (i + k)
            else:
                idx_score[idx] += 1 / (i + k)
    
    result_idx = sorted(idx_score,key=idx_score.get,reverse=True)
    return result_idx

def reciprocal_rank(result_ids,rel_id):
    mrr = 0
    i = 0
    for i, result_id in enumerate(result_ids):
        if i >= 5:
            break
        if corpus[result_id] == rel_id:
            mrr = 1 / (i + 1)
            return mrr
        i += 1
    return mrr

mrr_list = []

for i,query in enumerate(query_set):
   
    expanded_query = query_expansion(query)
    
    # using expanded query in bm25 only
    list1 = get_top_bm25_results(expanded_query,100)
    list2 = get_top_semantic_results(query,100)
    
    # combing results through RFF
    idx_list = reciprocal_rank_fusion(list1,list2)
    reranked_idx = cross_encoder_reranking(idx_list,query)

    # computing rr
    rr = reciprocal_rank(reranked_idx[:5],rel_uids[i])
    print(f'Reciprocal rank for {i+1}th query: {rr}')
    
    mrr_list.append(rr)

print('Overall Mean Reciprocal Rank: ',np.mean(mrr_list))

