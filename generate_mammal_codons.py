import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
import matplotlib.cm as cm

# Set dark background style
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(14, 8), dpi=200)
fig.patch.set_facecolor('#0b0f19')
ax.set_facecolor('#0b0f19')

# 1. Load Data
with open('data/species_tai_gtai.json') as f:
    d = json.load(f)
species_list = d.get('species', d) if isinstance(d, dict) else d

# Extract mammals
mammal_data = []
for s in species_list:
    if 'Mammal' in s.get('group', ''):
        mammal_data.append(s['codons'])

df = pd.DataFrame(mammal_data).fillna(0)
codons = [c for c in df.columns if len(c) == 3 and c.isupper()]
data = df[codons]

# 2. Compute Mean w_i per codon across all mammals
mean_wi = data.mean()

# 3. K-Means Clustering (k=8) on the 61 means
kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
X = mean_wi.values.reshape(-1, 1)
raw_labels = kmeans.fit_predict(X)

# 4. Map the clusters so that 0 = Slowest (Full Pause), 7 = Fastest (Max Sprint)
cluster_centers = kmeans.cluster_centers_.flatten()
sorted_cluster_indices = np.argsort(cluster_centers)
label_mapping = {old_label: new_label for new_label, old_label in enumerate(sorted_cluster_indices)}
labels = np.array([label_mapping[l] for l in raw_labels])

# 5. Sort codons by their mean w_i so the X-axis flows smoothly from slow to fast
sorted_codon_indices = np.argsort(mean_wi.values)
sorted_codons = [codons[i] for i in sorted_codon_indices]
sorted_labels = labels[sorted_codon_indices]

# Define tAI color profile (Red=Slow, Blue/Green=Fast)
cmap = cm.get_cmap('turbo', 8)
colors = [cmap(i) for i in range(8)]

# 6. Plot every single sample (157 mammals x 61 codons = 9577 points)
x_positions = []
y_values = []
point_colors = []

for x_idx, codon in enumerate(sorted_codons):
    bin_num = sorted_labels[x_idx]
    c_color = colors[bin_num]
    
    vals = data[codon].values
    jitter = np.random.normal(0, 0.15, size=len(vals))
    x_positions.extend(x_idx + jitter)
    y_values.extend(vals)
    point_colors.extend([c_color] * len(vals))

# Scatter plot of all samples
ax.scatter(x_positions, y_values, c=point_colors, s=15, alpha=0.5, edgecolors='none')

for bin_num in range(8):
    bin_x_indices = [i for i, l in enumerate(sorted_labels) if l == bin_num]
    if not bin_x_indices: continue
    center_x = np.mean(bin_x_indices)
    
    ax.text(center_x, -0.05, f'Bin {bin_num}', color=colors[bin_num], 
            fontsize=12, fontweight='bold', ha='center', va='top')
    
    if bin_num == 0:
        ax.text(center_x, -0.10, '(Full Pause)', color='white', fontsize=9, ha='center', alpha=0.7)
    elif bin_num == 7:
        ax.text(center_x, -0.10, '(Max Sprint)', color='white', fontsize=9, ha='center', alpha=0.7)

ax.set_xticks(range(61))
ax.set_xticklabels(sorted_codons, rotation=90, fontsize=7, fontfamily='monospace', color='#a0aec0')
ax.set_xlim(-1, 61)
ax.set_ylim(-0.15, 1.05)
ax.grid(True, color='#2a3441', linestyle='-', linewidth=0.5, alpha=0.3)
for spine in ax.spines.values():
    spine.set_color('#2a3441')

ax.set_title('K-MEANS CLUSTERING OF MAMMALIAN TRANSLATION SPEED BINS (K=8)\nShowing variance of all 61 codons across mammalian species', 
             color='white', pad=20, fontsize=14, fontweight='bold', loc='left')
ax.set_ylabel('Codon Weight (w$_i$)', color='#a0aec0', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('img/mammals_kmeans_bins.png', facecolor=fig.get_facecolor(), edgecolor='none')
print("Saved to img/mammals_kmeans_bins.png")
