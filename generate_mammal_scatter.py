import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import matplotlib.cm as cm

# Set light background style
plt.style.use('default')
fig, ax = plt.subplots(figsize=(16, 9), dpi=200)

# 1. Load Data
with open('data/species_tai_gtai.json') as f:
    d = json.load(f)
species_list = d.get('species', d) if isinstance(d, dict) else d

# Extract mammals
mammal_data = []
for s in species_list:
    if 'Mammal' in s.get('group', ''):
        mammal_data.append(s['codons'])

# Compute average w_i for each mammal to sort them smoothly on the X-axis
mammal_means = [np.mean(list(c.values())) for c in mammal_data]
sorted_mammal_indices = np.argsort(mammal_means)

all_x = []
all_y = []
all_colors = []

# Define tAI color profile (Red=Slow, Blue/Green=Fast)
cmap = cm.get_cmap('turbo', 8)
colors = [cmap(i) for i in range(8)]

# 2. Process each mammal individually
for x_idx, m_idx in enumerate(sorted_mammal_indices):
    codons_dict = mammal_data[m_idx]
    w_values = np.array(list(codons_dict.values())).reshape(-1, 1)
    
    # Run K-Means on this specific mammal
    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    raw_labels = kmeans.fit_predict(w_values)
    
    # Map the clusters so that 0 = Slowest, 7 = Fastest
    cluster_centers = kmeans.cluster_centers_.flatten()
    sorted_cluster_indices = np.argsort(cluster_centers)
    label_mapping = {old_label: new_label for new_label, old_label in enumerate(sorted_cluster_indices)}
    
    # Assign new labels and add to plot arrays
    for i, w in enumerate(w_values.flatten()):
        bin_num = label_mapping[raw_labels[i]]
        all_x.append(x_idx)  # X-axis is the species index
        all_y.append(w)      # Y-axis is the raw w_i value
        all_colors.append(colors[bin_num])

# 3. Scatter plot of all samples
# alpha=0.6 so overlapping points blend
ax.scatter(all_x, all_y, c=all_colors, s=10, alpha=0.6, edgecolors='none')

# 4. Styling
ax.set_xlim(-2, len(mammal_data) + 2)
ax.set_ylim(-0.05, 1.05)

ax.grid(True, color='#e2e8f0', linestyle='-', linewidth=0.5, alpha=0.5)
ax.set_axisbelow(True)

for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)
for spine in ['left', 'bottom']:
    ax.spines[spine].set_color('#cbd5e1')

ax.set_title('INDIVIDUAL MAMMALIAN tAI CLUSTERING (K=8)\nEvery dot is a codon. Each vertical column is 1 of 157 Mammalian species independently clustered into 8 speed bins.', 
             color='#1e293b', pad=20, fontsize=14, fontweight='bold', loc='left')
ax.set_ylabel('Codon Weight (w$_i$)', color='#475569', fontsize=12, fontweight='bold')
ax.set_xlabel('Mammalian Species (Sorted by Overall Translation Speed)', color='#475569', fontsize=12, fontweight='bold', labelpad=10)

# Create a custom legend for the bins
import matplotlib.patches as mpatches
legend_patches = []
labels = ['Bin 0 (Full Pause)', 'Bin 1', 'Bin 2', 'Bin 3', 'Bin 4', 'Bin 5', 'Bin 6', 'Bin 7 (Max Sprint)']
for i in range(8):
    legend_patches.append(mpatches.Patch(color=colors[i], label=labels[i]))
ax.legend(handles=legend_patches, loc='lower right', bbox_to_anchor=(1.15, 0), frameon=False, fontsize=10)

plt.tight_layout()
plt.savefig('img/mammals_species_scatter.png', facecolor='white', edgecolor='none')
print("Saved to img/mammals_species_scatter.png")
