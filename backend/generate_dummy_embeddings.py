import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR / 'indexes'

num_clusters = 5
points_per_cluster = 2000
embedding_dim = 768

embeddings = []

for i in range(num_clusters):

    center = np.random.randn(embedding_dim) * 10

    cluster = center + np.random.randn(
        points_per_cluster,
        embedding_dim
    )

    embeddings.append(cluster)

embeddings = np.vstack(embeddings).astype("float32")

INDEX_DIR.mkdir(parents=True,exist_ok=True)
np.save(INDEX_DIR / 'dummy_embeddings.npy', embeddings)