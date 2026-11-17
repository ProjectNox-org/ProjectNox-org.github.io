(() => {
  'use strict';

  // Mobile navigation toggle
  const navToggle = document.getElementById('nav-toggle');
  const navLinks = document.getElementById('nav-links');
  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      const expanded = navToggle.getAttribute('aria-expanded') === 'true';
      navToggle.setAttribute('aria-expanded', String(!expanded));
      navLinks.classList.toggle('is-open', !expanded);
    });

    navLinks.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
          navToggle.setAttribute('aria-expanded', 'false');
          navLinks.classList.remove('is-open');
        }
      });
    });
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
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        e.preventDefault();
        const nextIdx = e.key === 'ArrowRight'
          ? (idx + 1) % tabButtons.length
          : (idx - 1 + tabButtons.length) % tabButtons.length;
        tabButtons[nextIdx].focus();
        activateTab(tabButtons[nextIdx]);
      }
    });
  });

  // Copyable URL buttons
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
      setTimeout(() => {
        btn.textContent = orig;
        btn.classList.remove('copied');
      }, 1800);
    });
  });

  // Repository category filter
  const filterChips = Array.from(document.querySelectorAll('.filter-chip'));
  const repoCards = Array.from(document.querySelectorAll('.repo-card'));

  filterChips.forEach((chip) => {
    chip.addEventListener('click', () => {
      const category = chip.getAttribute('data-category');
      filterChips.forEach((c) => c.setAttribute('aria-pressed', String(c === chip)));
      repoCards.forEach((card) => {
        const cardCat = card.getAttribute('data-category');
        card.hidden = category !== 'all' && cardCat !== category;
      });
    });
  });
})();
