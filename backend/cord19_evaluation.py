# ----------------- INITIAL CONFIG --------------------- #

CHOICE = input('Use cross encoder reranking ? (yes/no): ')
K = int(input('Enter the value of query set to be used (1 - 1446): '))

# ------------------------------------------------------ #

import numpy as np
import pandas as pd
from pathlib import Path

from preprocessing.query_expansion import query_expansion
from evaluation_metrics.reciprocal_rank import reciprocal_rank
from postprocessing.reciprocal_rank_fusion import reciprocal_rank_fusion
from postprocessing.reranking import cross_encoder_reranking
from utils.bm25_search import get_top_bm25_results
from utils.semantic_search import get_top_semantic_results

# generating dynamic paths through pathlib
BASE_DIR = Path(__file__).resolve().parent
TEST_PATH = str(BASE_DIR / 'data/cord19_test.zip')
CSV_PATH = str(BASE_DIR / 'data/cord19_metadata.zip')
BM25_INDEX = str(BASE_DIR / 'cord19_indexes/bm25.index.pkl')
FAISS_INDEX = str(BASE_DIR / 'cord19_indexes/faiss.index')

# constructing query set
df = pd.read_csv(TEST_PATH)
query_set = df['tweet_text'].tolist()
rel_uids = df['cord_uid'].tolist()

# constructing texts and corpus for cross encoder reranking
df = pd.read_csv(CSV_PATH)
corpus = df['cord_uid'].tolist()
texts = df['embedding_string'].tolist()

mrr_list = []

for i,query in enumerate(query_set):

    if i >= K:
        break

    expanded_query = query_expansion(query)
    
    # using expanded query in bm25 only
    list1 = get_top_bm25_results(expanded_query,100,BM25_INDEX)
    list2 = get_top_semantic_results(query,100,FAISS_INDEX)
    
    # combing results through RFF
    idx_list = reciprocal_rank_fusion(list1,list2)

    if CHOICE == 'yes':
        reranked_idx = cross_encoder_reranking(idx_list,texts,query)[0]
    else:
        reranked_idx = idx_list

    # computing rr
    rr = reciprocal_rank(reranked_idx[:5],rel_uids[i],corpus)
    print(f'Reciprocal rank for {i+1}th query: {rr}')
    
    mrr_list.append(rr)

print('Overall Mean Reciprocal Rank: ',np.mean(mrr_list))

