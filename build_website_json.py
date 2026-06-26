#!/usr/bin/env python3
import csv
import json
import os

def load_taxonomy_map(base_dir):
    taxonomy_path = os.path.join(base_dir, 'genus_taxonomy.json')
    if os.path.exists(taxonomy_path):
        with open(taxonomy_path, 'r') as f:
            return json.load(f)
    return {}

def load_prokaryote_map(pipeline_dir):
    prok_map = {}
    counts_path = os.path.join(pipeline_dir, 'prokaryote_output/filtered_trna_counts.tsv')
    if os.path.exists(counts_path):
        with open(counts_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                prok_map[row['species']] = row['clade'].capitalize()
    return prok_map

def infer_taxonomic_group(species_name, taxonomy_map, prok_map):
    # Try with exact name
    if species_name in prok_map:
        return prok_map[species_name]
    
    # Try replacing underscores with spaces (in case CSV has underscores)
    spaced_name = species_name.replace("_", " ")
    if spaced_name in prok_map:
        return prok_map[spaced_name]
        
    genus = species_name.split(' ')[0] if species_name else ''
    # Remove brackets from genus if present (e.g. '[Mycoplasma]')
    genus = genus.replace('[', '').replace(']', '').replace('_', '')
    
    if genus in taxonomy_map:
        cls = taxonomy_map[genus]
        if cls != 'Unknown':
            return f"Vertebrate ({cls})"
    return 'Eukaryote (Other)'

def read_csv_to_records(csv_path, taxonomy_map, prok_map):
    records = []
    codons = []
    if not os.path.exists(csv_path):
        print(f"Skipping {csv_path} (not found)")
        return records, codons

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return records, codons
            
        codons = header[1:]
        for row in reader:
            if not row or not row[0].strip() or len(row) < 2:
                continue
            species = row[0].strip()
            raw_values = {}
            for i, codon in enumerate(codons):
                try:
                    raw_values[codon] = float(row[i + 1])
                except (IndexError, ValueError):
                    raw_values[codon] = 0.0

            raw_vals = list(raw_values.values())
            raw_max = max(raw_vals) if raw_vals else 1.0
            raw_mean = sum(raw_vals) / len(raw_vals) if raw_vals else 0.0

            if raw_max > 0:
                norm_values = {c: round(v / raw_max, 6) for c, v in raw_values.items()}
            else:
                norm_values = raw_values

            record = {
                'species': species.replace("_", " "),
                'group': infer_taxonomic_group(species, taxonomy_map, prok_map),
                'codons': norm_values,
                'raw_max_wi': round(raw_max, 2),
                'raw_mean_wi': round(raw_mean, 2),
            }
            records.append(record)
    print(f"Loaded {len(records)} records from {csv_path}")
    return records, codons

def aggregate_records(records):
    from collections import defaultdict
    groups = defaultdict(list)
    
    for r in records:
        full_name = r['species']
        base_name = full_name
        accession = ""
        if ' (GCF ' in full_name:
            parts = full_name.split(' (GCF ')
            base_name = parts[0]
            accession = "GCF_" + parts[1].replace(')', '')
        elif ' (GCA ' in full_name:
            parts = full_name.split(' (GCA ')
            base_name = parts[0]
            accession = "GCA_" + parts[1].replace(')', '')
            
        r['base_species'] = base_name
        r['accession'] = accession
        
        r['distinct_anticodons'] = sum(1 for v in r['codons'].values() if v > 0)
        r['total_wi'] = sum(v for v in r['codons'].values())
        
        if r['distinct_anticodons'] < 40:
            print(f"Discarding bad assembly {accession} for {base_name} ({r['distinct_anticodons']} anticodons)")
            continue
            
        groups[base_name].append(r)
        
    final_records = []
    for base_name, asms in groups.items():
        asms.sort(key=lambda x: (x['distinct_anticodons'], x['total_wi']), reverse=True)
        
        champion = asms[0]
        champion['species'] = base_name
        champion['alternates'] = []
        
        for alt in asms[1:]:
            champion['alternates'].append({
                'accession': alt['accession'],
                'codons': alt['codons'],
                'raw_max_wi': alt['raw_max_wi'],
                'raw_mean_wi': alt['raw_mean_wi']
            })
            
        del champion['base_species']
        del champion['distinct_anticodons']
        del champion['total_wi']
        
        final_records.append(champion)
        
    return final_records

def build_json(records, codons, out_path):
    group_counts = {}
    for r in records:
        g = r['group']
        group_counts[g] = group_counts.get(g, 0) + 1

    species_data = {
        'metadata': {
            'total_species': len(records),
            'codons': codons,
            'groups': group_counts,
        },
        'species': records
    }

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(species_data, f, separators=(',', ':'))
    print(f"Wrote {out_path} ({len(records)} species)")

def main():
    base_dir = '/Users/dlt006/Documents/TEMPO_Antigrav/tAIatlas/taiatlas.github.io'
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    pipeline_dir = '/Users/dlt006/Documents/TEMPO_Antigrav/tAIatlas/pipeline/tai_pipeline'
    
    tax_map = load_taxonomy_map(base_dir)
    prok_map = load_prokaryote_map(pipeline_dir)

    for strategy in ['raw', 'static', 'dynamic']:
        dosreis_recs = []
        all_codons_strat = []
        
        recs, c = read_csv_to_records(os.path.join(pipeline_dir, f'prokaryote_output/prokaryotic_tai_database_{strategy}.csv'), tax_map, prok_map)
        dosreis_recs.extend(recs)
        if c: all_codons_strat = c
        
        recs, c = read_csv_to_records(os.path.join(pipeline_dir, f'eukaryotic_tai_database_{strategy}.csv'), tax_map, prok_map)
        dosreis_recs.extend(recs)
        if c: all_codons_strat = c

        dosreis_recs = aggregate_records(dosreis_recs)
        dosreis_recs.sort(key=lambda x: (x['group'], x['species']))
        if dosreis_recs:
            build_json(dosreis_recs, all_codons_strat, os.path.join(data_dir, f'species_tai_dosreis_{strategy}.json'))

    # gtAI: Prokaryotes + Eukaryotes (Computed on Dynamic only)
    gtai_recs = []
    all_codons_gtai = []
    
    recs, c = read_csv_to_records(os.path.join(pipeline_dir, 'prokaryote_output/prokaryotic_gtai_database.csv'), tax_map, prok_map)
    gtai_recs.extend(recs)
    if c: all_codons_gtai = c
    
    recs, c = read_csv_to_records(os.path.join(pipeline_dir, 'eukaryotic_gtai_database.csv'), tax_map, prok_map)
    gtai_recs.extend(recs)
    if c: all_codons_gtai = c

    gtai_recs = aggregate_records(gtai_recs)
    gtai_recs.sort(key=lambda x: (x['group'], x['species']))
    if gtai_recs:
        build_json(gtai_recs, all_codons_gtai, os.path.join(data_dir, 'species_tai_gtai.json'))

if __name__ == '__main__':
    main()
