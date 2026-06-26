import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score
import matplotlib.cm as cm

# Set light background style
plt.style.use('default')
fig, ax = plt.subplots(figsize=(12, 10), dpi=200)

# 1. Load Data
with open('data/species_tai_gtai.json') as f:
    d = json.load(f)
species_list = d.get('species', d) if isinstance(d, dict) else d

all_w = []
for s in species_list:
    if 'Mammal' in s.get('group', ''):
        all_w.extend(list(s['codons'].values()))

X = np.array(all_w).reshape(-1, 1)

# 2. Run K-Means on all 9,577 scalar points
n_clusters = 8
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
raw_labels = kmeans.fit_predict(X)

# Map labels so 0 = Slowest, 7 = Fastest
cluster_centers = kmeans.cluster_centers_.flatten()
sorted_cluster_indices = np.argsort(cluster_centers)
label_mapping = {old_label: new_label for new_label, old_label in enumerate(sorted_cluster_indices)}
cluster_labels = np.array([label_mapping[l] for l in raw_labels])

# 3. Calculate Silhouette Scores for every single point
sample_silhouette_values = silhouette_samples(X, cluster_labels)
overall_score = silhouette_score(X, cluster_labels)

# Define tAI color profile (Red=Slow, Blue/Green=Fast)
cmap = cm.get_cmap('turbo', n_clusters)
colors = [cmap(i) for i in range(n_clusters)]

# 4. Plot Silhouette Scatter Plot
y_lower = 10
y_ticks = []
y_tick_labels = []

# We iterate through the bins (0 to 7)
for i in range(n_clusters):
    # Aggregate the silhouette scores for samples belonging to cluster i, and sort them
    ith_cluster_silhouette_values = sample_silhouette_values[cluster_labels == i]
    ith_cluster_silhouette_values.sort()

    size_cluster_i = ith_cluster_silhouette_values.shape[0]
    y_upper = y_lower + size_cluster_i

    # Plot as a scatter plot (thousands of dots forming the silhouette blade)
    y_range = np.arange(y_lower, y_upper)
    ax.scatter(ith_cluster_silhouette_values, y_range, 
               s=1, color=colors[i], alpha=0.8, edgecolors='none')

    # Label the cluster in the middle
    y_ticks.append(y_lower + 0.5 * size_cluster_i)
    y_tick_labels.append(f'Bin {i}')
    
    # Compute new y_lower for next plot
    y_lower = y_upper + 100  # 100 blank space between clusters

# 5. Styling
ax.set_title(f'SILHOUETTE SCATTER PLOT OF MAMMALIAN SPEED BINS (K=8)\nEvery one of the 9,577 tAI weights is plotted based on its mathematical fit to its assigned Bin', 
             color='#1e293b', pad=20, fontsize=14, fontweight='bold', loc='left')
ax.set_xlabel('Silhouette Coefficient (Mathematical Cluster Cohesion)', color='#475569', fontsize=12, fontweight='bold')
ax.set_ylabel('Speed Bins (Organized by Cluster, Not by Mammal)', color='#475569', fontsize=12, fontweight='bold')

# The vertical line for average silhouette score of all the values
ax.axvline(x=overall_score, color="red", linestyle="--", linewidth=2, label=f'Average Score: {overall_score:.3f}')

ax.set_yticks(y_ticks)
ax.set_yticklabels(y_tick_labels, fontweight='bold', color='#333333')
ax.set_xlim([-0.1, 1.0])
ax.grid(True, color='#e2e8f0', linestyle='-', linewidth=0.5, axis='x', alpha=0.5)
ax.set_axisbelow(True)

for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)
for spine in ['left', 'bottom']:
    ax.spines[spine].set_color('#cbd5e1')

ax.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#e2e8f0')

plt.tight_layout()
plt.savefig('img/mammals_silhouette_scatter.png', facecolor='white', edgecolor='none')
print("Saved to img/mammals_silhouette_scatter.png")
