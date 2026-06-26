import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import matplotlib.cm as cm

# 1. Load Data
with open('data/species_tai_gtai.json') as f:
    d = json.load(f)
species_list = d.get('species', d) if isinstance(d, dict) else d

# Extract all w_i values across all mammals
w_list = []
for s in species_list:
    if 'Mammal' in s.get('group', ''):
        w_list.extend(list(s['codons'].values()))

X = np.array(w_list).reshape(-1, 1)

# 2. Run K-Means(8) purely on the raw w_i
kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
raw_labels = kmeans.fit_predict(X)

cluster_centers = kmeans.cluster_centers_.flatten()
sorted_cluster_indices = np.argsort(cluster_centers)
label_mapping = {old_label: new_label for new_label, old_label in enumerate(sorted_cluster_indices)}
labels = np.array([label_mapping[l] for l in raw_labels])

# 3. Add random jitter for the Y-axis so points don't perfectly overlap
# This allows us to see the density of the 9,577 points
np.random.seed(42)
jitter_y = np.random.normal(0, 0.1, size=len(w_list))

# 4. Plot
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(14, 6), dpi=200)
fig.patch.set_facecolor('#0b0f19')
ax.set_facecolor('#0b0f19')

cmap = cm.get_cmap('turbo', 8)
colors = [cmap(i) for i in range(8)]

# Plot each bin
for i in range(8):
    mask = labels == i
    ax.scatter(X[mask, 0], jitter_y[mask], c=[colors[i]], s=8, alpha=0.5, label=f'Bin {i}', edgecolors='none')
    
    # Draw a vertical dashed line at the cluster boundaries to show the exact math
    if i < 7:
        max_val_in_bin = np.max(X[mask, 0])
        min_val_in_next = np.min(X[labels == (i+1), 0])
        threshold = (max_val_in_bin + min_val_in_next) / 2.0
        ax.axvline(x=threshold, color='white', linestyle='--', linewidth=1, alpha=0.3)

ax.set_title('MAMMALIAN tAI CLUSTERING PURELY BY SPEED ($w_i$)\n9,577 Codon Weights separated into 8 Mathematical Bins (No Codon/Species Bias)', color='white', pad=20, fontsize=14, fontweight='bold')
ax.set_xlabel('Translational Procession Speed ($w_i$)', color='lightgray', fontsize=12, fontweight='bold')

# Hide Y axis because it's just random jitter
ax.get_yaxis().set_visible(False)
for spine in ['top', 'right', 'left']:
    ax.spines[spine].set_visible(False)
ax.spines['bottom'].set_color('#cbd5e1')

leg = ax.legend(markerscale=3, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=8, frameon=False, fontsize=10)
for text in leg.get_texts():
    text.set_color('white')

plt.tight_layout()
plt.savefig('img/mammals_wi_jitter.png', facecolor='#0b0f19', edgecolor='none')
print("Saved to img/mammals_wi_jitter.png")
