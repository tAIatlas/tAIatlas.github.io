/* ========================================
   main.js — Shared functionality
   Navigation, scroll animations, utilities
   ======================================== */

(function () {
  'use strict';

  // --- Mobile Navigation Toggle ---
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      navToggle.setAttribute('aria-expanded',
        navLinks.classList.contains('open'));
    });

    // Close on link click
    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('open');
      });
    });
  }

  // --- Active Nav Link ---
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPage || (currentPage === '' && href === 'index.html')) {
      link.classList.add('active');
    }
  });

  // --- Scroll Fade-In Animation ---
  const observerOptions = {
    root: null,
    rootMargin: '0px 0px -60px 0px',
    threshold: 0.1
  };

  const fadeObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        fadeObserver.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.fade-in').forEach(el => {
    fadeObserver.observe(el);
  });

  // --- Nav Background on Scroll ---
  const nav = document.querySelector('.nav');
  if (nav) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 40) {
        nav.classList.add('scrolled');
      } else {
        nav.classList.remove('scrolled');
      }
    }, { passive: true });
  }

  // --- Utility: Format Number ---
  window.taiUtils = {
    formatNumber(n) {
      if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
      return n.toString();
    },

    debounce(fn, delay) {
      let timer;
      return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
      };
    },

    escapeHtml(str) {
      const div = document.createElement('div');
      div.textContent = str;
      return div.innerHTML;
    },

    highlightMatch(text, query) {
      if (!query) return taiUtils.escapeHtml(text);
      const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(`(${escaped})`, 'gi');
      return taiUtils.escapeHtml(text).replace(regex, '<mark>$1</mark>');
    },

    getGroupClass(group) {
      const map = {
        'Mammal': 'mammal',
        'Bird': 'bird',
        'Fish': 'fish',
        'Reptile': 'reptile',
        'Amphibian': 'amphibian'
      };
      return map[group] || 'other';
    },

    // Load species data (cached)
    _dataCache: {},
    async loadSpeciesData(weightType = 'dosreis_dynamic') {
      if (this._dataCache[weightType]) return this._dataCache[weightType];
      const basePath = window.location.pathname.includes('explore') ||
                       window.location.pathname.includes('download') ||
                       window.location.pathname.includes('about')
                       ? '' : '';
      const resp = await fetch(`${basePath}data/species_tai_${weightType}.json`);
      if (!resp.ok) throw new Error(`Failed to load ${weightType} species data`);
      this._dataCache[weightType] = await resp.json();
      return this._dataCache[weightType];
    }
  };

})();
