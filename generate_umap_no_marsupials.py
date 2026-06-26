import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import umap
import matplotlib.cm as cm

# List of Marsupials to exclude
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

print(f"Total placental mammals included: {len(mammals)}")

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

# 2. Run K-Means(8) on raw w_i
kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
raw_w = X[:, 0].reshape(-1, 1)
raw_labels = kmeans.fit_predict(raw_w)

cluster_centers = kmeans.cluster_centers_.flatten()
sorted_cluster_indices = np.argsort(cluster_centers)
label_mapping = {old_label: new_label for new_label, old_label in enumerate(sorted_cluster_indices)}
labels = np.array([label_mapping[l] for l in raw_labels])

# 3. Generate UMAP Projection
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

ax.set_title('UMAP PROJECTION OF PLACENTAL MAMMALIAN CODON WEIGHTS\n(Marsupial outliers mathematically removed)', color='white', pad=20, fontsize=16, fontweight='bold')
leg = ax.legend(markerscale=3, loc='lower right', frameon=False, fontsize=12)
for text in leg.get_texts():
    text.set_color('white')

plt.axis('off')
plt.tight_layout()
plt.savefig('img/mammals_umap_placental.png', facecolor='#0b0f19', edgecolor='none')
print("Saved to img/mammals_umap_placental.png")
