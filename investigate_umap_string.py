import json
import pandas as pd
import numpy as np
import umap
from sklearn.cluster import DBSCAN

# 1. Load Data
with open('data/species_tai_gtai.json') as f:
    d = json.load(f)
species_list = d.get('species', d) if isinstance(d, dict) else d

mammals = [s for s in species_list if 'Mammal' in s.get('group', '')]
mammal_names = [s['species'] for s in mammals]

w_list = []
codon_list = []
mammal_list = []

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

# Re-run UMAP
reducer = umap.UMAP(n_neighbors=50, min_dist=0.1, random_state=42)
embedding = reducer.fit_transform(X)

# 2. Use DBSCAN to find the main blob and the isolated islands
# The main mass will be a huge dense cluster. The squiggly line will be its own cluster.
clustering = DBSCAN(eps=0.5, min_samples=10).fit(embedding)
labels = clustering.labels_

unique_labels = set(labels)
print("DBSCAN Clusters found:")
for label in unique_labels:
    mask = labels == label
    count = np.sum(mask)
    if label == -1:
        print(f"Noise points (-1): {count}")
    else:
        print(f"Cluster {label}: {count} points")
        
        # If this is a small isolated cluster (like the line with ~61 points)
        if count < 500:
            mammals_in_cluster = set(np.array(mammal_list)[mask])
            print(f"  -> Mammals in this isolated cluster: {mammals_in_cluster}")
            
            # Print the bin distributions to confirm it has all colors
            bins_in_cluster = []
            for idx in np.where(mask)[0]:
                bins_in_cluster.append(data_matrix[idx][0]) # We'll just look at w_i
            
            print(f"  -> w_i range: {min(bins_in_cluster):.2f} to {max(bins_in_cluster):.2f}")

# Let's also just explicitly check the mammal with the most extreme average w_i
print("\nMammals with most extreme average w_i (Feature 3 in UMAP):")
sorted_means = np.argsort(mammal_means)
print(f"Lowest: {mammal_names[sorted_means[0]]} ({mammal_means[sorted_means[0]]:.4f})")
print(f"2nd Lowest: {mammal_names[sorted_means[1]]} ({mammal_means[sorted_means[1]]:.4f})")
print(f"Highest: {mammal_names[sorted_means[-1]]} ({mammal_means[sorted_means[-1]]:.4f})")
print(f"2nd Highest: {mammal_names[sorted_means[-2]]} ({mammal_means[sorted_means[-2]]:.4f})")
