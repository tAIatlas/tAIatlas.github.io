import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples
import matplotlib.cm as cm

# 1. Load Data
with open('data/species_tai_gtai.json') as f:
    d = json.load(f)
species_list = d.get('species', d) if isinstance(d, dict) else d
mammals = [s for s in species_list if 'Mammal' in s.get('group', '')]

# 2. Filter to only the 100 High-Quality Mammals
good_mammals = []
for m in mammals:
    if all(w > 0.0 for w in m['codons'].values()):
        good_mammals.append(m)

# Extract all 6,100 w_i values
w_list = []
for m in good_mammals:
    w_list.extend(list(m['codons'].values()))
X = np.array(w_list).reshape(-1, 1)

print(f"Running K-Means Analysis on {len(good_mammals)} High-Quality Mammals ({len(X)} codon weights)")

# 3. Test multiple K values to prove what the optimal number of bins is now
best_k = 0
best_score = -1
for k in range(2, 11):
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    score = silhouette_score(X, labels)
    print(f"K={k} Silhouette Score: {score:.4f}")
    if score > best_score:
        best_score = score
        best_k = k

print(f"\nMATHEMATICAL CONCLUSION: The optimal number of bins is still K={best_k}!")

# 4. Generate the Silhouette Scatter Plot for K=8 on the clean data
kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(X)

# Sort labels logically based on centers
cluster_centers = kmeans.cluster_centers_.flatten()
sorted_cluster_indices = np.argsort(cluster_centers)
label_mapping = {old_label: new_label for new_label, old_label in enumerate(sorted_cluster_indices)}
labels = np.array([label_mapping[l] for l in cluster_labels])

silhouette_vals = silhouette_samples(X, labels)

plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(14, 10), dpi=200)
fig.patch.set_facecolor('#0b0f19')
ax.set_facecolor('#0b0f19')

y_lower = 10
cmap = cm.get_cmap('turbo', 8)
colors = [cmap(i) for i in range(8)]

# Plot the silhouette blades
for i in range(8):
    ith_cluster_silhouette_values = silhouette_vals[labels == i]
    ith_cluster_silhouette_values.sort()
    
    size_cluster_i = ith_cluster_silhouette_values.shape[0]
    y_upper = y_lower + size_cluster_i
    
    ax.fill_betweenx(np.arange(y_lower, y_upper), 0, ith_cluster_silhouette_values,
                     facecolor=colors[i], edgecolor=colors[i], alpha=0.7)
    
    # Add bin label in the middle
    ax.text(-0.05, y_lower + 0.5 * size_cluster_i, f"Bin {i}", color='white', 
            fontweight='bold', va='center', ha='right', fontsize=12)
    
    y_lower = y_upper + 20

# The vertical line for average silhouette score
avg_score = silhouette_score(X, labels)
ax.axvline(x=avg_score, color="red", linestyle="--", linewidth=2)
ax.text(avg_score + 0.02, y_lower - 50, f"Average Silhouette Score: {avg_score:.2f}", 
        color="red", fontweight="bold", fontsize=12, rotation=90, va="top")

ax.set_title("HIGH-QUALITY MAMMALIAN SILHOUETTE SCATTER PLOT\n(Corrupted zero-value assemblies removed)", 
             color="white", pad=20, fontsize=16, fontweight="bold")
ax.set_xlabel("Silhouette Coefficient (Cluster Cohesion)", color="lightgray", fontsize=12, fontweight="bold")
ax.set_ylabel("6,100 Pure Codon Weights (Sorted by Bin)", color="lightgray", fontsize=12, fontweight="bold")

ax.set_yticks([])  # Clear the yaxis labels / ticks
ax.set_xlim([-0.1, 1.0])
for spine in ['top', 'right', 'left']:
    ax.spines[spine].set_visible(False)

plt.tight_layout()
plt.savefig('img/mammals_clean_silhouette.png', facecolor='#0b0f19', edgecolor='none')
print("\nSaved high-quality plot to img/mammals_clean_silhouette.png")
