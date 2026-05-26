import pickle
import numpy as np
from pathlib import Path
from preprocessing.query_normalization import normalize_query

BASE_DIR = Path(__file__).resolve().parent
IDX_PATH = BASE_DIR.parent / 'cord19_indexes'

with open(IDX_PATH / 'bm25.index.pkl','rb') as f:
    bm25_idx = pickle.load(f)

def get_top_bm25_results(query : str, n : int):
    
    # query normalization
    query_tokens = normalize_query(query)

    # 1-D numpy array populated with similarity scores of each of the documents
    scores = bm25_idx.get_scores(query_tokens)
    
    # argsort returns the indices of the sorted numbers (prior sort) [::-1] reverses the list
    idx_list = np.argsort(scores)[::-1][:n]

    return idx_list