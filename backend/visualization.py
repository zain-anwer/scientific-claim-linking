from pathlib import Path
from sklearn.cluster import KMeans
import pandas as pd
import plotly.express as px
import numpy as np
import umap


BASE_DIR = Path(__file__).resolve().parent
embeddings = np.load(BASE_DIR / 'indexes/embeddings.npy')

reducer = umap.UMAP(
    n_components=3,
    random_state=42
)

kmeans = KMeans(
    n_clusters = 10,
    random_state = 42,
    n_init = 'auto'
)

reduced = reducer.fit_transform(embeddings)
labels = kmeans.fit_predict(embeddings)

df = pd.DataFrame(
    {
        "x" : embeddings[:,0],
        "y" : embeddings[:,1],
        "z" : embeddings[:,0],
        "cluster" : labels
    }
)

fig = px.scatter_3d(
    df, 
    x = 'x',
    y = 'y',
    z = 'z',
    color = 'cluster'
)

fig.show()