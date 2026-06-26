import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import matplotlib.cm as cm

# 1. Load Clean Data
with open('data/species_tai_gtai.json') as f:
    d = json.load(f)
species_list = d.get('species', d) if isinstance(d, dict) else d
mammals = [s for s in species_list if 'Mammal' in s.get('group', '')]
good_mammals = [m for m in mammals if all(w > 0.0 for w in m['codons'].values())]

w_list = []
for m in good_mammals:
    w_list.extend(list(m['codons'].values()))
X = np.array(w_list).reshape(-1, 1)

np.random.seed(42)
jitter_y = np.random.normal(0, 0.1, size=len(w_list))

# 2. Setup Plot
plt.style.use('dark_background')
fig, axes = plt.subplots(4, 1, figsize=(14, 14), dpi=200, sharex=True)
fig.patch.set_facecolor('#0b0f19')

k_values = [5, 6, 7, 8]

for idx, k in enumerate(k_values):
    ax = axes[idx]
    ax.set_facecolor('#0b0f19')
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    raw_labels = kmeans.fit_predict(X)

    # Sort labels
    cluster_centers = kmeans.cluster_centers_.flatten()
    sorted_cluster_indices = np.argsort(cluster_centers)
    label_mapping = {old_label: new_label for new_label, old_label in enumerate(sorted_cluster_indices)}
    labels = np.array([label_mapping[l] for l in raw_labels])

    cmap = cm.get_cmap('turbo', k)
    colors = [cmap(i) for i in range(k)]

    for i in range(k):
        mask = labels == i
        ax.scatter(X[mask, 0], jitter_y[mask], c=[colors[i]], s=8, alpha=0.5, edgecolors='none')
        
        if i < k - 1:
            max_val_in_bin = np.max(X[mask, 0])
            min_val_in_next = np.min(X[labels == (i+1), 0])
            threshold = (max_val_in_bin + min_val_in_next) / 2.0
            ax.axvline(x=threshold, color='white', linestyle='--', linewidth=1.5, alpha=0.5)
            
    ax.set_title(f'K = {k} Bins', color='white', pad=10, fontsize=14, fontweight='bold')
    ax.get_yaxis().set_visible(False)
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    
    if idx == 3:
        ax.spines['bottom'].set_color('#cbd5e1')
        ax.set_xlabel('Translational Procession Speed ($w_i$)', color='lightgray', fontsize=12, fontweight='bold')
    else:
        ax.spines['bottom'].set_visible(False)
        ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)

plt.tight_layout()
plt.savefig('img/mammals_k_comparison.png', facecolor='#0b0f19', edgecolor='none')
print("Saved to img/mammals_k_comparison.png")
