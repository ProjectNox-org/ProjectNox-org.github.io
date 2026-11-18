(() => {
  'use strict';

  function normalizeText(value) {
    return (value || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');
  }

  // Accessible installation tabs (Progressive Enhancement: both panels visible when JS is disabled)
  const tabButtons = Array.from(document.querySelectorAll('[role="tab"]'));
  const tabPanels = Array.from(document.querySelectorAll('[role="tabpanel"]'));

  function activateTab(btn, updateHash = false) {
    if (!btn) return;
    const targetId = btn.getAttribute('aria-controls');
    tabButtons.forEach((b) => {
      const selected = b === btn;
      b.setAttribute('aria-selected', String(selected));
      b.tabIndex = selected ? 0 : -1;
    });
    tabPanels.forEach((panel) => {
      panel.hidden = panel.id !== targetId;
    });
    if (updateHash) {
      const targetHash = btn.id === 'tab-anime' ? '#aniyomi' : '#mihon';
      if (window.location.hash.toLowerCase() !== targetHash) {
        history.replaceState(null, '', targetHash);
      }
    }
  }

  function syncTabFromHash() {
    if (tabButtons.length === 0) return;
    const hash = window.location.hash.toLowerCase();
    const animeTab = document.getElementById('tab-anime');
    const mangaTab = document.getElementById('tab-manga');
    if (hash === '#aniyomi' && animeTab) {
      activateTab(animeTab, false);
    } else if (mangaTab) {
      activateTab(mangaTab, false);
    }
  }

  tabButtons.forEach((btn, idx) => {
    btn.addEventListener('click', () => activateTab(btn, true));
    btn.addEventListener('keydown', (e) => {
      let nextIdx = null;
      if (e.key === 'ArrowRight') nextIdx = (idx + 1) % tabButtons.length;
      if (e.key === 'ArrowLeft') nextIdx = (idx - 1 + tabButtons.length) % tabButtons.length;
      if (e.key === 'Home') nextIdx = 0;
      if (e.key === 'End') nextIdx = tabButtons.length - 1;
      if (nextIdx !== null) {
        e.preventDefault();
        tabButtons[nextIdx].focus();
        activateTab(tabButtons[nextIdx], true);
      }
    });
  });

  if (tabButtons.length > 0) {
    syncTabFromHash();
    window.addEventListener('hashchange', syncTabFromHash);
  }

  // Optional ambient motion pause control (CSS + external banner SVG animations per variant)
  const motionToggle = document.getElementById('motion-toggle');
  const svgTextCache = new Map();
  let motionRequestSeq = 0;

  async function createPausedSvgBlob(url, seq) {
    if (!url || !url.toLowerCase().includes('.svg')) return null;
    try {
      let rawSvg = svgTextCache.get(url);
      if (!rawSvg) {
        const resp = await fetch(url, { cache: 'force-cache' });
        if (!resp.ok) return null;
        rawSvg = await resp.text();
        svgTextCache.set(url, rawSvg);
      }
      if (seq !== motionRequestSeq || document.documentElement.getAttribute('data-motion') !== 'paused') {
        return null;
      }
      if (!rawSvg.includes('</svg>')) return null;
      const pausedSvg = rawSvg.replace(
        '</svg>',
        '<style data-nox-paused="true">*,*::before,*::after{animation-play-state:paused!important;}</style></svg>'
      );
      return URL.createObjectURL(new Blob([pausedSvg], { type: 'image/svg+xml' }));
    } catch {
      return null;
    }
  }

  function revokeNodeBlob(node) {
    if (node && node.dataset && node.dataset.pausedBlobUrl) {
      URL.revokeObjectURL(node.dataset.pausedBlobUrl);
      delete node.dataset.pausedBlobUrl;
    }
  }

  async function pauseBannerSvgs(seq) {
    const imgs = Array.from(document.querySelectorAll('.banner-inner img'));
    if (imgs.length === 0) return { ok: true };

    let allOk = true;
    await Promise.all(
      imgs.map(async (img) => {
        if (!img.dataset.origSrc) {
          img.dataset.origSrc = img.getAttribute('src') || '';
        }
        const picture = img.closest('picture');
        const sources = picture ? Array.from(picture.querySelectorAll('source')) : [];

        const sourceTasks = sources.map(async (source) => {
          if (!source.dataset.origSrcset) {
            source.dataset.origSrcset = source.getAttribute('srcset') || '';
          }
          const orig = source.dataset.origSrcset;
          if (!orig) return;
          const blobUrl = await createPausedSvgBlob(orig, seq);
          if (seq !== motionRequestSeq || document.documentElement.getAttribute('data-motion') !== 'paused') {
            if (blobUrl) URL.revokeObjectURL(blobUrl);
            return;
          }
          if (!blobUrl) {
            allOk = false;
            return;
          }
          revokeNodeBlob(source);
          source.dataset.pausedBlobUrl = blobUrl;
          source.setAttribute('srcset', blobUrl);
        });

        const imgTask = (async () => {
          const orig = img.dataset.origSrc;
          if (!orig) return;
          const blobUrl = await createPausedSvgBlob(orig, seq);
          if (seq !== motionRequestSeq || document.documentElement.getAttribute('data-motion') !== 'paused') {
            if (blobUrl) URL.revokeObjectURL(blobUrl);
            return;
          }
          if (!blobUrl) {
            allOk = false;
            return;
          }
          revokeNodeBlob(img);
          img.dataset.pausedBlobUrl = blobUrl;
          img.setAttribute('src', blobUrl);
        })();

        await Promise.all([...sourceTasks, imgTask]);
      })
    );
    return { ok: allOk };
  }

  function resumeBannerSvgs() {
    document.querySelectorAll('.banner-inner img').forEach((img) => {
      const picture = img.closest('picture');
      if (picture) {
        picture.querySelectorAll('source').forEach((source) => {
          if (source.dataset.origSrcset) {
            source.setAttribute('srcset', source.dataset.origSrcset);
          }
          revokeNodeBlob(source);
        });
      }
      if (img.dataset.origSrc) {
        img.setAttribute('src', img.dataset.origSrc);
      }
      revokeNodeBlob(img);
    });
  }

  function updateMotionToggleUi(paused, svgOk = true) {
    if (!motionToggle) return;
    motionToggle.setAttribute('aria-pressed', String(paused));
    if (!paused) {
      delete motionToggle.dataset.svgStatus;
      motionToggle.textContent = 'Pausar animações';
    } else if (svgOk) {
      motionToggle.dataset.svgStatus = 'paused';
      motionToggle.textContent = 'Retomar animações';
    } else {
      motionToggle.dataset.svgStatus = 'partial';
      motionToggle.textContent = 'Retomar animações (CSS pausado)';
    }
  }

  async function applyMotionState(paused) {
    const seq = ++motionRequestSeq;
    if (paused) {
      document.documentElement.setAttribute('data-motion', 'paused');
      updateMotionToggleUi(true, true);
      const { ok } = await pauseBannerSvgs(seq);
      if (seq === motionRequestSeq && document.documentElement.getAttribute('data-motion') === 'paused') {
        updateMotionToggleUi(true, ok);
      }
    } else {
      document.documentElement.removeAttribute('data-motion');
      resumeBannerSvgs();
      updateMotionToggleUi(false, true);
    }
  }

  if (motionToggle) {
    let savedPref = null;
    try {
      savedPref = localStorage.getItem('nox-motion');
    } catch {
      savedPref = null;
    }
    const prefersReduced =
      typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const initialPaused = savedPref === 'paused' || (savedPref === null && prefersReduced);
    applyMotionState(initialPaused);
    motionToggle.addEventListener('click', () => {
      const nextPaused = document.documentElement.getAttribute('data-motion') !== 'paused';
      applyMotionState(nextPaused);
      try {
        localStorage.setItem('nox-motion', nextPaused ? 'paused' : 'active');
      } catch {
        // ignore storage errors
      }
    });
  }

  // Copyable URL buttons with verified success feedback
  const liveStatus = document.getElementById('copy-status');
  document.querySelectorAll('.copy-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const value = btn.getAttribute('data-copy');
      if (!value) return;

      let success = false;
      if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
        try {
          await navigator.clipboard.writeText(value);
          success = true;
        } catch {
          success = false;
        }
      }

      if (!success) {
        const tmp = document.createElement('textarea');
        tmp.value = value;
        tmp.setAttribute('readonly', '');
        tmp.style.position = 'absolute';
        tmp.style.left = '-9999px';
        document.body.appendChild(tmp);
        tmp.select();
        try {
          success = document.execCommand('copy');
        } catch {
          success = false;
        }
        document.body.removeChild(tmp);
      }

      const orig = btn.getAttribute('data-label') || btn.textContent;
      btn.setAttribute('data-label', orig);
      btn.classList.remove('copied', 'error');

      if (success) {
        btn.textContent = 'Copiado!';
        btn.classList.add('copied');
        if (liveStatus) liveStatus.textContent = `URL copiada: ${value}`;
      } else {
        btn.textContent = 'Erro ao copiar';
        btn.classList.add('error');
        if (liveStatus) liveStatus.textContent = 'Não foi possível copiar automaticamente.';
      }

      clearTimeout(btn._copyTimer);
      btn._copyTimer = setTimeout(() => {
        btn.textContent = orig;
        btn.classList.remove('copied', 'error');
      }, 1800);
    });
  });

  // Repository directory accent-insensitive search, clear button & keyboard-accessible filters
  const searchInput = document.getElementById('repo-search');
  const searchClear = document.getElementById('repo-clear');
  const filterChips = Array.from(document.querySelectorAll('.filter-chip'));
  const repoCards = Array.from(document.querySelectorAll('.repo-card'));
  const directoryStatus = document.getElementById('directory-status');
  const emptyState = document.getElementById('repo-empty');
  const resetFiltersBtn = document.getElementById('reset-filters');

  if (repoCards.length > 0) {
    let activeCategory = 'all';
    let searchTerm = '';

    function applyDirectoryFilters() {
      const query = normalizeText(searchTerm.trim());
      let visibleCount = 0;

      repoCards.forEach((card) => {
        const cardCat = card.getAttribute('data-category') || '';
        const haystack = normalizeText(card.getAttribute('data-search') || card.textContent || '');
        const matchesCat = activeCategory === 'all' || cardCat === activeCategory;
        const matchesQuery = !query || haystack.includes(query);
        const visible = matchesCat && matchesQuery;
        card.hidden = !visible;
        if (visible) visibleCount += 1;
      });

      if (searchClear) {
        searchClear.hidden = searchTerm.length === 0;
      }

      if (directoryStatus) {
        directoryStatus.textContent =
          visibleCount === repoCards.length && activeCategory === 'all' && !query
            ? `${repoCards.length} projetos disponíveis`
            : `${visibleCount} de ${repoCards.length} projetos`;
      }

      if (emptyState) {
        emptyState.hidden = visibleCount > 0;
      }
    }

    filterChips.forEach((chip, idx) => {
      chip.addEventListener('click', () => {
        activeCategory = chip.getAttribute('data-category') || 'all';
        filterChips.forEach((c) => c.setAttribute('aria-pressed', String(c === chip)));
        applyDirectoryFilters();
      });

      chip.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
          e.preventDefault();
          const nextIdx =
            e.key === 'ArrowRight'
              ? (idx + 1) % filterChips.length
              : (idx - 1 + filterChips.length) % filterChips.length;
          filterChips[nextIdx].focus();
        }
      });
    });

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        searchTerm = e.target.value || '';
        applyDirectoryFilters();
      });
    }

    if (searchClear) {
      searchClear.addEventListener('click', () => {
        searchTerm = '';
        if (searchInput) {
          searchInput.value = '';
          searchInput.focus();
        }
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
