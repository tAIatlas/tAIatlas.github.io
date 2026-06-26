import json
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import umap

# 1. Load Data
with open('data/species_tai_gtai.json') as f:
    d = json.load(f)
species_list = d.get('species', d) if isinstance(d, dict) else d

mammals = [s for s in species_list if 'Mammal' in s.get('group', '')]
mammal_names = [s['species'] for s in mammals]

w_list = []
codon_list = []
mammal_list = []

# Precalculate codon means and mammal means
df = pd.DataFrame([m['codons'] for m in mammals])
codon_means = df.mean().to_dict()
mammal_means = df.mean(axis=1).to_list()

data_matrix = []
for m_idx, m in enumerate(mammals):
    for c_idx, (codon, w) in enumerate(m['codons'].items()):
        w_list.append(w)
        codon_list.append(codon)
        mammal_list.append(mammal_names[m_idx])
        data_matrix.append([w, codon_means[codon], mammal_means[m_idx]])

X = np.array(data_matrix)

# 2. Re-run K-Means for Bins
kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
raw_w = X[:, 0].reshape(-1, 1)
raw_labels = kmeans.fit_predict(raw_w)

cluster_centers = kmeans.cluster_centers_.flatten()
sorted_cluster_indices = np.argsort(cluster_centers)
label_mapping = {old_label: new_label for new_label, old_label in enumerate(sorted_cluster_indices)}
labels = np.array([label_mapping[l] for l in raw_labels])

# 3. Re-run UMAP to get the exact same embedding
reducer = umap.UMAP(n_neighbors=50, min_dist=0.1, random_state=42)
embedding = reducer.fit_transform(X)

# 4. Find bottom-left points
# Bottom-left corresponds to min X and min Y
min_x = np.min(embedding[:, 0])
min_y = np.min(embedding[:, 1])

# Calculate Euclidean distance to the bottom-left corner
distances = np.sqrt((embedding[:, 0] - min_x)**2 + (embedding[:, 1] - min_y)**2)

# Get the indices of the 30 closest points
closest_indices = np.argsort(distances)[:30]

print("POINTS IN THE BOTTOM-LEFT CORNER OF THE UMAP:")
for idx in closest_indices:
    dist = distances[idx]
    codon = codon_list[idx]
    mammal = mammal_list[idx]
    w = w_list[idx]
    bin_num = labels[idx]
    print(f"Dist: {dist:.2f} | Bin {bin_num} | Codon: {codon} | w_i: {w:.4f} | Mammal: {mammal}")
