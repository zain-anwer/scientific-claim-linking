# ------------------------- fixing bloody import issues --------------------------- #

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
# to fix the stupid import issues
sys.path.insert(0, str(BASE_DIR.parent))  # adds the parent directory to path

# ---------------------------------------------------------------------------------- #

import pickle
import numpy as np

IDX_PATH = BASE_DIR.parent / 'indexes'
with open(IDX_PATH / 'bm25.index.pkl','rb') as f:
    bm25_idx = pickle.load(f)

def get_top_bm25_results(query : str, n : int):

    query_tokens = query.split()

    # 1-D numpy array populated with similarity scores of each of the documents
    scores = bm25_idx.get_scores(query_tokens)
    
    # argsort returns the indices of the sorted numbers (prior sort) [::-1] reverses the list
    idx_list = np.argsort(scores)[::-1][:n]

    return idx_list