import numpy as np
import pandas as pd
from pathlib import Path

from preprocessing.query_expansion import query_expansion
from utils.reciprocal_rank import reciprocal_rank
from utils.reciprocal_rank_fusion import reciprocal_rank_fusion
from utils.reranking import cross_encoder_reranking
from utils.bm25_search import get_top_bm25_results
from utils.semantic_search import get_top_semantic_results

# generating dynamic paths through pathlib
BASE_DIR = Path(__file__).resolve().parent
TEST_DIR = BASE_DIR.parent
CSV_PATH = BASE_DIR.parent / 'evaluation_metadata.csv'

# constructing query set
df = pd.read_csv(TEST_DIR / 'gold_standard.tsv',sep='\t')
query_set = df['tweet_text'].tolist()
rel_uids = df['cord_uid'].tolist()

# constructing texts and corpus for cross encoder reranking
df = pd.read_csv(CSV_PATH)
corpus = df['cord_uid'].tolist()
texts = df['embedding_string'].tolist()

mrr_list = []

choice = input('Use Cross Encoder? : ')

for i,query in enumerate(query_set):

    expanded_query = query_expansion(query)
    
    # using expanded query in bm25 only
    list1 = get_top_bm25_results(expanded_query,100)
    list2 = get_top_semantic_results(query,100)
    
    # combing results through RFF
    idx_list = reciprocal_rank_fusion(list1,list2)

    if choice == 'yes':
        reranked_idx = cross_encoder_reranking(idx_list,texts,query)
    else:
        reranked_idx = idx_list

    # computing rr
    rr = reciprocal_rank(reranked_idx[:5],rel_uids[i],corpus)
    print(f'Reciprocal rank for {i+1}th query: {rr}')
    
    mrr_list.append(rr)

print('Overall Mean Reciprocal Rank: ',np.mean(mrr_list))

