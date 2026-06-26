import json
import csv
import glob
import os

print("--- Updating JSON Databases ---")
json_files = glob.glob('data/species_tai*.json')

vertebrate_species = set()

for filepath in json_files:
    print(f"Processing {filepath}...")
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    species_list = data.get('species', data) if isinstance(data, dict) else data
    
    incomplete_count = 0
    for s in species_list:
        missing = []
        is_vert = 'Vertebrate' in s.get('group', '')
        if is_vert:
            vertebrate_species.add(s['species'])
            for c, w in s['codons'].items():
                if w == 0.0:
                    missing.append(c)
        
        # Only flag if it's a vertebrate and has missing codons
        s['is_incomplete'] = len(missing) > 0
        s['missing_codons'] = missing
        if len(missing) > 0:
            incomplete_count += 1
            
        # Check alternates
        if 'alternates' in s:
            for alt in s['alternates']:
                alt_missing = []
                if is_vert:
                    for c, w in alt['codons'].items():
                        if w == 0.0:
                            alt_missing.append(c)
                alt['is_incomplete'] = len(alt_missing) > 0
                alt['missing_codons'] = alt_missing
                
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=None)
    print(f"  -> Flagged {incomplete_count} incomplete vertebrate species.")

print("\n--- Updating CSV Databases ---")
csv_files = ['data/vertebrate_tai.csv', 'data/merged_tai.csv']
for filepath in csv_files:
    if not os.path.exists(filepath):
        continue
    print(f"Processing {filepath}...")
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
        
    if 'Is_Incomplete_Assembly' not in fieldnames:
        fieldnames.extend(['Is_Incomplete_Assembly', 'Missing_Codons'])
        
    codon_cols = [c for c in fieldnames if len(c) == 3 and c.upper() == c]
    
    incomplete_count = 0
    for row in rows:
        missing = []
        species_name = row.get('Species', '')
        
        # In vertebrate_tai.csv, all are vertebrates.
        # In merged_tai.csv, we must check if species_name is in vertebrate_species.
        is_vert = ('vertebrate' in filepath) or (species_name in vertebrate_species)
        
        if is_vert:
            for c in codon_cols:
                try:
                    val = float(row[c])
                    if val == 0.0:
                        missing.append(c)
                except:
                    pass
                
        row['Is_Incomplete_Assembly'] = 'True' if len(missing) > 0 else 'False'
        row['Missing_Codons'] = ','.join(missing) if len(missing) > 0 else ''
        if len(missing) > 0:
            incomplete_count += 1
            
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> Flagged {incomplete_count} incomplete vertebrate rows.")
