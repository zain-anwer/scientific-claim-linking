from tqdm import tqdm
import numpy as np
import pandas as pd
import faiss
import pickle
from pathlib import Path
from utils.embeddings import generate_embeddings

BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR.parent / "indexes"

def build_faiss_index():

    df = pd.read_csv(BASE_DIR.parent.parent/'cleaned_metadata.csv')
    texts = df['embedding_string'].fillna('').tolist()
    ids = df['id'].fillna('').tolist()

    BATCH_SIZE = 16
    batched_embeddings = []

    for i in tqdm(range(0,len(texts),BATCH_SIZE)):
        batched_embeddings.append(generate_embeddings(texts[i:i+BATCH_SIZE]))

    embeddings = np.vstack(batched_embeddings)

    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    # checking and creating the indexes directory in case it doesn't exist
    INDEX_DIR.mkdir(parents=True,exist_ok=True)

    # saving the faiss index
    faiss.write_index(index,str(INDEX_DIR/'faiss.index'))

    # saving embedding vectors for cluster representation
    np.save(INDEX_DIR/'embeddings.npy',embeddings)

    # saving uids for querying
    with open(INDEX_DIR/'uids.pkl','wb') as f:
        pickle.dump(ids,f)

    print('FAISS index generated successfully')

if __name__ == '__main__':
    build_faiss_index()    
