/* ========================================
   explore.js — Species Explorer
   Table, sorting, filtering, bar chart
   ======================================== */

(function () {
  'use strict';

  let allSpecies = [];
  let codons = [];
  let filteredSpecies = [];
  let commonNames = {};
  let sortCol = 'group';
  let sortDir = 'asc';
  // Default weight type
  let currentWeightType = 'gtai';

  // Clean display name: "Vertebrate (Mammal)" -> "Mammal", "Eukaryote (Other)" -> "Other Eukaryotes"
  function displayGroupName(g) {
    if (g.startsWith('Vertebrate (') && g.endsWith(')')) return g.slice(12, -1);
    if (g === 'Eukaryote (Other)') return 'Other Eukaryotes';
    return g;
  }

  const tableBody = document.getElementById('species-table-body');
  const filterSelect = document.getElementById('group-filter');
  const searchInput = document.getElementById('species-search');
  const speciesCountEl = document.getElementById('species-count');
  const detailPanel = document.getElementById('species-detail');
  const loadingEl = document.getElementById('loading');

  if (!tableBody) return;

  // --- Init ---
  async function init() {
    try {
      if (loadingEl) loadingEl.style.display = 'block';

      // Load common names on first call
      if (Object.keys(commonNames).length === 0) {
        try {
          const cnResp = await fetch('data/common_names.json');
          if (cnResp.ok) commonNames = await cnResp.json();
        } catch (e) { console.warn('Common names not available:', e); }
      }

      const data = await taiUtils.loadSpeciesData(currentWeightType);
      allSpecies = data.species;
      codons = data.metadata.codons;

      // Re-populate group filter based on the new dataset
      if (filterSelect) {
        const currentSelection = filterSelect.value;
        // Clear all options
        filterSelect.innerHTML = '';

        // Custom order: most complex organisms first
        const groupOrder = [
          'Vertebrate (Mammal)',
          'Vertebrate (Bird)',
          'Vertebrate (Reptile)',
          'Vertebrate (Amphibian)',
          'Vertebrate (Fish)',
          'Eukaryote (Other)',
          'Bacteria',
          'Archaea'
        ];


        const groups = Object.keys(data.metadata.groups);
        const orderedGroups = groupOrder.filter(g => groups.includes(g));
        // Add any groups not in our custom order at the end
        groups.forEach(g => { if (!orderedGroups.includes(g)) orderedGroups.push(g); });

        let selectionExists = false;
        orderedGroups.forEach(g => {
          const opt = document.createElement('option');
          opt.value = g;
          opt.textContent = `${displayGroupName(g)} (${data.metadata.groups[g]})`;
          filterSelect.appendChild(opt);
          if (g === currentSelection) selectionExists = true;
        });
        
        // Default to Mammals on first load, otherwise preserve selection
        if (selectionExists && currentSelection) {
          filterSelect.value = currentSelection;
        } else {
          filterSelect.value = 'Vertebrate (Mammal)';
        }
      }

      applyFilters();
      if (loadingEl) loadingEl.style.display = 'none';
      
      // Re-render open detail panel if active
      if (detailPanel && detailPanel.classList.contains('active')) {
          const header = detailPanel.querySelector('.species-detail-header h2');
          if (header) showSpeciesDetail(header.textContent);
      }

      // Check URL params
      const params = new URLSearchParams(window.location.search);
      const speciesParam = params.get('species');
      if (speciesParam) {
        showSpeciesDetail(speciesParam);
        if (searchInput) searchInput.value = speciesParam;
      }
    } catch (err) {
      console.error('Failed to load data:', err);
      if (loadingEl) {
        loadingEl.innerHTML = '<span style="color:#ff6b6b">Failed to load data. Make sure you are serving via HTTP server.</span>';
      }
    }
  }

  // --- Filtering ---
  function applyFilters() {
    const query = searchInput ? searchInput.value.trim().toLowerCase() : '';
    const group = filterSelect ? filterSelect.value : '';

    filteredSpecies = allSpecies.filter(s => {
      const cn = (commonNames[s.species] || '').toLowerCase();
      const matchQuery = !query || s.species.toLowerCase().includes(query) || cn.includes(query);
      const matchGroup = !group || s.group === group;
      return matchQuery && matchGroup;
    });

    sortSpecies();
    renderTable();
    updateCount();
  }

  // --- Sorting ---
  function sortSpecies() {
    filteredSpecies.sort((a, b) => {
      let va, vb;
      if (sortCol === 'species') {
        va = a.species.toLowerCase();
        vb = b.species.toLowerCase();
      } else if (sortCol === 'group') {
        va = a.group.toLowerCase();
        vb = b.group.toLowerCase();
      } else if (sortCol === 'mean_wi') {
        va = calcMean(a);
        vb = calcMean(b);
      } else if (sortCol === 'max_wi') {
        va = calcMax(a);
        vb = calcMax(b);
      }
      
      if (va < vb) return sortDir === 'asc' ? -1 : 1;
      if (va > vb) return sortDir === 'asc' ? 1 : -1;
      
      // Tiebreaker by species name
      const sa = a.species.toLowerCase();
      const sb = b.species.toLowerCase();
      if (sa < sb) return -1;
      if (sa > sb) return 1;
      return 0;
    });
  }

  function calcMean(species) {
    const vals = Object.values(species.codons);
    return vals.reduce((s, v) => s + v, 0) / vals.length;
  }

  function calcMax(species) {
    return Math.max(...Object.values(species.codons));
  }

  function calcMin(species) {
    return Math.min(...Object.values(species.codons));
  }

  // --- Render Table ---
  function renderTable() {
    const displaySpecies = filteredSpecies.slice(0, 200); // Cap for performance
    const html = displaySpecies.map(s => {
      const groupClass = taiUtils.getGroupClass(s.group);
      const mean = calcMean(s).toFixed(3);
      const max = calcMax(s).toFixed(3);
      const isProkaryote = s.group === 'Bacteria' || s.group === 'Archaea';
      const warningIcon = '';
      const cn = commonNames[s.species];
      const nameHtml = cn
        ? `<span style="font-weight:600; color: var(--text-primary);">${taiUtils.escapeHtml(cn)}</span> <span style="font-style:italic; color: var(--text-secondary); font-size:0.85em;">(${taiUtils.escapeHtml(s.species)})</span>`
        : `<span style="font-style:italic;">${taiUtils.escapeHtml(s.species)}</span>`;
      return `<tr data-species="${taiUtils.escapeHtml(s.species)}">
        <td class="species-cell">${nameHtml}${warningIcon}</td>
        <td><span class="group-badge ${groupClass}">${taiUtils.escapeHtml(displayGroupName(s.group))}</span></td>
        <td>${mean}</td>
        <td>${max}</td>
      </tr>`;
    }).join('');

    tableBody.innerHTML = html;

    // Row click
    tableBody.querySelectorAll('tr').forEach(row => {
      row.addEventListener('click', () => {
        tableBody.querySelectorAll('tr').forEach(r => r.classList.remove('selected'));
        row.classList.add('selected');

        const container = document.getElementById('table-scroll-container');
        if (container) {
          container.style.maxHeight = '95px';
          setTimeout(() => {
            container.scrollTo({ top: row.offsetTop - 48, behavior: 'smooth' });
          }, 150);
        }

        showSpeciesDetail(row.dataset.species);
      });
    });
  }

  function updateCount() {
    if (speciesCountEl) {
      speciesCountEl.textContent = `${filteredSpecies.length} species`;
      if (filteredSpecies.length < allSpecies.length) {
        speciesCountEl.textContent += ` of ${allSpecies.length}`;
      }
      if (filteredSpecies.length > 200) {
        speciesCountEl.textContent += ' (showing first 200)';
      }
    }
  }

  // --- Column Sort ---
  document.querySelectorAll('.data-table th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.sort;
      if (sortCol === col) {
        sortDir = sortDir === 'asc' ? 'desc' : 'asc';
      } else {
        sortCol = col;
        sortDir = 'asc';
      }

      // Update arrow displays
      document.querySelectorAll('.data-table th').forEach(h => {
        h.classList.remove('sorted');
        const arrow = h.querySelector('.sort-arrow');
        if (arrow) arrow.textContent = '↕';
      });
      th.classList.add('sorted');
      const arrow = th.querySelector('.sort-arrow');
      if (arrow) arrow.textContent = sortDir === 'asc' ? '↑' : '↓';

      sortSpecies();
      renderTable();
    });
  });

  // --- Event Listeners ---
  if (filterSelect) {
    filterSelect.addEventListener('change', applyFilters);
  }
  if (searchInput) {
    searchInput.addEventListener('input', taiUtils.debounce(applyFilters, 200));
  }
  
  // Weight toggle listener
  const btnGtai = document.getElementById('btn-gtai');
  const selectClassical = document.getElementById('select-classical');
  if (btnGtai && selectClassical) {
    btnGtai.addEventListener('click', () => {
      if (currentWeightType !== 'gtai') {
        currentWeightType = 'gtai';
        btnGtai.classList.add('btn-primary');
        btnGtai.classList.remove('btn-secondary');
        selectClassical.value = "";
        init();
      }
    });

    selectClassical.addEventListener('change', (e) => {
      if (e.target.value && e.target.value !== currentWeightType) {
        currentWeightType = e.target.value;
        btnGtai.classList.remove('btn-primary');
        btnGtai.classList.add('btn-secondary');
        init();
      }
    });
  }

  // --- Species Detail / Bar Chart ---
  window.showSpeciesDetail = function (speciesName, altIndex = -1) {
    const rootSpecies = allSpecies.find(s => s.species === speciesName);
    if (!rootSpecies || !detailPanel) return;

    const activeSpecies = altIndex >= 0 ? rootSpecies.alternates[altIndex] : rootSpecies;

    const headerContainer = detailPanel.querySelector('.species-detail-header div');
    if (headerContainer) {
      const detailCN = commonNames[rootSpecies.species];
      let titleHtml = detailCN
        ? `<h2 style="display: inline-block; margin-right: 12px; margin-bottom: 0;">${detailCN}</h2><span style="font-style: italic; font-size: 1.1rem; color: var(--text-secondary);">${rootSpecies.species}</span>`
        : `<h2 style="font-style: italic; display: inline-block; margin-right: 12px; margin-bottom: 0;">${rootSpecies.species}</h2>`;
      
      if (rootSpecies.alternates && rootSpecies.alternates.length > 0) {
        titleHtml += `<select id="assembly-select" style="padding: 4px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg-alt); color: var(--text);">`;
        const pSel = altIndex === -1 ? 'selected' : '';
        titleHtml += `<option value="-1" ${pSel}>${rootSpecies.accession} (Primary)</option>`;
        rootSpecies.alternates.forEach((alt, idx) => {
          const aSel = idx === altIndex ? 'selected' : '';
          titleHtml += `<option value="${idx}" ${aSel}>${alt.accession} (Alternate)</option>`;
        });
        titleHtml += `</select>`;
      } else if (rootSpecies.accession) {
        titleHtml += `<span style="font-size: 0.9em; color: var(--text-muted);">(${rootSpecies.accession})</span>`;
      }
      
      const gc = taiUtils.getGroupClass(rootSpecies.group);
      titleHtml += `<br><span class="detail-group group-badge ${gc}" style="margin-top: 8px; display: inline-block;">${displayGroupName(rootSpecies.group)}</span>`;
      
      const isProkaryote = rootSpecies.group === 'Bacteria' || rootSpecies.group === 'Archaea';
      if (activeSpecies.is_incomplete && !isProkaryote) {
        titleHtml += `<div class="incomplete-warning" style="margin-top: 16px; padding: 10px 12px; background: var(--bg-alt); border-left: 3px solid #ffb703; border-radius: 4px; color: var(--text-secondary); font-size: 0.85rem; display: flex; align-items: flex-start; gap: 8px;">
          <span style="color: #ffb703; font-size: 1.1rem; line-height: 1;">⚠️</span>
          <span><strong>Note on Draft Assembly:</strong> This genome is missing explicit tRNA genes for ${activeSpecies.missing_codons.length} codon(s): <span style="font-family: var(--font-mono); color: var(--text-primary);">${activeSpecies.missing_codons.join(', ')}</span>. Relative metrics for these specific codons may be skewed.</span>
        </div>`;
      }

      headerContainer.innerHTML = titleHtml;

      const sel = document.getElementById('assembly-select');
      if (sel) {
        sel.addEventListener('change', (e) => {
          showSpeciesDetail(rootSpecies.species, parseInt(e.target.value));
        });
      }
    }

    // Build bar chart
    renderBarChart(activeSpecies);

    // Show panel
    detailPanel.classList.add('active');
    detailPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const geneticCode = {
    'TTT': 'Phe', 'TTC': 'Phe',
    'TTA': 'Leu', 'TTG': 'Leu', 'CTT': 'Leu', 'CTC': 'Leu', 'CTA': 'Leu', 'CTG': 'Leu',
    'ATT': 'Ile', 'ATC': 'Ile', 'ATA': 'Ile',
    'ATG': 'Met',
    'GTT': 'Val', 'GTC': 'Val', 'GTA': 'Val', 'GTG': 'Val',
    'TCT': 'Ser', 'TCC': 'Ser', 'TCA': 'Ser', 'TCG': 'Ser', 'AGT': 'Ser', 'AGC': 'Ser',
    'CCT': 'Pro', 'CCC': 'Pro', 'CCA': 'Pro', 'CCG': 'Pro',
    'ACT': 'Thr', 'ACC': 'Thr', 'ACA': 'Thr', 'ACG': 'Thr',
    'GCT': 'Ala', 'GCC': 'Ala', 'GCA': 'Ala', 'GCG': 'Ala',
    'TAT': 'Tyr', 'TAC': 'Tyr',
    'CAT': 'His', 'CAC': 'His',
    'CAA': 'Gln', 'CAG': 'Gln',
    'AAT': 'Asn', 'AAC': 'Asn',
    'AAA': 'Lys', 'AAG': 'Lys',
    'GAT': 'Asp', 'GAC': 'Asp',
    'GAA': 'Glu', 'GAG': 'Glu',
    'TGT': 'Cys', 'TGC': 'Cys',
    'TGG': 'Trp',
    'CGT': 'Arg', 'CGC': 'Arg', 'CGA': 'Arg', 'CGG': 'Arg', 'AGA': 'Arg', 'AGG': 'Arg',
    'GGT': 'Gly', 'GGC': 'Gly', 'GGA': 'Gly', 'GGG': 'Gly'
  };

  // Okabe-Ito Colorblind-Friendly Palette with variations for each AA within a class
  const aaColors = {
    // Acidic (Vermilion variations)
    'Asp': '#D55E00', 'Glu': '#B85100',
    // Basic (Blue variations)
    'Arg': '#0072B2', 'Lys': '#0082CC', 'His': '#006299',
    // Polar Uncharged (Sky Blue variations)
    'Asn': '#56B4E9', 'Gln': '#4AA4D5',
    // Hydroxyl (Orange variations)
    'Ser': '#E69F00', 'Thr': '#D29100',
    // Sulfur (Yellow variations)
    'Cys': '#F0E442', 'Met': '#DCD03B',
    // Aliphatic/Hydrophobic (Bluish Green variations)
    'Leu': '#009E73', 'Val': '#00B383', 'Ile': '#008A64',
    // Aromatic (Reddish Purple variations)
    'Phe': '#CC79A7', 'Tyr': '#D88DB5', 'Trp': '#C06699',
    // Special/Small (Grey variations)
    'Gly': '#999999', 'Ala': '#B3B3B3', 'Pro': '#808080'
  };

  function renderBarChart(species) {
    const chartAaEl = document.getElementById('codon-chart-aa');
    const chartDescEl = document.getElementById('codon-chart-desc');
    if (!chartAaEl || !chartDescEl) return;

    const values = codons.map(c => species.codons[c] || 0);

    // Build data objects for each codon
    const codonData = codons.map(c => {
      const val = species.codons[c] || 0;
      const aa = geneticCode[c] || 'Unknown';
      const color = aaColors[aa] || '#00d4ff';
      return { codon: c, val: val, aa: aa, color: color };
    });

    const maxVal = Math.max(...codonData.map(d => d.val), 1);
    const chartHeight = 280;

    // 1. Chart Grouped by Amino Acid
    const aaGroups = {};
    [...codonData].forEach(d => {
      if (!aaGroups[d.aa]) aaGroups[d.aa] = [];
      aaGroups[d.aa].push(d);
    });
    
    const sortedAAs = Object.keys(aaGroups).sort();
    
    let groupedHtml = '';
    sortedAAs.forEach(aa => {
       const bars = aaGroups[aa].sort((a, b) => b.val - a.val);
       const barsHtml = bars.map(d => {
         const heightPx = Math.max(2, (d.val / maxVal) * chartHeight);
         const labelStyle = d.val === 0 ? 'color: #ff4444; font-weight: 800;' : '';
         return `<div class="bar-wrapper">
           <div class="bar-value">${d.val.toFixed(2)}</div>
           <div class="bar" style="height: 2px; background: ${d.color}; box-shadow: 0 0 10px ${d.color}40;" data-height="${heightPx}" title="${d.aa} (${d.codon}): ${d.val.toFixed(3)}"></div>
           <div class="bar-label" style="${labelStyle}">${d.codon}</div>
         </div>`;
       }).join('');
       
       groupedHtml += `<div class="aa-group" style="display: flex; flex-direction: column; align-items: center; margin: 0 2px; flex: ${bars.length}; min-width: 0;">
         <div style="display: flex; gap: 2px; height: 100%; align-items: flex-end; width: 100%; justify-content: center;">${barsHtml}</div>
         <div style="font-weight: 700; font-size: 0.85rem; color: var(--text-primary); margin-top: 12px; white-space: nowrap;">${aa}</div>
       </div>`;
    });
    
    chartAaEl.innerHTML = `<div class="bar-chart" style="justify-content: center; gap: 4px;">${groupedHtml}</div>`;

    // 2. Chart Sorted by Descending Value
    const descSorted = [...codonData].sort((a, b) => b.val - a.val);
    const descHtml = descSorted.map(d => {
      const heightPx = Math.max(2, (d.val / maxVal) * chartHeight);
      const labelStyle = d.val === 0 ? 'color: #ff4444; font-weight: 800;' : '';
      return `<div class="bar-wrapper">
        <div class="bar-value">${d.val.toFixed(2)}</div>
        <div class="bar" style="height: 2px; background: ${d.color}; box-shadow: 0 0 10px ${d.color}40;" data-height="${heightPx}" title="${d.aa} (${d.codon}): ${d.val.toFixed(3)}"></div>
        <div class="bar-label" style="${labelStyle}">${d.codon}</div>
        <div class="bar-aa-label" style="font-size: 0.65rem; font-weight: 600; color: var(--text-secondary); margin-top: 10px;">${d.aa}</div>
      </div>`;
    }).join('');
    
    chartDescEl.innerHTML = `<div class="bar-chart">${descHtml}</div>`;

    // Animate bars in
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        document.querySelectorAll('.bar-chart .bar').forEach(bar => {
          bar.style.height = bar.dataset.height + 'px';
        });
      });
    });

    // Stats summary
    const statsEl = document.getElementById('detail-stats');
    if (statsEl) {
      const mean = calcMean(species).toFixed(4);
      const max = calcMax(species).toFixed(4);
      const min = calcMin(species).toFixed(4);
      const maxCodon = codons[values.indexOf(Math.max(...values))];
      const minCodon = codons[values.indexOf(Math.min(...values))];
      const rawMax = species.raw_max_wi ? species.raw_max_wi.toFixed(1) : 'N/A';
      statsEl.innerHTML = `
        <div class="detail-stat">
          <span class="detail-stat-label">Mean w<sub>i</sub></span>
          <span class="detail-stat-value">${mean}</span>
        </div>
        <div class="detail-stat">
          <span class="detail-stat-label">Max w<sub>i</sub></span>
          <span class="detail-stat-value">${max} <small>(${maxCodon})</small></span>
        </div>
        <div class="detail-stat">
          <span class="detail-stat-label">Min w<sub>i</sub></span>
          <span class="detail-stat-value">${min} <small>(${minCodon})</small></span>
        </div>
        <div class="detail-stat">
          <span class="detail-stat-label">Codons</span>
          <span class="detail-stat-value">${codons.length}</span>
        </div>
        <div class="detail-stat">
          <span class="detail-stat-label">Raw Max W<sub>i</sub></span>
          <span class="detail-stat-value">${rawMax}</span>
        </div>`;
    }
  }

  // Close detail
  const closeBtn = document.getElementById('close-detail');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      if (detailPanel) detailPanel.classList.remove('active');
      const tableBody = document.getElementById('species-table-body');
      if (tableBody) tableBody.querySelectorAll('tr').forEach(r => r.classList.remove('selected'));
      
      const container = document.getElementById('table-scroll-container');
      if (container) container.style.maxHeight = '600px';
    });
  }

  // Init
  init();

})();
