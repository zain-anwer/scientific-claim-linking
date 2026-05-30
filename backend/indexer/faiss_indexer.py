# -------------------------- FIXING IMPORT ISSUES --------------------------------------- #

import sys
from pathlib import Path

# getting the parent directory of 'indexer' (the root folder containing both modules)
# this probably fixes the path from where the code is executed 
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ---------------------------------------------------------------------------------------- #

from tqdm import tqdm
import numpy as np
import pandas as pd
import faiss
import pickle
from pathlib import Path
from preprocessing.embeddings import generate_embeddings

BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = str(BASE_DIR.parent / "indexes")

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
