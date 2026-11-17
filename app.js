(() => {
  'use strict';

  // Mobile navigation toggle
  const navToggle = document.getElementById('nav-toggle');
  const navLinks = document.getElementById('nav-links');

  function closeMobileNav() {
    if (!navToggle || !navLinks) return;
    navToggle.setAttribute('aria-expanded', 'false');
    navLinks.classList.remove('is-open');
  }

  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      const expanded = navToggle.getAttribute('aria-expanded') === 'true';
      navToggle.setAttribute('aria-expanded', String(!expanded));
      navLinks.classList.toggle('is-open', !expanded);
    });

    navLinks.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        if (window.innerWidth <= 1080) {
          closeMobileNav();
        }
      });
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && navLinks.classList.contains('is-open')) {
        closeMobileNav();
        navToggle.focus();
      }
    });
  }

  // Subtle progressive scroll reveal (respects prefers-reduced-motion)
  const revealItems = Array.from(document.querySelectorAll('.reveal'));
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (revealItems.length > 0 && !prefersReducedMotion && 'IntersectionObserver' in window) {
    document.documentElement.classList.add('has-reveal');
    const observer = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: '0px 0px -24px 0px' }
    );
    revealItems.forEach((el) => observer.observe(el));
  } else {
    revealItems.forEach((el) => el.classList.add('is-visible'));
  }

  // Accessible installation tabs (Manga vs Anime)
  const tabButtons = Array.from(document.querySelectorAll('[role="tab"]'));
  const tabPanels = Array.from(document.querySelectorAll('[role="tabpanel"]'));

  function activateTab(btn) {
    const targetId = btn.getAttribute('aria-controls');
    tabButtons.forEach((b) => {
      const selected = b === btn;
      b.setAttribute('aria-selected', String(selected));
      b.tabIndex = selected ? 0 : -1;
    });
    tabPanels.forEach((panel) => {
      panel.hidden = panel.id !== targetId;
    });
  }

  tabButtons.forEach((btn, idx) => {
    btn.addEventListener('click', () => activateTab(btn));
    btn.addEventListener('keydown', (e) => {
      let nextIdx = null;
      if (e.key === 'ArrowRight') nextIdx = (idx + 1) % tabButtons.length;
      if (e.key === 'ArrowLeft') nextIdx = (idx - 1 + tabButtons.length) % tabButtons.length;
      if (e.key === 'Home') nextIdx = 0;
      if (e.key === 'End') nextIdx = tabButtons.length - 1;
      if (nextIdx !== null) {
        e.preventDefault();
        tabButtons[nextIdx].focus();
        activateTab(tabButtons[nextIdx]);
      }
    });
  });

  if (tabButtons.length > 0 && window.location.hash) {
    const hash = window.location.hash.toLowerCase();
    const animeTab = document.getElementById('tab-anime');
    const mangaTab = document.getElementById('tab-manga');
    if (hash === '#aniyomi' && animeTab) activateTab(animeTab);
    if (hash === '#mihon' && mangaTab) activateTab(mangaTab);
  }

  // Copyable URL buttons with live region feedback
  const liveStatus = document.getElementById('copy-status');
  document.querySelectorAll('.copy-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const value = btn.getAttribute('data-copy');
      if (!value) return;
      try {
        await navigator.clipboard.writeText(value);
      } catch {
        const tmp = document.createElement('textarea');
        tmp.value = value;
        tmp.setAttribute('readonly', '');
        tmp.style.position = 'absolute';
        tmp.style.left = '-9999px';
        document.body.appendChild(tmp);
        tmp.select();
        document.execCommand('copy');
        document.body.removeChild(tmp);
      }
      const orig = btn.textContent;
      btn.textContent = 'Copiado!';
      btn.classList.add('copied');
      if (liveStatus) {
        liveStatus.textContent = `URL copiada: ${value}`;
      }
      setTimeout(() => {
        btn.textContent = orig;
        btn.classList.remove('copied');
      }, 1800);
    });
  });

  // Repository directory search & category filter
  const searchInput = document.getElementById('repo-search');
  const filterChips = Array.from(document.querySelectorAll('.filter-chip'));
  const repoCards = Array.from(document.querySelectorAll('.repo-card'));
  const directoryStatus = document.getElementById('directory-status');
  const emptyState = document.getElementById('repo-empty');
  const resetFiltersBtn = document.getElementById('reset-filters');

  if (repoCards.length > 0) {
    let activeCategory = 'all';
    let searchTerm = '';

    function applyDirectoryFilters() {
      const query = searchTerm.trim().toLowerCase();
      let visibleCount = 0;

      repoCards.forEach((card) => {
        const cardCat = card.getAttribute('data-category') || '';
        const haystack = (card.getAttribute('data-search') || card.textContent || '').toLowerCase();
        const matchesCat = activeCategory === 'all' || cardCat === activeCategory;
        const matchesQuery = !query || haystack.includes(query);
        const visible = matchesCat && matchesQuery;
        card.hidden = !visible;
        if (visible) visibleCount += 1;
      });

      if (directoryStatus) {
        directoryStatus.textContent =
          visibleCount === repoCards.length
            ? `Exibindo todos os ${repoCards.length} repositórios públicos da organização.`
            : `Exibindo ${visibleCount} de ${repoCards.length} repositórios públicos.`;
      }

      if (emptyState) {
        emptyState.hidden = visibleCount > 0;
      }
    }

    filterChips.forEach((chip) => {
      chip.addEventListener('click', () => {
        activeCategory = chip.getAttribute('data-category') || 'all';
        filterChips.forEach((c) => c.setAttribute('aria-pressed', String(c === chip)));
        applyDirectoryFilters();
      });
    });

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        searchTerm = e.target.value || '';
        applyDirectoryFilters();
      });
    }

    if (resetFiltersBtn) {
      resetFiltersBtn.addEventListener('click', () => {
        activeCategory = 'all';
        searchTerm = '';
        if (searchInput) searchInput.value = '';
        filterChips.forEach((c) =>
          c.setAttribute('aria-pressed', String(c.getAttribute('data-category') === 'all'))
        );
        applyDirectoryFilters();
        if (searchInput) searchInput.focus();
      });
    }
  }
})();
