from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import umap

# UMAP MACROS
UMAP_SPREAD = 1.5      # higher values -> more spread out
UMAP_MIN_DIST = 0.05   # tighter clusters with lower values
UMAP_COMPONENTS = 3    # 3 dimensional space
UMAP_NEIGHBORS = 15    
UMAP_METRIC = 'cosine'

# KMEANS MACROS
N_CLUSTERS = 10

BASE_DIR = Path(__file__).resolve().parent
embeddings = np.load(BASE_DIR / 'indexes/embeddings.npy')

reducer = umap.UMAP(
    n_components = UMAP_COMPONENTS,
    n_neighbors = UMAP_NEIGHBORS,
    min_dist = UMAP_MIN_DIST,
    spread = UMAP_SPREAD, 
    metric = UMAP_METRIC,
    random_state = 42,
    low_memory = False
)

kmeans = KMeans(
    n_clusters = N_CLUSTERS,
    random_state = 42,
    n_init = 'auto'
)

# running kmeans on higher dimensional undistorted data
labels = kmeans.fit_predict(embeddings)

# reducing through umap
reduced = reducer.fit_transform(embeddings)








# plotly visualization

# Visual options
BRIDGE_OPACITY  = 0.07   # opacity of point→centroid lines (0 to disable)
POINT_OPACITY   = 0.65
CENTROID_SIZE   = 18
POINT_SIZE      = 4
 
# Colour palette — 10 distinct colours (extend if N_CLUSTERS > 10)
PALETTE = [
    "#FF6B6B", "#FFD93D", "#6BCB77", "#4D96FF", "#C77DFF",
    "#F4845F", "#2EC4B6", "#E71D36", "#FF9F1C", "#A8DADC",
]


# ─── 4. CENTROID POSITIONS IN REDUCED SPACE ──────────────────────────────────
# Average reduced coordinates per cluster (visual centroids for plotting)
 
centroids_3d = np.array([
    reduced[labels == k].mean(axis=0) for k in range(N_CLUSTERS)
])
 
# ─── 5. DENSITY-AWARE OPACITY ────────────────────────────────────────────────
# Use k-NN local density estimate: denser regions get more transparent points
# so the shape of the manifold is visible rather than a solid blob.
 
print("Estimating local density …")
nbrs = NearestNeighbors(n_neighbors=10, algorithm="ball_tree").fit(reduced)
distances, _ = nbrs.kneighbors(reduced)
local_density = 1.0 / (distances[:, 1:].mean(axis=1) + 1e-6)   # exclude self
 
# Rescale density to [min_opacity, max_opacity]
min_op, max_op = 0.25, 0.85
d_min, d_max = local_density.min(), local_density.max()
# Higher density → lower opacity (so interior is see-through)
opacities = max_op - (local_density - d_min) / (d_max - d_min + 1e-9) * (max_op - min_op)
 
# ─── 6. BUILD PLOTLY FIGURE ──────────────────────────────────────────────────
 
print("Building figure …")
fig = go.Figure()
 
for k in range(N_CLUSTERS):
    mask = labels == k
    pts  = reduced[mask]
    ops  = opacities[mask]
    col  = PALETTE[k % len(PALETTE)]
    name = f"Cluster {k}"
 
    # ── 6a. Bridge lines: each point → its centroid ──────────────────────────
    if BRIDGE_OPACITY > 0:
        cx, cy, cz = centroids_3d[k]
        # Interleave point coords with centroid coords and None (line breaks)
        lx, ly, lz = [], [], []
        for px, py, pz in pts:
            lx += [px, cx, None]
            ly += [py, cy, None]
            lz += [pz, cz, None]
 
        fig.add_trace(go.Scatter3d(
            x=lx, y=ly, z=lz,
            mode="lines",
            line=dict(color=col, width=1),
            opacity=BRIDGE_OPACITY,
            showlegend=False,
            hoverinfo="none",
            name=f"{name} bridges",
        ))
 
    # ── 6b. Data points (density-aware opacity via per-marker colour trick) ──
    # Plotly doesn't support per-point opacity natively, so we use rgba strings.
    def hex_to_rgba(hex_col: str, alpha: float) -> str:
        r, g, b = int(hex_col[1:3], 16), int(hex_col[3:5], 16), int(hex_col[5:7], 16)
        return f"rgba({r},{g},{b},{alpha:.2f})"
 
    marker_colours = [hex_to_rgba(col, float(a)) for a in ops]
 
    fig.add_trace(go.Scatter3d(
        x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
        mode="markers",
        marker=dict(
            size=POINT_SIZE,
            color=marker_colours,
            line=dict(width=0),
        ),
        name=name,
        legendgroup=name,
        hovertemplate=(
            f"<b>{name}</b><br>"
            "x: %{x:.3f}<br>y: %{y:.3f}<br>z: %{z:.3f}<extra></extra>"
        ),
    ))
 
    # ── 6c. Centroid marker ───────────────────────────────────────────────────
    cx, cy, cz = centroids_3d[k]
    fig.add_trace(go.Scatter3d(
        x=[cx], y=[cy], z=[cz],
        mode="markers+text",
        marker=dict(
            size=CENTROID_SIZE,
            color=col,
            symbol="x",
            line=dict(color="white", width=2),
            opacity=1.0,
        ),
        text=[f"C{k}"],
        textfont=dict(color="white", size=10),
        textposition="middle center",
        name=f"{name} centroid",
        legendgroup=name,
        showlegend=False,
        hovertemplate=(
            f"<b>Centroid {k}</b><br>"
            f"x: {cx:.3f}<br>y: {cy:.3f}<br>z: {cz:.3f}<extra></extra>"
        ),
    ))
 
# ─── 7. LAYOUT ───────────────────────────────────────────────────────────────
 
fig.update_layout(
    title=dict(
        text=(
            "Scientific Paper Embedding Space<br>"
            "<sup>SPECTER2 · UMAP(cosine) · KMeans</sup>"
        ),
        font=dict(
            size=16,
            family="Roboto, sans-serif",
        ),
        x=0.5,
        xanchor="center",
        pad=dict(t=10),
    ),
    scene=dict(
        xaxis_title="UMAP-1",
        yaxis_title="UMAP-2",
        zaxis_title="UMAP-3",
        bgcolor="rgb(10,10,20)",
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            backgroundcolor="rgb(10,10,20)",
            color="rgba(255,255,255,0.6)",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            backgroundcolor="rgb(10,10,20)",
            color="rgba(255,255,255,0.6)",
        ),
        zaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            backgroundcolor="rgb(10,10,20)",
            color="rgba(255,255,255,0.6)",
        ),
        camera=dict(
            eye=dict(x=1.5, y=1.5, z=0.8)  # slightly pulled back for full visibility
        ),
    ),
    paper_bgcolor="rgb(15,15,25)",
    plot_bgcolor="rgb(15,15,25)",
    font=dict(
        color="rgba(255,255,255,0.85)",
        family="Roboto, sans-serif",
        size=12,
    ),
    legend=dict(
        title=dict(
            text="Clusters",
            font=dict(size=13, family="Roboto, sans-serif"),
        ),
        bgcolor="rgba(255,255,255,0.05)",
        bordercolor="rgba(255,255,255,0.15)",
        borderwidth=1,
        x=1.0,
        xanchor="right",   # pin legend to right edge instead of overflowing
        y=0.95,
        yanchor="top",
        font=dict(size=11),
    ),
    margin=dict(l=10, r=160, t=90, b=10),  # r=160 reserves space for legend
    autosize=True,          # fills the container instead of fixed width
    height=750,
)
 
fig.show()
 
# Optional: save to HTML for portfolio / submission
out_html = BASE_DIR / "cluster_visualization.html"
fig.write_html(str(out_html))
print(f"\nSaved interactive HTML → {out_html}")