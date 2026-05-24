from rank_bm25 import BM25Okapi
import pandas as pd
from pathlib import Path
import pickle

def build_bm25_index():
    BASE_DIR = Path(__file__).resolve().parent

    # the file path is relative to the cwd
    # what a load of crap :)

    INDEX_FOLDER = BASE_DIR.parent/'indexes/'
    INDEX_FILE   = BASE_DIR.parent/'indexes/bm25.index.pkl'


    # documents have already been parsed and cleaned in the dataset collection stage
    df = pd.read_csv(BASE_DIR.parent.parent/'cleaned_metadata.csv')
    docs = df['bm25_index_string'].tolist()

    corpus = [doc.split() for doc in docs]
    bm25_index = BM25Okapi(corpus)

    INDEX_FOLDER.mkdir(parents=True,exist_ok=True)

    with open(INDEX_FILE,mode="wb") as f:
        pickle.dump(bm25_index,f)

    print("BM25 index generated successfully")

if __name__ == '__main__':
    build_bm25_index()