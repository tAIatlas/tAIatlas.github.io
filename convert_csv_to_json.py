#!/usr/bin/env python3
"""Convert tAI CSV databases to JSON for the tAIatlas web interface.

Uses NCBI Taxonomy-derived genus_taxonomy.json for accurate clade assignment,
and normalizes raw W_i to w_i = W_i / max(W_i) per species (dos Reis 2004).
"""

import csv
import json
import math
import os
import shutil


def load_taxonomy_map(base_dir):
    """Load the NCBI-derived genus → class mapping."""
    taxonomy_path = os.path.join(base_dir, 'genus_taxonomy.json')
    if os.path.exists(taxonomy_path):
        with open(taxonomy_path, 'r') as f:
            return json.load(f)
    print("  ⚠ genus_taxonomy.json not found, falling back to heuristic")
    return {}


def infer_taxonomic_group(species_name, taxonomy_map):
    """Infer taxonomic group from genus name using NCBI taxonomy."""
    genus = species_name.split()[0] if species_name else ''
    if genus in taxonomy_map:
        cls = taxonomy_map[genus]
        if cls != 'Unknown':
            return cls
    return 'Other Vertebrate'


def read_csv_to_records(csv_path, taxonomy_map, normalize=True):
    """Read a CSV file and return a list of species records.
    
    If normalize=True, converts raw W_i to w_i = W_i / max(W_i) per species.
    Also stores raw_max_wi as a proxy for tRNA gene count (quality indicator).
    """
    records = []
    codons = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        codons = header[1:]  # All columns after Species
        for row in reader:
            if not row or not row[0].strip():
                continue
            species = row[0].strip()
            raw_values = {}
            for i, codon in enumerate(codons):
                try:
                    raw_values[codon] = float(row[i + 1])
                except (IndexError, ValueError):
                    raw_values[codon] = 0.0

            # Compute raw stats
            raw_vals = list(raw_values.values())
            raw_max = max(raw_vals) if raw_vals else 1.0
            raw_mean = sum(raw_vals) / len(raw_vals) if raw_vals else 0.0

            # Normalize: w_i = W_i / max(W_i) — dos Reis (2004) standard
            if normalize and raw_max > 0:
                norm_values = {c: round(v / raw_max, 6) for c, v in raw_values.items()}
            else:
                norm_values = raw_values

            record = {
                'species': species,
                'group': infer_taxonomic_group(species, taxonomy_map),
                'codons': norm_values,       # Normalized w_i (0–1 scale)
                'raw_max_wi': round(raw_max, 2),  # Proxy for tRNA gene depth
                'raw_mean_wi': round(raw_mean, 2),
            }
            records.append(record)
    return records, codons


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)

    tempo_dir = os.path.dirname(os.path.dirname(base_dir))

    # Load NCBI taxonomy mapping
    print("Loading taxonomy mapping...")
    taxonomy_map = load_taxonomy_map(base_dir)
    print(f"  → {len(taxonomy_map)} genera mapped")

    # Source CSV files
    ncbi_csv = os.path.join(tempo_dir, 'global_vertebrate_stAI_database_ncbi.csv')
    gtrnadb_csv = os.path.join(tempo_dir, 'global_vertebrate_stAI_database.csv')
    merged_csv = os.path.join(tempo_dir, 'global_vertebrate_stAI_database_merged.csv')

    # Read all three datasets (normalized)
    print("Reading NCBI dataset...")
    ncbi_records, codons = read_csv_to_records(ncbi_csv, taxonomy_map, normalize=True)
    print(f"  → {len(ncbi_records)} species")

    print("Reading GtRNAdb dataset...")
    gtrnadb_records, _ = read_csv_to_records(gtrnadb_csv, taxonomy_map, normalize=True)
    print(f"  → {len(gtrnadb_records)} species")

    print("Reading merged dataset...")
    merged_records, _ = read_csv_to_records(merged_csv, taxonomy_map, normalize=True)
    print(f"  → {len(merged_records)} species")

    # Count taxonomic groups
    group_counts = {}
    for r in merged_records:
        g = r['group']
        group_counts[g] = group_counts.get(g, 0) + 1
    print(f"\nTaxonomic groups in merged: {group_counts}")

    # Sanity check: show a few species
    print("\n=== Normalization Check ===")
    for sp_name in ['Homo sapiens', 'Ambystoma mexicanum', 'Danio rerio']:
        rec = next((r for r in merged_records if r['species'] == sp_name), None)
        if rec:
            vals = list(rec['codons'].values())
            print(f"  {sp_name}: norm_mean={sum(vals)/len(vals):.4f}, "
                  f"norm_max={max(vals):.4f}, raw_max_Wi={rec['raw_max_wi']}")

    # Build the main JSON payload
    species_data = {
        'metadata': {
            'total_species': len(merged_records),
            'ncbi_species': len(ncbi_records),
            'gtrnadb_species': len(gtrnadb_records),
            'codons': codons,
            'groups': group_counts,
            'description': 'Normalized tRNA Adaptation Index (tAI) w_i values '
                           '(w_i = W_i / max(W_i)) for vertebrate species',
            'normalization': 'dos Reis (2004): w_i = W_i / max(W_i) per species',
        },
        'species': merged_records
    }

    # Write main JSON
    json_path = os.path.join(data_dir, 'species_tai.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(species_data, f, separators=(',', ':'))
    size_mb = os.path.getsize(json_path) / (1024 * 1024)
    print(f"\nWrote {json_path} ({size_mb:.2f} MB)")

    # Copy CSV files for download (raw values preserved)
    for src, dst_name in [
        (ncbi_csv, 'vertebrate_tai.csv'),
        (gtrnadb_csv, 'gtrnadb_tai.csv'),
        (merged_csv, 'merged_tai.csv'),
    ]:
        dst = os.path.join(data_dir, dst_name)
        shutil.copy2(src, dst)
        print(f"Copied {dst_name}")

    print("\n✓ All data files generated successfully!")
    print(f"  Values shown on web: NORMALIZED w_i (0–1)")
    print(f"  Values in CSVs:      RAW W_i (gene copy counts)")


if __name__ == '__main__':
    main()

