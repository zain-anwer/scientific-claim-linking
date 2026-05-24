import numpy as np
import pickle
import faiss
import pandas as pd
from pathlib import Path
from indexer.faiss_indexer import generate_embeddings
from preprocessing.query_expansion import query_expansion
from preprocessing.query_normalization import normalize_query


BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / 'indexes'

df = pd.read_csv(BASE_DIR.parent / 'cleaned_metadata.csv')
df['doc'] = df['doi'].fillna(' ') + ' ' + df['title'].fillna(' ')
corpus = df['doc'].tolist()

# query set

query_set = [
    'chicken pox is much severe for adults',
    'dengue leads to insomnia and nausea',
    'covid vaccines lead to malaria',
    'covid is nothing but asthma',
]

faiss_idx = faiss.read_index(str(INDEX_PATH / 'faiss.index'))
with open(INDEX_PATH / 'bm25.index.pkl','rb') as f:
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

for query in query_set:
   
    expanded_query = query_expansion(query)
    
    # using expanded query in bm25 only
    list1 = get_top_bm25_results(expanded_query,3)
    list2 = get_top_semantic_results(query,3)
    
    # combing results through RFF
    idx_list = reciprocal_rank_fusion(list1,list2)
    result = [corpus[i] for i in idx_list]
    print('Result afer Reciprocal Rank Fusion (RRF): ')
    print(result)
