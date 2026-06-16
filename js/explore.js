/* ========================================
   explore.js — Species Explorer
   Table, sorting, filtering, bar chart
   ======================================== */

(function () {
  'use strict';

  let allSpecies = [];
  let codons = [];
  let filteredSpecies = [];
  let sortCol = 'species';
  let sortDir = 'asc';

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
      const data = await taiUtils.loadSpeciesData();
      allSpecies = data.species;
      codons = data.metadata.codons;

      // Populate group filter
      if (filterSelect) {
        const groups = Object.keys(data.metadata.groups).sort();
        groups.forEach(g => {
          const opt = document.createElement('option');
          opt.value = g;
          opt.textContent = `${g} (${data.metadata.groups[g]})`;
          filterSelect.appendChild(opt);
        });
      }

      applyFilters();
      if (loadingEl) loadingEl.style.display = 'none';

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
      const matchQuery = !query || s.species.toLowerCase().includes(query);
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
      return `<tr data-species="${taiUtils.escapeHtml(s.species)}">
        <td class="species-cell">${taiUtils.escapeHtml(s.species)}</td>
        <td><span class="group-badge ${groupClass}">${taiUtils.escapeHtml(s.group)}</span></td>
        <td>${mean}</td>
        <td>${max}</td>
      </tr>`;
    }).join('');

    tableBody.innerHTML = html;

    // Row click
    tableBody.querySelectorAll('tr').forEach(row => {
      row.addEventListener('click', () => {
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

  // --- Species Detail / Bar Chart ---
  window.showSpeciesDetail = function (speciesName) {
    const species = allSpecies.find(s => s.species === speciesName);
    if (!species || !detailPanel) return;

    const header = detailPanel.querySelector('.species-detail-header h2');
    if (header) header.textContent = species.species;

    const groupEl = detailPanel.querySelector('.detail-group');
    if (groupEl) {
      const gc = taiUtils.getGroupClass(species.group);
      groupEl.className = `detail-group group-badge ${gc}`;
      groupEl.textContent = species.group;
    }

    // Build bar chart
    renderBarChart(species);

    // Show panel
    detailPanel.classList.add('active');
    detailPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  function renderBarChart(species) {
    const chartEl = document.getElementById('codon-chart');
    if (!chartEl) return;

    const values = codons.map(c => species.codons[c] || 0);
    const maxVal = Math.max(...values, 1);

    // Create bars
    const chartHeight = 280; // px, matches CSS .bar-chart height minus padding
    const barsHtml = codons.map((codon, i) => {
      const val = values[i];
      const heightPx = Math.max(2, (val / maxVal) * chartHeight);
      return `<div class="bar-wrapper">
        <div class="bar-value">${val.toFixed(1)}</div>
        <div class="bar" style="height: 2px" data-height="${heightPx}" title="${codon}: ${val.toFixed(1)}"></div>
        <div class="bar-label">${codon}</div>
      </div>`;
    }).join('');

    chartEl.innerHTML = `<div class="bar-chart">${barsHtml}</div>`;

    // Animate bars in
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        chartEl.querySelectorAll('.bar').forEach(bar => {
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
    });
  }

  // Init
  init();

})();
