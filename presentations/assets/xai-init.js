// xai-init.js — Inject x.ai-inspired theme + navigation across presentation pages
(function () {
  if (window.__xaiInit) return; window.__xaiInit = true;

  const scriptEl = document.currentScript || (function(){
    const els = document.querySelectorAll('script[src*="xai-init.js"]');
    return els[els.length - 1] || null;
  })();
  const base = scriptEl ? new URL('./', scriptEl.src) : new URL('./', window.location);

  // Helper: add stylesheet once
  function ensureStylesheet(href, id) {
    if (id && document.getElementById(id)) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    if (id) link.id = id;
    document.head.appendChild(link);
  }

  // Helper: check if a sticky header already exists
  function hasNativeHeader() {
    const header = document.querySelector('.header, .top');
    if (!header) return false;
    const cs = getComputedStyle(header);
    return cs.position === 'sticky' || cs.position === 'fixed';
  }

  // Helper: detect reveal.js pages
  function isRevealPage() {
    return !!document.querySelector('.reveal');
  }

  // Build navigation root path relative to this script (it sits in presentations/assets/)
  const root = new URL('../', base); // presentations/

  // Inject CSS theme
  ensureStylesheet(new URL('xai-theme.css', base).href, 'xai-theme-css');

  // Enable body flags and background layers
  function attachBackground() {
    document.body.classList.add('xai-enabled');
    if (isRevealPage()) document.body.classList.add('reveal-page');
    // background layers (placed once)
    if (!document.querySelector('.xai-bg')) {
      const bg = document.createElement('div');
      bg.className = 'xai-bg';
      document.body.appendChild(bg);
    }
    if (!document.querySelector('.xai-grid')) {
      const grid = document.createElement('div');
      grid.className = 'xai-grid';
      document.body.appendChild(grid);
    }
  }

  function setActiveLink(el, href) {
    try {
      const here = new URL(window.location.href, window.location.origin);
      const target = new URL(href, window.location.origin);
      if (here.pathname.endsWith(target.pathname)) {
        el.classList.add('active');
      }
    } catch (e) { /* noop */ }
  }

  function addTopNav() {
    if (document.querySelector('.xai-nav')) return; // once
    const nav = document.createElement('header');
    nav.className = 'xai-nav';

    const left = document.createElement('a');
    left.href = new URL('index.html', root).href;
    left.className = 'xai-brand';
    left.innerHTML = '<span class="xai-dot"></span><span class="xai-title">AI News</span>';

    const links = document.createElement('nav');
    links.className = 'xai-links';

    const items = [
      { name: 'Home', href: new URL('index.html', root).href },
      { name: 'Ranking', href: new URL('ai_ranking_interactive.html', root).href },
      { name: 'Report', href: new URL('integrated_report.html', root).href },
      { name: 'Slides', href: new URL('day_slides_index.html', root).href },
      { name: 'Latest', href: new URL('ai_ranking_report_latest.html', root).href }
    ];
    items.forEach(i => {
      const a = document.createElement('a');
      a.className = 'xai-link';
      a.href = i.href;
      a.textContent = i.name;
      setActiveLink(a, i.href);
      links.appendChild(a);
    });

    nav.appendChild(left);
    nav.appendChild(links);
    document.body.appendChild(nav);
    document.body.classList.add('xai-padding');
  }

  function addCornerFab() {
    if (document.querySelector('.xai-fab')) return; // once
    const fab = document.createElement('a');
    fab.href = new URL('index.html', root).href;
    fab.className = 'xai-fab';
    fab.innerHTML = '<span class="xai-dot"></span><span>Presentations</span>';
    document.body.appendChild(fab);
  }

  function init() {
    attachBackground();
    // If the page already has its own sticky header, avoid stacking bars; show compact FAB instead
    if (hasNativeHeader()) {
      addCornerFab();
    } else {
      addTopNav();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();

