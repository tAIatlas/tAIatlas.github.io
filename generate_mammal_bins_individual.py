import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
import matplotlib.cm as cm

# Set light background style
plt.style.use('default')
fig, ax = plt.subplots(figsize=(12, 8), dpi=200)

# 1. Load Data
with open('data/species_tai_gtai.json') as f:
    d = json.load(f)
species_list = d.get('species', d) if isinstance(d, dict) else d

# Extract mammals
mammal_data = []
for s in species_list:
    if 'Mammal' in s.get('group', ''):
        mammal_data.append(s['codons'])

# 2. Process each mammal individually
all_x = []
all_y = []
all_colors = []

# Define tAI color profile (Red=Slow, Blue/Green=Fast)
cmap = cm.get_cmap('turbo', 8)
colors = [cmap(i) for i in range(8)]

# We will run KMeans(k=8) on each mammal's 61 codons individually
for codons_dict in mammal_data:
    w_values = np.array(list(codons_dict.values())).reshape(-1, 1)
    
    # Run K-Means
    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    raw_labels = kmeans.fit_predict(w_values)
    
    # Map the clusters so that 0 = Slowest, 7 = Fastest
    cluster_centers = kmeans.cluster_centers_.flatten()
    sorted_cluster_indices = np.argsort(cluster_centers)
    label_mapping = {old_label: new_label for new_label, old_label in enumerate(sorted_cluster_indices)}
    
    # Assign new labels and add to plot arrays
    for i, w in enumerate(w_values.flatten()):
        bin_num = label_mapping[raw_labels[i]]
        
        # Add 0 jitter for a straight vertical stack
        jitter = 0
        all_x.append(bin_num + jitter)
        all_y.append(w)
        all_colors.append(colors[bin_num])

# 3. Scatter plot of all samples
ax.scatter(all_x, all_y, c=all_colors, s=15, alpha=0.5, edgecolors='none')

# 4. Styling
ax.set_xticks(range(8))
x_labels = [
    "0\n(Full Pause)", "1", "2", "3", "4", "5", "6", "7\n(Max Sprint)"
]
ax.set_xticklabels(x_labels, fontweight='bold', color='#333333')

ax.set_xlim(-0.5, 7.5)
ax.set_ylim(-0.05, 1.05)

ax.grid(True, color='#e2e8f0', linestyle='-', linewidth=1, axis='y')
ax.set_axisbelow(True) # Put grid behind points

for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)
for spine in ['left', 'bottom']:
    ax.spines[spine].set_color('#cbd5e1')

ax.set_title('INDIVIDUAL K-MEANS CLUSTERING OF MAMMALIAN TRANSLATION SPEEDS (K=8)\nEach of the 157 species is independently grouped into 8 internal codon speed bins', 
             color='#1e293b', pad=20, fontsize=14, fontweight='bold', loc='left')
ax.set_ylabel('Codon Weight (w$_i$)', color='#475569', fontsize=12, fontweight='bold')
ax.set_xlabel('Speed Bin', color='#475569', fontsize=12, fontweight='bold', labelpad=10)

plt.tight_layout()
plt.savefig('img/mammals_individual_bins.png', facecolor='white', edgecolor='none')
print("Saved to img/mammals_individual_bins.png")
