import json
import pandas as pd
import numpy as np
import umap
from sklearn.cluster import DBSCAN

# List of Marsupials to exclude (matches previous script exactly)
marsupials = [
    'Trichosurus vulpecula', 'Notamacropus eugenii', 'Dromiciops gliroides',
    'Monodelphis domestica', 'Sminthopsis crassicaudata', 'Gracilinanus agilis',
    'Sarcophilus harrisii', 'Phascolarctos cinereus', 'Vombatus ursinus'
]

# 1. Load Data
with open('data/species_tai_gtai.json') as f:
    d = json.load(f)
species_list = d.get('species', d) if isinstance(d, dict) else d

# Filter to Mammals, but EXCLUDE Marsupials
mammals = []
mammal_names = []
for s in species_list:
    if 'Mammal' in s.get('group', ''):
        name = s['species']
        if name not in marsupials:
            mammals.append(s)
            mammal_names.append(name)

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

# 2. Re-run EXACT SAME UMAP Projection to get identical coordinates
reducer = umap.UMAP(n_neighbors=50, min_dist=0.1, random_state=42)
embedding = reducer.fit_transform(X)

# 3. Identify all distinct physical islands in the UMAP using DBSCAN
clustering = DBSCAN(eps=1.0, min_samples=5).fit(embedding)
labels = clustering.labels_
unique_labels = set(labels)

print("--- UMAP OUTLIER ISLAND ANALYSIS ---")
print(f"Total points: {len(X)}")
print(f"Total distinct physical islands found: {len(unique_labels) - (1 if -1 in unique_labels else 0)}\n")

for label in unique_labels:
    if label == -1:
        continue # Skip noise
        
    mask = labels == label
    count = np.sum(mask)
    
    # If the island is less than 50% of the data, it's an outlier island
    if count < len(X) * 0.5:
        island_x = embedding[mask, 0]
        island_y = embedding[mask, 1]
        center_x = np.mean(island_x)
        center_y = np.mean(island_y)
        
        # Get all unique mammals that have points in this island
        mammals_in_island = set(np.array(mammal_list)[mask])
        
        print(f"OUTLIER ISLAND {label}:")
        print(f"  - Size: {count} codons")
        print(f"  - Location (Center): X={center_x:.2f}, Y={center_y:.2f}")
        print(f"  - Bounding Box: X({np.min(island_x):.2f} to {np.max(island_x):.2f}), Y({np.min(island_y):.2f} to {np.max(island_y):.2f})")
        print(f"  - Mammals isolated here ({len(mammals_in_island)}):")
        for m in sorted(list(mammals_in_island)):
            # Count how many points this mammal contributed to this island
            m_mask = mask & (np.array(mammal_list) == m)
            m_count = np.sum(m_mask)
            print(f"      * {m} ({m_count} codons)")
        print()

print("--- OVERALL EMBEDDING BOUNDS ---")
print(f"Global X range: {np.min(embedding[:, 0]):.2f} to {np.max(embedding[:, 0]):.2f}")
print(f"Global Y range: {np.min(embedding[:, 1]):.2f} to {np.max(embedding[:, 1]):.2f}")
