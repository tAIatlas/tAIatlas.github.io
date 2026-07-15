/* ========================================
   search.js — Species Search with Autocomplete
   Works on both index.html and explore.html
   ======================================== */

(function () {
  'use strict';

  const searchInput = document.getElementById('species-search');
  const searchResults = document.getElementById('search-results');

  if (!searchInput || !searchResults) return;

  let speciesList = [];
  let commonNames = {};
  let selectedIndex = -1;

  // Load data
  async function init() {
    try {
      try {
        const cnResp = await fetch('data/common_names.json');
        if (cnResp.ok) commonNames = await cnResp.json();
      } catch (e) { console.warn('Common names not available:', e); }

      const data = await taiUtils.loadSpeciesData();
      speciesList = data.species.map(s => ({
        name: s.species,
        group: s.group,
        common: commonNames[s.species] || ''
      }));
    } catch (err) {
      console.error('Failed to load species data for search:', err);
    }
  }

  function showResults(results, query) {
    if (results.length === 0 || query.length < 2) {
      searchResults.classList.remove('active');
      searchResults.innerHTML = '';
      return;
    }

    selectedIndex = -1;
    const html = results.slice(0, 12).map((item, i) => {
      const groupClass = taiUtils.getGroupClass(item.group);
      const highlightedName = taiUtils.highlightMatch(item.name, query);
      const displayName = item.common 
        ? `<span style="font-weight:600; color:var(--text-primary);">${taiUtils.highlightMatch(item.common, query)}</span> <span style="font-size:0.85em; font-style:italic; color:var(--text-secondary);">(${highlightedName})</span>`
        : highlightedName;
      return `<div class="search-result-item" data-index="${i}" data-species="${taiUtils.escapeHtml(item.name)}" role="option">
        <span class="species-name">${displayName}</span>
        <span class="species-group group-badge ${groupClass}">${taiUtils.escapeHtml(item.group)}</span>
      </div>`;
    }).join('');

    searchResults.innerHTML = html;
    searchResults.classList.add('active');

    // Click handlers
    searchResults.querySelectorAll('.search-result-item').forEach(el => {
      el.addEventListener('click', () => {
        const species = el.dataset.species;
        navigateToSpecies(species);
      });
    });
  }

  function navigateToSpecies(species) {
    // If on index page, navigate to explore with query param
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    if (currentPage === 'index.html' || currentPage === '' || currentPage === '/') {
      window.location.href = `explore.html?species=${encodeURIComponent(species)}`;
    } else if (currentPage === 'explore.html') {
      // Trigger species detail view
      if (window.showSpeciesDetail) {
        window.showSpeciesDetail(species);
      }
      searchInput.value = species;
      searchResults.classList.remove('active');
    }
  }

  function filterSpecies(query) {
    if (!query || query.length < 2) return [];
    const lower = query.toLowerCase();
    // Prioritize starts-with matches
    const starts = [];
    const contains = [];
    for (const item of speciesList) {
      const nameLower = item.name.toLowerCase();
      const commonLower = item.common.toLowerCase();
      if (nameLower.startsWith(lower) || commonLower.startsWith(lower)) {
        starts.push(item);
      } else if (nameLower.includes(lower) || commonLower.includes(lower)) {
        contains.push(item);
      }
    }
    return [...starts, ...contains];
  }

  // Input handler
  searchInput.addEventListener('input', taiUtils.debounce(function () {
    const query = this.value.trim();
    const results = filterSpecies(query);
    showResults(results, query);
  }, 150));

  // Keyboard navigation
  searchInput.addEventListener('keydown', (e) => {
    const items = searchResults.querySelectorAll('.search-result-item');
    if (!items.length) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
      updateSelected(items);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, 0);
      updateSelected(items);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      // If nothing is selected but results exist, pick the first one
      const indexToSelect = selectedIndex >= 0 ? selectedIndex : 0;
      if (items[indexToSelect]) {
        const species = items[indexToSelect].dataset.species;
        navigateToSpecies(species);
      }
    } else if (e.key === 'Escape') {
      searchResults.classList.remove('active');
    }
  });

  function updateSelected(items) {
    items.forEach((el, i) => {
      el.style.background = i === selectedIndex ? 'rgba(0, 212, 255, 0.1)' : '';
    });
    if (items[selectedIndex]) {
      items[selectedIndex].scrollIntoView({ block: 'nearest' });
    }
  }

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
      searchResults.classList.remove('active');
    }
  });

  // Focus re-opens
  searchInput.addEventListener('focus', () => {
    const query = searchInput.value.trim();
    if (query.length >= 2) {
      const results = filterSpecies(query);
      showResults(results, query);
    }
  });

  // Initialize
  init();

})();
