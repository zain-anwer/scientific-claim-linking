import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel

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