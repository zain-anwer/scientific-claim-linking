import torch
from tqdm import tqdm
import numpy as np
import pandas as pd
import faiss
import pickle
from pathlib import Path
from transformers import AutoTokenizer, AutoModel

BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR.parent / "indexes"
MODEL_NAME = 'allenai/specter2_base'
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model.eval() # since we aren't using it for training

def generate_embeddings(texts : list[str]) -> np.ndarray:    

    # text --> tokens --> numerical tags --> padding/truncation
    # return_tensors flag decides the math object returned
    # neural networks cannot read normal python lists since they expect batch data
    # soo we convert them to PyTorch tensors [[xx,xx,xx,...,xx]]

    inputs = tokenizer(
        texts,
        return_tensors = 'pt',
        truncation = True,
        padding = True,
        max_length = 512,
    )
    
    # slashes RAM usage by stopping training or something
    with torch.no_grad():

        # the tokenizer returns a dictionary output
        # input_ids are numerical representations of tokens
        # attention_mask is a tensor that tells which tokens are padding and which are not (1/0)
        outputs = model(
            input_ids = inputs["input_ids"],
            attention_mask = inputs["attention_mask"]
        )
    
    embeddings = outputs.last_hidden_state[:,0,:]
    embeddings = embeddings.numpy()
    return embeddings.astype('float32')

def build_faiss_index():

    df = pd.read_csv(BASE_DIR.parent.parent/'cleaned_metadata.csv')
    texts = df['embedding_string'].fillna('').tolist()
    cord_uids = df['cord_uid'].fillna('').tolist()

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
        pickle.dump(cord_uids,f)

    print('FAISS index generated successfully')

if __name__ == '__main__':
    build_faiss_index()    
