import json
import pandas as pd
import numpy as np
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

# Calculate the center of the entire dataset
center_x = np.median(embedding[:, 0])
center_y = np.median(embedding[:, 1])

# Find the distance of each point to the nearest neighbor (or just check the extreme coordinates)
# Let's find points with Y < -something or X < -something that are far from the center
x_coords = embedding[:, 0]
y_coords = embedding[:, 1]

print(f"X range: {np.min(x_coords):.2f} to {np.max(x_coords):.2f}")
print(f"Y range: {np.min(y_coords):.2f} to {np.max(y_coords):.2f}")

# Find points that are isolated. 
# We'll calculate the 10th percentile and 90th percentile to see the main mass.
print(f"X 5th-95th: {np.percentile(x_coords, 5):.2f} to {np.percentile(x_coords, 95):.2f}")
print(f"Y 5th-95th: {np.percentile(y_coords, 5):.2f} to {np.percentile(y_coords, 95):.2f}")

# Find the absolute extreme bottom-left outliers that are significantly far from the 5th percentile
# For example, if min X is -20 but 5th percentile is -5.
isolated_indices = []
for i in range(len(x_coords)):
    # Let's just find points that are deeply in the bottom-left quadrant relative to the main mass
    # where both X and Y are very small compared to the bulk.
    if x_coords[i] < np.percentile(x_coords, 1) and y_coords[i] < np.percentile(y_coords, 1):
        isolated_indices.append(i)

if not isolated_indices:
    # If none match both, just find the absolute smallest X+Y
    distances = (x_coords - np.min(x_coords))**2 + (y_coords - np.min(y_coords))**2
    isolated_indices = np.argsort(distances)[:20]

# Filter to unique mammals in this isolated list
outlier_mammals = {}
for idx in isolated_indices:
    m = mammal_list[idx]
    if m not in outlier_mammals:
        outlier_mammals[m] = []
    outlier_mammals[m].append(codon_list[idx])

print("\nISOLATED OUTLIER MAMMALS IN BOTTOM LEFT:")
for m, c_list in outlier_mammals.items():
    print(f"{m}: {len(c_list)} codons (e.g., {c_list[:3]})")
