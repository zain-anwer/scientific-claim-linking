import faiss
from pathlib import Path
from preprocessing.embeddings import generate_embeddings

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_IDX_PATH = BASE_DIR.parent / 'indexes/faiss.index'

def get_top_semantic_results(query : str, n : int,IDX_PATH = None):

    faiss_idx = None

    if IDX_PATH:
        faiss_idx = faiss.read_index(str(IDX_PATH))
    else:
        faiss_idx = faiss.read_index(str(DEFAULT_IDX_PATH))

    query_vector = generate_embeddings([query])

    # faiss search already returns indices of embeddings sorted by distance   
    distances, idx_list = faiss_idx.search(query_vector,n)

    return idx_list[0]
