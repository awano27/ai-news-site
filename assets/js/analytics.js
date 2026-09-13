/*
 * analytics.js — visionhub.jp
 * ------------------------------------------------------------
 * Loads Google Analytics 4 (GA4) with a Measurement ID pulled from
 * /config/analytics.json at runtime. This lets us swap / rotate the
 * ID without touching every HTML page.
 *
 * Behaviour:
 *   - No-ops if config is missing or the ID is a placeholder.
 *   - Respects Do-Not-Track and doesn't fire on localhost.
 *   - Emits a custom 'slide_view' event on day-slide pages with the
 *     date as a parameter so we can segment news-desk traffic.
 * ------------------------------------------------------------
 */
(function () {
  'use strict';

  if (window.__AIHUB_ANALYTICS_LOADED) return;
  window.__AIHUB_ANALYTICS_LOADED = true;

  var host = (location && location.hostname) || '';
  var allowLocal = window.__AIHUB_ANALYTICS_ALLOW_LOCALHOST === true
    || /(?:^|[?&])analytics_debug=1(?:&|$)/.test(location.search || '');
  if (!allowLocal && (host === 'localhost' || host === '127.0.0.1' || host === '')) return;
  if (navigator && navigator.doNotTrack === '1') return;

  fetch('/config/analytics.json', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (cfg) {
      if (!cfg || !cfg.measurement_id) return;
      var id = String(cfg.measurement_id);
      if (!/^G-[A-Z0-9]{6,}$/.test(id)) return; // placeholder guard
      if (/REPLACE|XXXX/i.test(id)) return;

      var s = document.createElement('script');
      s.async = true;
      s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(id);
      document.head.appendChild(s);

      window.dataLayer = window.dataLayer || [];
      function gtag(){ window.dataLayer.push(arguments); }
      window.gtag = gtag;
      gtag('js', new Date());
      gtag('config', id, {
        anonymize_ip: true,
        send_page_view: true
      });

      // Custom event for slide pages
      var m = /day_slide_(\d{4})_(\d{2})_(\d{2})\.html/.exec(location.pathname);
      if (m) {
        gtag('event', 'slide_view', {
          slide_date: m[1] + '-' + m[2] + '-' + m[3]
        });
      }

      var sentDepth = {};
      function sendDepth() {
        var doc = document.documentElement;
        var body = document.body;
        var scrollTop = window.pageYOffset || doc.scrollTop || 0;
        var height = Math.max(doc.scrollHeight, body ? body.scrollHeight : 0);
        var win = window.innerHeight || doc.clientHeight || 0;
        var denom = height - win;
        var pct = denom <= 0 ? 100 : Math.min(100, Math.round((scrollTop / denom) * 100));
        [25, 50, 75, 100].forEach(function (th) {
          if (pct >= th && !sentDepth[th]) {
            sentDepth[th] = true;
            gtag('event', 'scroll_depth', { percent: th, percent_scrolled: th });
          }
        });
      }
      window.addEventListener('scroll', sendDepth, { passive: true });
      sendDepth();

      document.addEventListener('click', function (ev) {
        var t = ev.target;
        if (!t || !t.closest) return;
        var cta = t.closest('[data-cta]');
        if (cta) {
          gtag('event', 'cta_click', {
            cta_id: cta.getAttribute('data-cta') || cta.id || '',
            link_url: cta.getAttribute('href') || ''
          });
          return;
        }
        var a = t.closest('a[href]');
        if (!a) return;
        var href = a.getAttribute('href') || '';
        try {
          var u = new URL(a.href, location.href);
          if (u.hostname && u.hostname !== location.hostname) {
            gtag('event', 'outbound_click', { link_domain: u.hostname, link_url: u.href });
          }
        } catch (err) {
          if (/^https?:\/\//i.test(href)) {
            gtag('event', 'outbound_click', { link_domain: href.split('/')[2] || '', link_url: href });
          }
        }
      });
    })
    .catch(function () { /* silent fail */ });
})();
