import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples
import umap
import matplotlib.cm as cm

# 1. Load Data
with open('data/species_tai_gtai.json') as f:
    d = json.load(f)
species_list = d.get('species', d) if isinstance(d, dict) else d

mammals = [s for s in species_list if 'Mammal' in s.get('group', '')]
mammal_names = [s['species'] for s in mammals]

w_list = []
codon_list = []
mammal_list = []

# Precalculate codon means and mammal means for UMAP manifold features
df = pd.DataFrame([m['codons'] for m in mammals])
codon_means = df.mean().to_dict()
mammal_means = df.mean(axis=1).to_list()

data_matrix = []
for m_idx, m in enumerate(mammals):
    for c_idx, (codon, w) in enumerate(m['codons'].items()):
        w_list.append(w)
        codon_list.append(codon)
        mammal_list.append(mammal_names[m_idx])
        # Feature vector: [Raw w_i, Average w_i of that codon, Average w_i of that mammal]
        data_matrix.append([w, codon_means[codon], mammal_means[m_idx]])

X = np.array(data_matrix)

# 2. Run K-Means(8) purely on the raw w_i to define exact speed bins
kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
raw_w = X[:, 0].reshape(-1, 1)
raw_labels = kmeans.fit_predict(raw_w)

cluster_centers = kmeans.cluster_centers_.flatten()
sorted_cluster_indices = np.argsort(cluster_centers)
label_mapping = {old_label: new_label for new_label, old_label in enumerate(sorted_cluster_indices)}
labels = np.array([label_mapping[l] for l in raw_labels])

# 3. Identify Divergent "Hallucinated" Mammals using Silhouette Scores
sil_scores = silhouette_samples(raw_w, labels)
mammal_sil_dict = {m: [] for m in mammal_names}
for i in range(len(mammal_list)):
    mammal_sil_dict[mammal_list[i]].append(sil_scores[i])

mammal_avg_sil = {m: np.mean(scores) for m, scores in mammal_sil_dict.items()}
sorted_mammals = sorted(mammal_avg_sil.items(), key=lambda x: x[1])

print("BOTTOM 10 MAMMALS BY SILHOUETTE SCORE (Candidates for removal):")
for m, score in sorted_mammals[:10]:
    print(f"{m}: {score:.4f}")

# 4. Generate UMAP Projection of all 9,577 points
reducer = umap.UMAP(n_neighbors=50, min_dist=0.1, random_state=42)
embedding = reducer.fit_transform(X)

# Plot
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(14, 10), dpi=200)
fig.patch.set_facecolor('#0b0f19')
ax.set_facecolor('#0b0f19')

cmap = cm.get_cmap('turbo', 8)
colors = [cmap(i) for i in range(8)]

for i in range(8):
    mask = labels == i
    ax.scatter(embedding[mask, 0], embedding[mask, 1], c=[colors[i]], s=15, alpha=0.7, label=f'Bin {i}', edgecolors='none')

ax.set_title('UMAP PROJECTION OF ALL 9,577 MAMMALIAN CODON WEIGHTS\nEvery single tAI calculation mapped into 8 distinct Speed Clusters', color='white', pad=20, fontsize=16, fontweight='bold')
leg = ax.legend(markerscale=3, loc='lower right', frameon=False, fontsize=12)
for text in leg.get_texts():
    text.set_color('white')

plt.axis('off')
plt.tight_layout()
plt.savefig('img/mammals_umap_9577.png', facecolor='#0b0f19', edgecolor='none')
print("Saved to img/mammals_umap_9577.png")
