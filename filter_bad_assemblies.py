import json

with open('data/species_tai_gtai.json') as f:
    d = json.load(f)
species_list = d.get('species', d) if isinstance(d, dict) else d

mammals = [s for s in species_list if 'Mammal' in s.get('group', '')]

good_mammals = []
bad_mammals = []

for m in mammals:
    missing_codons = []
    for codon, w in m['codons'].items():
        if w == 0.0:
            missing_codons.append(codon)
    
    if len(missing_codons) > 0:
        bad_mammals.append({
            'species': m['species'],
            'accession': m.get('accession', 'Unknown'),
            'missing_count': len(missing_codons),
            'missing_codons': missing_codons
        })
    else:
        good_mammals.append(m['species'])

print(f"Total Mammals Evaluated: {len(mammals)}")
print(f"Corrupted Assemblies Found (w_i = 0.0): {len(bad_mammals)}")
print(f"High-Quality Assemblies Remaining: {len(good_mammals)}\n")

print("--- CORRUPTED GENOME ASSEMBLIES ---")
# Sort by the most missing codons
bad_mammals = sorted(bad_mammals, key=lambda x: x['missing_count'], reverse=True)

for b in bad_mammals:
    print(f"{b['species']} ({b['accession']}): Missing {b['missing_count']} codons {b['missing_codons']}")

