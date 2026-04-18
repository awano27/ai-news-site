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
  if (host === 'localhost' || host === '127.0.0.1' || host === '') return;
  if (navigator && navigator.doNotTrack === '1') return;

  fetch('/config/analytics.json', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (cfg) {
      if (!cfg || !cfg.measurement_id) return;
      var id = String(cfg.measurement_id);
      if (!/^G-[A-Z0-9]{6,}$/.test(id)) return; // placeholder guard

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
    })
    .catch(function () { /* silent fail */ });
})();
