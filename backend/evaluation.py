# ----------------- INITIAL CONFIG --------------------- #

CHOICE = input('Use cross encoder reranking ? (yes/no): ')
K = int(input('Number of queries to process : '))

# ------------------------------------------------------ #

import numpy as np
import pandas as pd
from pathlib import Path

from preprocessing.query_expansion import query_expansion
from preprocessing.query_normalization import normalize_query_semantic_search
from evaluation_metrics.reciprocal_rank import reciprocal_rank
from postprocessing.reciprocal_rank_fusion import reciprocal_rank_fusion
from postprocessing.reranking import cross_encoder_reranking
from postprocessing.fact_checking import claim_verification
from utils.bm25_search import get_top_bm25_results
from utils.semantic_search import get_top_semantic_results

# generating dynamic paths through pathlib
BASE_DIR = Path(__file__).resolve().parent
TEST_PATH = str(BASE_DIR / 'data/test.zip')
CSV_PATH = str(BASE_DIR / 'data/cleaned_metadata.zip')

# constructing query set
test_df = pd.read_csv(TEST_PATH)
query_set = test_df['social_post'].tolist()
rel_ids = test_df['id'].tolist()

# constructing texts and corpus for cross encoder reranking
df = pd.read_csv(CSV_PATH)
corpus = df['id'].tolist()
texts = df['embedding_string'].tolist()

# to store reciprocal rank values for every query
mrr_list = []


for i,query in enumerate(query_set):

    if i >= K:
        break

    # normalization happens before query expansion to remove noise
    bm25_query = query_expansion(query)

    # applying specific normalization (emoji/URL/unicode/elongation/etc)
    semantic_query = normalize_query_semantic_search(query)

    # using expanded query in bm25 only
    list1 = get_top_bm25_results(bm25_query,100)

    # use unexpanded query in semantic search
    list2 = get_top_semantic_results(query,100)
    
    # combing results through RFF
    idx_list = reciprocal_rank_fusion(list1,list2)

    if CHOICE == 'yes':
        reranked_idx = cross_encoder_reranking(idx_list,texts,query)[0]
    else:
        reranked_idx = idx_list

    # checking NLI pipeline for the papers
    # truth_value = []
    # for idx in reranked_idx:
    #    truth_value.append(claim_verification(query,df['title'].iloc[idx],df['abstract'].iloc[idx])[0])

    # computing rr
    rr = reciprocal_rank(reranked_idx[:5],rel_ids[i],corpus)
    print(f'Reciprocal rank for {i+1}th query: {rr}')
    # print(f'Truth value of according to posts: ',truth_value)
    
    mrr_list.append(rr)

print('Overall Mean Reciprocal Rank: ',np.mean(mrr_list))

