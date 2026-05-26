import faiss
from pathlib import Path
from utils.embeddings import generate_embeddings

BASE_DIR = Path(__file__).resolve().parent
IDX_PATH = BASE_DIR.parent / 'cord19_indexes'

faiss_idx = faiss.read_index(str(IDX_PATH / 'faiss.index'))

def get_top_semantic_results(query : str, n : int):

    query_vector = generate_embeddings([query])

    # faiss search already returns indices of embeddings sorted by distance   
    distances, idx_list = faiss_idx.search(query_vector,n)

    return idx_list[0]
