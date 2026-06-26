import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.cm as cm
import matplotlib.patheffects as pe

# Set light background style
plt.style.use('default')
fig, ax = plt.subplots(figsize=(12, 8), dpi=200)

# 1. Load Data
with open('data/species_tai_gtai.json') as f:
    d = json.load(f)
species_list = d.get('species', d) if isinstance(d, dict) else d

mammal_data = []
for s in species_list:
    if 'Mammal' in s.get('group', ''):
        mammal_data.append(s['codons'])

# 2. Build matrix of 61 Codons x 157 Mammals
df = pd.DataFrame(mammal_data).fillna(0)
codons = [c for c in df.columns if len(c) == 3 and c.isupper()]
data = df[codons].values.T # Shape: (61, 157)

# 3. PCA to 2D
pca = PCA(n_components=2, random_state=42)
pca_result = pca.fit_transform(data)

# 4. K-Means (k=8) on the original 157D space
kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
raw_labels = kmeans.fit_predict(data)

# Sort bins so 0 is slowest (lowest mean PC1/w_i) and 7 is fastest
cluster_centers = kmeans.cluster_centers_.mean(axis=1) # Mean across all 157 mammals
sorted_cluster_indices = np.argsort(cluster_centers)
label_mapping = {old_label: new_label for new_label, old_label in enumerate(sorted_cluster_indices)}
labels = np.array([label_mapping[l] for l in raw_labels])

# Define tAI color profile (Red=Slow, Blue/Green=Fast)
cmap = cm.get_cmap('turbo', 8)
colors = [cmap(i) for i in range(8)]

# Plot points
for i in range(8):
    mask = labels == i
    ax.scatter(pca_result[mask, 0], pca_result[mask, 1], 
               c=[colors[i]], label=f'Bin {i}', 
               alpha=0.8, s=100, edgecolors='white', linewidth=1, zorder=2)

# Annotate codons
for idx, codon in enumerate(codons):
    bin_num = labels[idx]
    ax.text(pca_result[idx, 0], pca_result[idx, 1] + 0.02, codon, 
            color='#333333', fontsize=8, ha='center', va='bottom', zorder=3,
            path_effects=[pe.withStroke(linewidth=2, foreground='white')])

# Draw centroids
centroids_pca = pca.transform(kmeans.cluster_centers_)
for i in range(8):
    bin_idx = np.where(sorted_cluster_indices == i)[0][0]
    ax.scatter(centroids_pca[bin_idx, 0], centroids_pca[bin_idx, 1], 
               c=[colors[i]], s=300, marker='X', edgecolors='black', linewidth=1.5, zorder=1)

# Styling
ax.grid(True, color='#e2e8f0', linestyle='-', linewidth=1, alpha=0.5)
ax.set_axisbelow(True)

for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)
for spine in ['left', 'bottom']:
    ax.spines[spine].set_color('#cbd5e1')

ax.set_title('PCA SCATTER PLOT OF MAMMALIAN CODON SPEED BINS (K=8)\nVisualizing the 61 codons clustered by their translation profiles across 157 mammals', 
             color='#1e293b', pad=20, fontsize=14, fontweight='bold', loc='left')
ax.set_xlabel('Principal Component 1 (Translation Speed / Mean w$_i$)', color='#475569', fontsize=12, fontweight='bold')
ax.set_ylabel('Principal Component 2 (Lineage Variance)', color='#475569', fontsize=12, fontweight='bold')

# Legend
leg = ax.legend(loc='lower right', frameon=True, facecolor='white', edgecolor='#e2e8f0')
leg.get_texts()[0].set_text('Bin 0 (Full Pause)')
leg.get_texts()[-1].set_text('Bin 7 (Max Sprint)')

plt.tight_layout()
plt.savefig('img/mammals_pca_codons.png', facecolor='white', edgecolor='none')
print("Saved to img/mammals_pca_codons.png")
