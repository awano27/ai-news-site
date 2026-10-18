#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const SLIDES_DIR = path.join(ROOT, 'presentations', 'day_slides');
const NEWS_DIR = path.join(ROOT, 'news');
const LATEST_JSON = path.join(NEWS_DIR, 'latest.json');
const INDEX_HTML = path.join(ROOT, 'index.html');
const ARCHIVE_INDEX_JSON = path.join(ROOT, 'public-pages', 'news', 'archive_index.json');
const DAY_SLIDES_LIST_JSON = path.join(ROOT, 'presentations', 'day_slides', 'list.json');
const DAY_SLIDES_META_JSON = path.join(ROOT, 'presentations', 'day_slides', 'meta_index.json');
const AUTO_DAILY_JSON = path.join(ROOT, 'public-pages', 'api', 'auto_daily_report', 'latest.json');
const DAILY_LATEST_JSON = path.join(ROOT, 'public-pages', 'news', 'daily_latest.json'); // legacy fallback only

const WEEKDAY_JP = ['日', '月', '火', '水', '木', '金', '土'];
const CATEGORY_LABELS = {
  business: 'BUSINESS · ビジネス',
  tools: 'TOOLS · ツール',
  company: 'COMPANY · 企業動向',
  sns: 'SNS · 注目の投稿',
  posts: 'POSTS · 解説',
  research: 'RESEARCH · 研究',
  tech: 'TECH · 技術',
};

// Source reviewed on 2026-10-18: this article covers an outdoor event, not AI.
// Exclude only this URL from homepage promotion; retain the source archives.
const HOMEPAGE_NEWS_EXCLUSIONS = new Set([
  'https://gigazine.net/news/20261017-sauna-camp-machiasobi31',
]);

function isHomepageNews(item) {
  try {
    const url = new URL(item && (item.url || sourceUrl(item)));
    return !HOMEPAGE_NEWS_EXCLUSIONS.has(url.origin + url.pathname.replace(/\/+$/, ''));
  } catch (_) {
    return true;
  }
}

const NAMED_ENTITIES = {
  amp: '&', lt: '<', gt: '>', quot: '"', apos: "'",
  nbsp: ' ', mdash: '—', ndash: '–',
  hellip: '…', lsquo: '‘', rsquo: '’',
  ldquo: '“', rdquo: '”', middot: '·',
  copy: '©', reg: '®', trade: '™',
};

function decodeEntities(value) {
  return String(value || '')
    .replace(/&#x([0-9a-fA-F]+);/g, (_, hex) => String.fromCodePoint(parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, dec) => String.fromCodePoint(parseInt(dec, 10)))
    .replace(/&([a-zA-Z]+);/g, (m, name) => NAMED_ENTITIES[name] !== undefined ? NAMED_ENTITIES[name] : m);
}

function newestSlide() {
  if (!fs.existsSync(SLIDES_DIR)) return null;
  const slides = fs.readdirSync(SLIDES_DIR)
    .map((name) => {
      const match = name.match(/^day_slide_(\d{4})_(\d{2})_(\d{2})\.html$/);
      if (!match) return null;
      return {
        name,
        date: `${match[1]}-${match[2]}-${match[3]}`,
        filePath: path.join(SLIDES_DIR, name),
      };
    })
    .filter(Boolean)
    .sort((a, b) => b.date.localeCompare(a.date));

  return slides[0] || null;
}

function extractTitle(html, date) {
  const titleMatch = html.match(/<title>([\s\S]*?)<\/title>/i);
  const raw = titleMatch ? titleMatch[1].trim() : `AI Daily Briefing ${date}`;
  return decodeEntities(raw)
    .replace(/\s*\|\s*\d{4}-\d{2}-\d{2}\s*·\s*AI Daily Briefing\s*$/i, '')
    .replace(/\s*[-|]\s*AI Daily Briefing\s*$/i, '')
    .replace(/\s*\|\s*Day Slide\s*\d{4}-\d{2}-\d{2}\s*$/i, '')
    .replace(/\s*\|\s*\d{4}-\d{2}-\d{2}\s*$/i, '')
    .trim() || `AI Daily Briefing ${date}`;
}

function extractHeroTwist(html, fallbackTitle) {
  const h1Match = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
  if (!h1Match) return fallbackTitle;
  const heading = h1Match[1].replace(/<span\b[^>]*class=["'][^"']*hero-subtitle[^"']*["'][^>]*>[\s\S]*?<\/span>/gi, '');
  const text = decodeEntities(heading.replace(/<br\s*\/?>/gi, ' ').replace(/<[^>]+>/g, ''))
    .replace(/\s*(?:\|\s*)?\d{4}-\d{2}-\d{2}\s*$/, '')
    .replace(/\s+/g, ' ')
    .trim();
  return text || fallbackTitle;
}

function extractHeroWhy(html, title) {
  const metaMatch = html.match(/<meta\s+name=["']description["']\s+content=["']([^"']+)["']/i);
  if (metaMatch) return decodeEntities(metaMatch[1]).replace(/\s+/g, ' ').trim();
  return extractSummary(html, title);
}

function extractSummary(html, title) {
  const classMatch = html.match(/<p[^>]*class=["'][^"']*(?:hero-sub|hero-kicker|sec-lede)[^"']*["'][^>]*>([\s\S]*?)<\/p>/i);
  if (classMatch) {
    return decodeEntities(classMatch[1].replace(/<[^>]+>/g, ' '))
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 260);
  }

  const metaMatch = html.match(/<meta\s+name=["']description["']\s+content=["']([^"']+)["']/i);
  if (metaMatch) return decodeEntities(metaMatch[1]).trim();

  const paragraphMatch = html.match(/<p[^>]*>([\s\S]*?)<\/p>/i);
  if (paragraphMatch) {
    return decodeEntities(paragraphMatch[1].replace(/<[^>]+>/g, ' '))
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 240);
  }

  return `${title} の要点を1枚のスライドで整理しました。`;
}

function todayJstIso(now = Date.now()) {
  // Calendar date in Asia/Tokyo: shift the instant by +9h and read the UTC date.
  return new Date(now + 9 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

function heroTodayLabel(slideDate) {
  // "今日の" only when the newest slide is dated today (JST); a delayed daily
  // publication must not advertise yesterday's slide as today's.
  return slideDate === todayJstIso() ? '今日のスライドを読む' : '最新のスライドを読む';
}

// Use the actual news generation instant; a slide calendar date is not a clock.
function dailyGenerationTime(editionDate, slideDate) {
  const daily = readJson(path.join(ROOT, 'daily-news', 'data.json'), {});
  const stamp = daily && daily.generated_iso;
  const instant = typeof stamp === 'string' ? Date.parse(stamp) : NaN;
  if (daily.date === editionDate && typeof stamp === 'string' &&
      /^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(stamp) &&
      Number.isFinite(instant) &&
      new Date(instant + 9 * 3600000).toISOString().slice(0, 10) === editionDate) {
    return stamp;
  }
  // A calendar date is known; an unqualified clock is not an instant.
  return editionDate || slideDate;
}

function readJson(filePath, fallback = null) {
  if (!fs.existsSync(filePath)) return fallback;
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (err) {
    throw new Error(`Invalid JSON in ${path.relative(ROOT, filePath)}: ${err.message}`);
  }
}

// Explicit editorial copy is reusable by report and homepage regeneration.
// Unknown URLs remain untouched; this is not an automatic translation service.
function normalizedArticleUrl(value) {
  if (typeof value !== 'string') return null;
  value = value.trim();
  if (!value || /[\x00-\x20\x7f\\]/.test(value)) return null;
  const parts = /^(https?):\/\/([^/?#]+)([^?#]*)(?:\?([^#]*))?(?:#(.*))?$/i.exec(value);
  if (!parts || parts[2].includes('@')) return null;
  try { new URL(value); } catch (_) { return null; } // Validate hostname/port only.
  // Keep explicit ports and dot segments distinct, as Python urlsplit does.
  return parts[1].toLowerCase() + '://' + parts[2].toLowerCase() + parts[3].replace(/\/$/, '') +
    (parts[4] ? '?' + parts[4] : '') + (parts[5] ? '#' + parts[5] : '');
}
let reviewedSummaries;
function loadReviewedSummaries() {
  if (reviewedSummaries) return reviewedSummaries;
  const file = path.join(ROOT, 'config', 'reviewed_news_summaries.json');
  if (!fs.existsSync(file)) return (reviewedSummaries = new Map());
  const fail = message => { throw new Error('reviewed summaries: ' + message); };
  let registry;
  try { registry = JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch (_) { fail('invalid JSON registry'); }
  if (!registry || registry.version !== 1 || !registry.articles || Array.isArray(registry.articles) || typeof registry.articles !== 'object') fail('unsupported registry schema');
  const records = new Map();
  const validDate = value => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
  for (const [key, copy] of Object.entries(registry.articles)) {
    const url = normalizedArticleUrl(key);
    if (!url || records.has(url)) fail('unsafe or duplicate source URL');
    if (!copy || !['title', 'tldr', 'summary', 'impact', 'source_url', 'source_date', 'reviewed_at', 'review_method', 'publisher']
      .every(field => typeof copy[field] === 'string' && copy[field].trim())) fail('nonempty copy and source metadata required');
    if (normalizedArticleUrl(copy.source_url) !== url) fail('source URL must match its registry key');
    if (!validDate(copy.source_date) || !validDate(copy.reviewed_at) || copy.reviewed_at < copy.source_date) fail('valid source/review dates required');
    records.set(url, copy);
  }
  return (reviewedSummaries = records);
}
function reviewedSummary(item) {
  const registry = loadReviewedSummaries();
  if (!item || item.claim_evidence != null) return item;
  const copy = registry.get(normalizedArticleUrl(item.url || (item.source && item.source.url)));
  if (!copy) return item;
  return { ...item, title: copy.title, tldr: copy.tldr, summary: copy.summary, impact: copy.impact,
    reviewed_summary: { source_url: copy.source_url, source_date: copy.source_date,
      reviewed_at: copy.reviewed_at, review_method: copy.review_method } };
}

function escapeHtml(value) {
  return String(value == null ? '' : value).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[c]));
}

function clamp(n, lo, hi) {
  return Math.max(lo, Math.min(hi, n));
}

function dateLabel(date) {
  // Use UTC noon for the calendar date so weekday is stable on UTC CI runners.
  // (JST midnight is still the previous UTC day, so getDay() on a UTC host was off-by-one.)
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date || '');
  if (!m) return `${date} · -`;
  const d = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]), 12, 0, 0));
  const dow = WEEKDAY_JP[d.getUTCDay()] || '-';
  return `${date} · ${dow}`;
}

function jstTimeFromIso(iso) {
  if (typeof iso === 'string' && /(?:Z|[+-]\d{2}:\d{2})$/.test(iso)) {
    const instant = Date.parse(iso);
    if (!Number.isFinite(instant)) return '';
    return new Date(instant + 9 * 3600000).toISOString().slice(0, 16).replace('T', ' ') + ' JST';
  }
  const m = /^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})/.exec(iso || '');
  if (!m) return '';
  return `${m[1]} ${m[2]}:${m[3]} JST`;
}

function statCount(n) {
  if (!Number.isFinite(n)) return '0+';
  if (n >= 1000) {
    const v = n / 1000;
    return `${v >= 10 ? Math.floor(v) : v.toFixed(1).replace(/\.0$/, '')}k+`;
  }
  return `${n}+`;
}

function sourceFromItem(item) {
  if (item && item.source) return item.source;
  if (item && Array.isArray(item.sources) && item.sources[0]) return item.sources[0];
  return {};
}

function sourceName(item) {
  const src = sourceFromItem(item);
  return src.name || 'AI Intelligence Hub';
}

function sourceUrl(item, fallback = '#') {
  const src = sourceFromItem(item);
  return src.url || fallback;
}

function scoreOf(item) {
  return clamp(Number(item && item.stars) || 0, 0, 5);
}

function collectRankingItems(data, slideUrl) {
  const pool = [];
  const sections = data && data.sections ? data.sections : {};
  for (const [category, items] of Object.entries(sections)) {
    if (!Array.isArray(items)) continue;
    for (const item of items) {
      if (!item || !item.title) continue;
      pool.push({
        title: item.title,
        category: item.category || category,
        stars: item.stars || 0,
        source: sourceName(item),
        url: sourceUrl(item),
      });
    }
  }

  return pool
    .sort((a, b) => scoreOf(b) - scoreOf(a))
    .slice(0, 3);
}

function rankingCardHtml(item, index) {
  const href = escapeHtml(item.url || '#');
  const rel = href.startsWith('http') ? ' target="_blank" rel="noopener noreferrer"' : '';
  const category = escapeHtml(item.category || 'NEWS');
  const title = escapeHtml(item.title || 'ニュース一覧を開く');
  const source = escapeHtml(item.source || 'AI Intelligence Hub');
  return [
    `          <a class="ranking-card" href="${href}"${rel} aria-label="${title}">`,

    '            <div class="rc-body">',
    `              <span class="rc-tag">${category}</span>`,
    `              <h3 class="rc-title">${title}</h3>`,
    `              <span class="rc-source">${source}</span>`,
    '            </div>',
    '          </a>',
  ].join('\n');
}

function collectCategoryItems(data, excludeUrls) {
  const sections = data && data.sections ? data.sections : {};
  const preferred = ['tech', 'research', 'tools', 'business', 'company', 'sns', 'posts'];
  const keys = preferred.concat(Object.keys(sections).filter((k) => !preferred.includes(k)));
  const blocked = new Set((excludeUrls || []).filter(Boolean));
  const seen = new Set();
  const items = [];
  for (const key of keys) {
    if (seen.has(key)) continue;
    seen.add(key);
    const list = sections[key];
    if (!Array.isArray(list) || !list.length) continue;
    const item = list.find((x) => x && x.title && !blocked.has(sourceUrl(x)));
    if (!item) continue;
    items.push({
      label: CATEGORY_LABELS[key] || key.toUpperCase(),
      title: item.title,
      source: sourceName(item),
      url: sourceUrl(item),
    });
    if (items.length >= 4) break;
  }
  return items;
}

function categoryCardHtml(item) {
  const href = escapeHtml(item.url || '#');
  const rel = href.startsWith('http') ? ' target="_blank" rel="noopener noreferrer"' : '';
  return [
    `          <a class="cat-card" href="${href}"${rel}>`,
    `            <div class="cat-label">${escapeHtml(item.label)}</div>`,
    `            <div class="cat-title">${escapeHtml(item.title)}</div>`,
    `            <div class="cat-source"><span>${escapeHtml(item.source)}</span><span class="arr">→</span></div>`,
    '          </a>',
  ].join('\n');
}

function replaceFirst(html, pattern, replacement, label) {
  if (!pattern.test(html)) {
    throw new Error(`Failed to update ${label} in index.html`);
  }
  return html.replace(pattern, replacement);
}

function replaceHrefById(html, id, href, label, required = true) {
  const idPattern = id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const openingTag = new RegExp(`<a\\b(?=[^>]*\\bid=["']${idPattern}["'])[^>]*>`, 'i');
  const match = html.match(openingTag);
  if (!match) {
    if (required) throw new Error(`Failed to update ${label} in index.html`);
    return html;
  }
  const hrefPattern = /\bhref=(['"])[^'"]*\1/i;
  if (!hrefPattern.test(match[0])) {
    if (required) throw new Error(`Missing href for ${label} in index.html`);
    return html;
  }
  const updated = match[0].replace(hrefPattern, `href="${escapeHtml(href)}"`);
  return html.replace(match[0], updated);
}

function replaceElementText(html, id, text, label, required = false) {
  const idPattern = id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const elementPattern = new RegExp(
    `(<([a-z][a-z0-9]*)\\b[^>]*\\bid=["']${idPattern}["'][^>]*>)[\\s\\S]*?(</\\2>)`,
    'i'
  );
  if (!elementPattern.test(html)) {
    if (required) throw new Error(`Failed to update ${label} in index.html`);
    return html;
  }
  return html.replace(elementPattern, (_, opening, _tag, closing) => (
    `${opening}${escapeHtml(text)}${closing}`
  ));
}

function replaceAnchorLabel(html, id, label) {
  const anchorPattern = new RegExp(
    `(<a\\b(?=[^>]*\\bid=["']${id}["'])[^>]*>)([\\s\\S]*?)(</a>)`, 'i'
  );
  return html.replace(anchorPattern, (_, opening, body, closing) => {
    const markers = (body.match(/<!--[\s\S]*?-->/g) || []).join('');
    return `${opening}${markers}${escapeHtml(label)}${closing}`;
  });
}

function replaceWeekGridWithEmptyState(html) {
  const marker = /(<!-- fallback:this-week -->)[\s\S]*?(<!-- fallback:end -->)/i;
  if (!marker.test(html)) return html;
  return html.replace(
    marker,
    '$1<div id="weekGrid" class="week-grid"><div class="week-card is-empty">' +
      '<span class="week-day">公開スライドなし</span>' +
      '<div class="week-title">公開スライドはまだありません</div>' +
      '<span class="week-go">スライド一覧で確認</span></div></div>$2'
  );
}

function preserveHomepageWithoutSlides() {
  if (!fs.existsSync(INDEX_HTML)) return;
  let html = fs.readFileSync(INDEX_HTML, 'utf8');
  const listUrl = 'presentations/day_slides_index.html';
  html = replaceHrefById(html, 'latestSlideHeroBtn', listUrl, 'header slide index', false);
  html = replaceHrefById(html, 'heroSlideBtn', listUrl, 'slide index CTA', false);
  html = replaceHrefById(html, 'todaySlideCard', listUrl, 'legacy slide card', false);
  html = replaceHrefById(html, 'sitrepLink', listUrl, 'sitrep slide index', false);
  html = replaceHrefById(html, 'heroTodayBtn', listUrl, 'hero today CTA', false);
  html = html.replace(
    /(\bhref=["'])presentations\/day_slides\/day_slide_\d{4}_\d{2}_\d{2}\.html(["'])/gi,
    `$1${listUrl}$2`
  );
  if (!html.includes('data-slides-unavailable="true"')) {
    html = html.replace('<html ', '<html data-slides-unavailable="true" ');
  }
  html = replaceAnchorLabel(html, 'latestSlideHeroBtn', 'スライド一覧');
  html = replaceAnchorLabel(html, 'heroSlideBtn', 'スライド一覧');
  html = replaceElementText(html, 'heroTodayLabel', '今日のスライドはありません', 'hero today label', false);
  html = replaceWeekGridWithEmptyState(html);
  html = replaceElementText(html, 'heroDate', '公開スライドなし');
  html = replaceElementText(html, 'todaySlideDate', '公開スライドなし');
  html = replaceElementText(html, 'heroTwist', '公開スライドはまだありません');
  html = replaceElementText(
    html,
    'heroWhy',
    '日次スライドが公開されると、ここに見出しと要点を表示します。'
  );
  fs.writeFileSync(INDEX_HTML, html, 'utf8');
  console.warn('[build-homepage-latest] no slide fallback written to index.html');
}

function replaceGrid(html, id, replacement) {
  const start = html.indexOf(`<div id="${id}"`);
  if (start === -1) throw new Error(`Missing #${id} in index.html`);
  const lineStart = html.lastIndexOf('\n', start) + 1;
  const endMarker = '\n      </div>\n    </section>';
  const end = html.indexOf(endMarker, start);
  if (end === -1) throw new Error(`Could not find closing section after #${id}`);
  return html.slice(0, lineStart) + replacement + html.slice(end);
}

function weekFallback(slide, metadata) {
  const anchor = Date.parse(`${slide.date}T12:00:00Z`);
  const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
  const titles = new Map((Array.isArray(metadata && metadata.issues) ? metadata.issues : [])
    .filter(issue => issue && typeof issue.title === 'string').map(issue => [issue.date, issue.title]));
  const cards = [];
  for (let offset = 0; offset < 7; offset++) {
    const day = new Date(anchor - offset * 86400000);
    const stamp = day.toISOString().slice(0, 10);
    const filename = `day_slide_${stamp.replace(/-/g, '_')}.html`;
    const file = path.join(SLIDES_DIR, filename);
    const exists = fs.existsSync(file) && fs.statSync(file).isFile();
    const title = exists ? (offset > 0 && titles.get(stamp)) || extractTitle(fs.readFileSync(file, 'utf8'), stamp) : '';
    const latest = offset === 0 && exists;
    const tag = exists ? 'a' : 'div';
    const href = exists ? ` href="presentations/day_slides/${filename}"` : '';
    const classes = 'week-card' + (latest ? ' is-today' : '') + (exists ? '' : ' is-empty');
    cards.push(`          <${tag} class="${classes}"${href}>` +
      (latest ? '<span class="today-flag">LATEST</span>' : '') +
      `<span class="week-day">${months[day.getUTCMonth()]} · ${WEEKDAY_JP[day.getUTCDay()]}曜</span>` +
      `<div class="week-date">${String(day.getUTCDate()).padStart(2, '0')}</div>` +
      `<div class="week-title">${escapeHtml(title)}</div>` +
      `<span class="week-go">${exists ? 'スライドを読む →' : '更新なし'}</span></${tag}>`);
  }
  return `\n        <div id="weekGrid" class="week-grid">\n${cards.join('\n')}\n        </div>\n        `;
}

function updateHomepage(data, slide, slideUrl) {
  if (!fs.existsSync(INDEX_HTML)) {
    console.warn(`[build-homepage-latest] index.html not found at ${INDEX_HTML}`);
    return;
  }

  const archiveEntries = readJson(ARCHIVE_INDEX_JSON, []);
  // Slide count must come from day_slides list/meta — archive_index length is news-days.
  const slideList = readJson(DAY_SLIDES_LIST_JSON, []);
  const slideMeta = readJson(DAY_SLIDES_META_JSON, {});
  const totalSlides = Array.isArray(slideList) && slideList.length
    ? slideList.length
    : (Number.isFinite(Number(slideMeta && slideMeta.generated_from))
        ? Number(slideMeta.generated_from)
        : 0);
  // archiveEntries.length is news-days (not slides); used only for item totals below.
  const totalItems = Array.isArray(archiveEntries)
    ? archiveEntries.reduce((sum, entry) => sum + (Number(entry.count) || 0), 0)
    : 0;
  const generatedAt = jstTimeFromIso(data.generated_at);
  const slideDate = slide.date;
  const fallbackDate = data.news_date || slideDate;
  const updateTime = generatedAt ? generatedAt.replace(/^\d{4}-\d{2}-\d{2}\s+/, '').replace(' JST', '') : '未記録';
  const slideHtml = fs.readFileSync(slide.filePath, 'utf8');
  const heroTitle = extractTitle(slideHtml, slideDate);
  const heroTwist = extractHeroTwist(slideHtml, heroTitle);
  const heroWhy = extractHeroWhy(slideHtml, heroTitle);
  const rankingItems = collectRankingItems(data, slideUrl);
  const categoryItems = collectCategoryItems(data, rankingItems.map((item) => item.url));
  let html = fs.readFileSync(INDEX_HTML, 'utf8');

  html = html.replace(/<meta http-equiv="Content-Security-Policy"[\s\S]*?\/>\n\s*/i, '');
  html = replaceFirst(
    html,
    /(<meta name="referrer" content="strict-origin-when-cross-origin" \/>\n)/,
    `$1  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; base-uri 'self'; object-src 'none'; img-src 'self' data: https:; font-src https://fonts.gstatic.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com; connect-src 'self' https://www.google-analytics.com https://*.google-analytics.com; form-action 'self'; upgrade-insecure-requests" />\n`,
    'CSP meta'
  );

  html = replaceHrefById(html, 'latestSlideHeroBtn', slideUrl, 'header latest slide CTA');
  html = replaceFirst(
    html,
    /<span id="heroDate"[^>]*>[\s\S]*?<\/span>/,
    `<span id="heroDate">${escapeHtml(dateLabel(slideDate))}</span>`,
    'hero date'
  );
  html = html.replace(
    /if \(el\) el\.textContent = y \+ '-' \+ m \+ '-' \+ d \+ ' .*? \+ w;/,
    "if (el && !el.textContent.trim()) el.textContent = y + '-' + m + '-' + d + ' · ' + w;"
  );
  const wasEmpty = html.includes('data-slides-unavailable="true"');
  html = html.replace(/ data-slides-unavailable="true"/g, '');
  if (wasEmpty) {
    html = replaceAnchorLabel(html, 'latestSlideHeroBtn', '最新スライド →');
    html = replaceAnchorLabel(html, 'heroSlideBtn', '最新スライドを読む →');
  }
  html = replaceFirst(html, /(<!-- fallback:this-week -->)[\s\S]*?(<!-- fallback:end -->)/i,
    (_match, start, end) => start + weekFallback(slide, slideMeta) + end, 'weekly slide fallback');
  html = replaceHrefById(html, 'heroSlideBtn', slideUrl, 'hero slide button');
  // todaySlideCard was the old wrapper ID. Keep compatibility while allowing
  // the new trends card to own the slide link directly.
  html = replaceHrefById(html, 'todaySlideCard', slideUrl, 'today slide card', false);
  html = replaceElementText(html, 'todaySlideDate', slideDate, 'today slide date', false);
  html = replaceHrefById(html, 'sitrepLink', slideUrl, 'sitrep link', false);
  html = replaceElementText(html, 'sitrepUpdate', heroTwist, 'slide topic', false);
  html = replaceElementText(html, 'sitrepDesk', heroWhy, 'slide summary', false);
  html = replaceElementText(html, 'sitrepAction', '出典と確認条件をスライドで確認。', 'slide reading guide', false);
  html = replaceHrefById(html, 'heroTodayBtn', slideUrl, 'hero today CTA', false);
  html = replaceElementText(html, 'heroTodayLabel', heroTodayLabel(slideDate), 'hero today label', false);
  html = replaceElementText(html, 'heroTwist', heroTwist, 'hero twist', false);
  html = replaceElementText(html, 'heroWhy', heroWhy, 'hero explanation', false);

  html = replaceElementText(html, 'rankingNewsDate', data.news_date || '未確認');
  const newsArchive = data.news_date && `daily-news/archive/${data.news_date}.html`;
  html = replaceHrefById(html, 'rankingNewsLink', newsArchive && fs.existsSync(path.join(ROOT, newsArchive)) ? newsArchive : 'daily-news/', 'news picks link', false);
  const rankingFallback = rankingItems.length
    ? rankingItems.map(rankingCardHtml).join('\n')
    : `          <a class="ranking-card" href="daily-news/">\n            <div class="rc-body"><h3 class="rc-title">ニュース一覧を開く</h3><span class="rc-source">AI Intelligence Hub</span></div>\n          </a>`;
  html = replaceGrid(
    html,
    'rankingGrid',
    `        <div id="rankingGrid" class="ranking-grid">\n${rankingFallback}\n        </div>`
  );

  const catFallback = categoryItems.length
    ? categoryItems.map(categoryCardHtml).join('\n')
    : `          <div class="cat-card"><div class="cat-label">ARCHIVE</div><div class="cat-title">最新スライドと過去ニュースはアーカイブから確認できます。</div><div class="cat-source"><a href="presentations/news_archive.html">アーカイブを見る →</a></div></div>`;
  html = replaceGrid(
    html,
    'catGrid',
    `        <div id="catGrid" class="cat-grid" data-news-date="${escapeHtml(data.news_date || '')}" data-excluded-news-urls="${escapeHtml(JSON.stringify([...HOMEPAGE_NEWS_EXCLUSIONS]))}">\n${catFallback}\n          <noscript>\n            <div class="cat-card"><div class="cat-label">LATEST</div><div class="cat-title">${escapeHtml(heroTitle)}</div><div class="cat-source"><a href="${slideUrl}">今日のスライドを見る →</a></div></div>\n          </noscript>\n        </div>`
  );

  html = replaceFirst(
    html,
    /<em id="statSlides">[\s\S]*?<\/em>/,
    `<em id="statSlides">${escapeHtml(statCount(totalSlides))}</em>`,
    'slide stats'
  );
  html = replaceFirst(
    html,
    /<em id="statItems">[\s\S]*?<\/em>/,
    `<em id="statItems">${escapeHtml(statCount(totalItems))}</em>`,
    'item stats'
  );
  html = replaceFirst(
    html,
    /<div class="archive-stat"><span class="archive-stat-num"><em(?: id="statUpdated")?>[\s\S]*?<\/em><\/span><span class="archive-stat-label">(?:Daily Update|Latest Update|最終更新|ニュース生成時刻) \(JST\)<\/span><\/div>/,
    `<div class="archive-stat"><span class="archive-stat-num"><em id="statUpdated">${escapeHtml(updateTime)}</em></span><span class="archive-stat-label">ニュース生成時刻 (JST)</span></div>`,
    'update time stats'
  );
  html = replaceFirst(
    html,
    /<span id="footerUpdated">[\s\S]*?<\/span>/,
    `<span id="footerUpdated">UPDATED ${escapeHtml(fallbackDate)}</span>`,
    'footer updated date'
  );

  fs.writeFileSync(INDEX_HTML, html, 'utf8');
  console.log(`Updated ${path.relative(ROOT, INDEX_HTML)} static fallbacks for ${slide.name}`);
}

// Map auto_daily_report categories (and synthetic ones for funding/github/models)
// to the 7 buckets the homepage HTML knows how to render.
const CATEGORY_MAP = {
  'AI Technology': 'tech',
  'AI Model':      'tech',
  'Research':      'research',
  'Product':       'tools',
  'Hardware':      'tech',
};

const SOURCE_NAME_MAP = {
  hn: 'Hacker News',
  arxiv: 'arXiv',
  github: 'GitHub',
  rss: 'RSS',
  jp: '国内ニュース',
};

function prettySource(raw) {
  if (!raw) return 'source';
  const key = String(raw).toLowerCase();
  return SOURCE_NAME_MAP[key] || raw;
}

function inferSourceFromUrl(url) {
  if (!url) return null;
  if (url.includes('huggingface.co')) return 'Hugging Face';
  if (url.includes('github.com')) return 'GitHub';
  if (url.includes('arxiv.org')) return 'arXiv';
  if (url.includes('news.ycombinator.com')) return 'Hacker News';
  return null;
}

function normalizeSource(item, fallbackName) {
  const url = item.url || '';
  const inferred = inferSourceFromUrl(url);
  const name = item.source || inferred || fallbackName;
  return {
    name: prettySource(name),
    url: url || '#',
  };
}

function starsForScore(score, importance) {
  // Numeric score from auto_daily_report (0-100). Falls back to importance string.
  if (typeof score === 'number' && Number.isFinite(score)) {
    if (score >= 80) return 5;
    if (score >= 65) return 4;
    if (score >= 45) return 3;
    return 2;
  }
  if (importance === 'high') return 4;
  if (importance === 'medium') return 3;
  return 2;
}

function blurbFor(item) {
  const raw = item.tldr || item.summary || '';
  return String(raw).replace(/\s+/g, ' ').trim().slice(0, 200);
}

// Preserve optional, reviewed records from the existing report. This consumer
// neither assigns a verification state nor updates its dates or fingerprints.
function claimEvidenceFor(item, reportDate) {
  const bundle = item.claim_evidence;
  if (!bundle || !Array.isArray(bundle.claims) || !bundle.claims.length) return {};
  const firstId = bundle.claims[0].id;
  const evidenceUrl = /^\d{4}-\d{2}-\d{2}$/.test(reportDate || '') && /^[A-Za-z][A-Za-z0-9_-]{0,99}$/.test(firstId || '')
    ? `presentations/daily_reports/auto_daily_report_${reportDate.replace(/-/g, '_')}.html#evidence-${firstId}`
    : null;
  return { claim_evidence: bundle, ...(evidenceUrl ? { evidence_url: evidenceUrl } : {}) };
}

function pushItem(sections, bucket, record, perBucketLimit = 6) {
  if (!sections[bucket]) sections[bucket] = [];
  if (sections[bucket].length >= perBucketLimit) return;
  sections[bucket].push(record);
}

// data.date is "today's report date" — far more reliable than per-article timestamps.
// soft warn at 3 days, fail-close at 14 days to avoid showing visibly stale homepage.
const MAX_DATA_AGE_DAYS_SOFT = 3;
const MAX_DATA_AGE_DAYS_HARD = 14;

function dataAgeDays(dateStr) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateStr || '')) return Infinity;
  const t = Date.parse(`${dateStr}T00:00:00Z`);
  if (!Number.isFinite(t)) return Infinity;
  return Math.floor((Date.now() - t) / 86400000);
}

function buildSectionsFromAutoDaily() {
  if (!fs.existsSync(AUTO_DAILY_JSON)) {
    console.warn(`[build-homepage-latest] auto_daily_report/latest.json not found at ${AUTO_DAILY_JSON}`);
    return { sections: {}, dailyDate: null };
  }

  let data;
  try {
    data = JSON.parse(fs.readFileSync(AUTO_DAILY_JSON, 'utf8'));
  } catch (err) {
    console.error(`[build-homepage-latest] failed to parse auto_daily_report/latest.json: ${err.message}`);
    return { sections: {}, dailyDate: null };
  }

  const reportDate = typeof data.date === 'string' ? data.date.slice(0, 10) : null;
  const ageDays = dataAgeDays(reportDate);
  if (ageDays > MAX_DATA_AGE_DAYS_HARD) {
    console.error(`[build-homepage-latest] auto_daily_report is ${ageDays} days old (>${MAX_DATA_AGE_DAYS_HARD}). Failing closed with empty sections.`);
    return { sections: {}, dailyDate: reportDate };
  }
  if (ageDays > MAX_DATA_AGE_DAYS_SOFT) {
    console.warn(`[build-homepage-latest] auto_daily_report is ${ageDays} days old (>${MAX_DATA_AGE_DAYS_SOFT}). Using anyway, but upstream pipeline may be stalled.`);
  }

  const sections = {};

  const headlines = Array.isArray(data.headlines) ? data.headlines.map(reviewedSummary) : [];
  headlines.sort((a, b) => (Number(b.score) || 0) - (Number(a.score) || 0));
  for (const h of headlines) {
    const bucket = CATEGORY_MAP[h.category] || 'tech';
    pushItem(sections, bucket, {
      title: h.title || 'Untitled',
      blurb: blurbFor(h),
      category: bucket,
      date: reportDate || '',
      stars: h.score_status === 'unscored' ? null : starsForScore(h.score, h.importance),
      ...(h.published_at ? { published_at: h.published_at } : {}),
      ...(h.score_status ? { score_status: h.score_status } : {}),
      source: normalizeSource(h, h.source),
      ...claimEvidenceFor(h, reportDate),
    });
  }

  const funding = Array.isArray(data.funding) ? data.funding : [];
  for (const f of funding) {
    pushItem(sections, 'business', {
      title: f.title || 'Untitled',
      blurb: blurbFor(f),
      category: 'business',
      date: reportDate || '',
      stars: starsForScore(f.score, f.importance),
      source: normalizeSource(f, 'funding'),
      ...claimEvidenceFor(f, reportDate),
    });
  }

  const github = Array.isArray(data.github) ? data.github : [];
  for (const g of github) {
    pushItem(sections, 'tools', {
      title: g.title || 'Untitled',
      blurb: blurbFor(g) || (g.metrics && g.metrics[0]) || '',
      category: 'tools',
      date: reportDate || '',
      stars: starsForScore(g.score, g.importance),
      source: normalizeSource(g, 'GitHub'),
    });
  }

  const models = Array.isArray(data.models) ? data.models : [];
  for (const m of models) {
    pushItem(sections, 'research', {
      title: m.title || 'Untitled',
      blurb: blurbFor(m) || (m.metrics && m.metrics[0]) || '',
      category: 'research',
      date: reportDate || '',
      stars: starsForScore(m.score, m.importance),
      source: normalizeSource(m, 'models'),
    });
  }

  // Drop empty buckets to keep the JSON tidy and avoid confusing the renderer.
  for (const k of Object.keys(sections)) {
    if (!sections[k] || sections[k].length === 0) delete sections[k];
  }

  return { sections, dailyDate: reportDate };
}

function buildSections() {
  return buildSectionsFromAutoDaily();
}

// Show what date search actually covers; do not imply the index is current.
function updateSearchCoverage() {
  const records = readJson(path.join(ROOT, 'public-pages', 'news', 'search_index.json'));
  function range(slides) {
    if (!Array.isArray(records)) return '未確認';
    const dates = records.filter(x => x && (x.type === 'slide') === slides).map(x => x.date)
      .filter(d => /^\d{4}-\d{2}-\d{2}$/.test(d || '') && Number.isFinite(Date.parse(d + 'T00:00:00Z')) &&
        new Date(d + 'T00:00:00Z').toISOString().slice(0, 10) === d).sort();
    return dates.length ? dates[0] + '〜' + dates[dates.length - 1] : '未収録';
  }
  const label = 'ニュース収録: ' + range(false) + ' / スライド収録: ' + range(true);
  for (const [relative, id] of [['index.html', 'searchArchiveRange'], ['presentations/news_archive.html', 'archiveCoverage']]) {
    const file = path.join(ROOT, relative);
    if (!fs.existsSync(file)) continue;
    const html = fs.readFileSync(file, 'utf8');
    const updated = replaceElementText(html, id, label);
    if (updated !== html) fs.writeFileSync(file, updated, 'utf8');
  }
}

// Independent dates: report content must not inherit the slide's calendar date.
function updateDailyBriefing() {
  if (!fs.existsSync(INDEX_HTML)) return;
  let html = fs.readFileSync(INDEX_HTML, 'utf8');
  const report = readJson(AUTO_DAILY_JSON, {});
  const date = /^\d{4}-\d{2}-\d{2}$/.test(report.date || '') ? report.date : null;
  const short = (value) => String(value || '').replace(/\s+/g, ' ').trim().slice(0, 180);
  const japanese = (value) => /[ぁ-んァ-ヶ一-龯]/.test(value || '');
  const seen = new Set();
  const items = (Array.isArray(report.headlines) ? report.headlines : []).map(reviewedSummary)
    .filter(item => item && item.title && isHomepageNews(item) && !seen.has(item.title) && seen.add(item.title))
    .sort((a, b) => (Number(b.score) || 0) - (Number(a.score) || 0)).slice(0, 3);
  const reportUrl = date && fs.existsSync(path.join(ROOT, 'presentations', 'daily_reports', `auto_daily_report_${date.replace(/-/g, '_')}.html`))
    ? `presentations/daily_reports/auto_daily_report_${date.replace(/-/g, '_')}.html` : 'presentations/auto_daily_report.html';
  const content = date && items.length ? items.map(item => {
    const change = [item.tldr, item.summary].find(japanese) || '日本語要約は未作成です。原文の出典をご確認ください。';
    const impact = japanese(item.impact) ? item.impact : '影響対象は未確認です。';
    const sourceLink = /^https?:\/\//i.test(item.url || '') ? ` <a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">出典を読む →</a>` : '';
    return `<li><h3>${escapeHtml(item.title)}</h3><p><strong>何が変わったか:</strong> ${escapeHtml(short(change))}</p><p><strong>誰に関係するか:</strong> ${escapeHtml(short(impact))}</p>${sourceLink}</li>`;
  }).join('\n') : '<li>主要ニュースは更新待ちです。日次レポートをご確認ください。</li>';
  html = html.replace(/<!-- homepage:headlines -->[\s\S]*?<!-- homepage:headlines:end -->/, `<!-- homepage:headlines --><ol id="dailyHeadlines">${content}</ol><!-- homepage:headlines:end -->`);
  html = replaceElementText(html, 'dailyReportDate', date || '未確認');
  html = replaceElementText(html, 'dailyReportStatus', date && date !== new Date(Date.now() + 9 * 3600000).toISOString().slice(0, 10) ? '（最新掲載分・本日分ではありません）' : '');
  html = replaceHrefById(html, 'dailyReportLink', reportUrl, 'daily report', false);
  const archive = readJson(ARCHIVE_INDEX_JSON, []);
  const legacyDate = Array.isArray(archive) ? archive.map(x => x.date).filter(x => /^\d{4}-\d{2}-\d{2}$/.test(x || '')).sort().pop() : null;
  const dailyPath = path.join(ROOT, 'daily-news', 'data.json');
  const daily = readJson(dailyPath, {});
  const dailyStamp = Date.parse((daily.date || '') + 'T00:00:00Z');
  const validDaily = /^\d{4}-\d{2}-\d{2}$/.test(daily.date || '') && Number.isFinite(dailyStamp) &&
    new Date(dailyStamp).toISOString().slice(0, 10) === daily.date &&
    Array.isArray(daily.items) && daily.items.length > 0 && daily.total === daily.items.length;
  // The per-day legacy aggregate index is no longer the daily timeline clock.
  // If a current payload exists but is invalid, show unknown rather than lie.
  const newsDate = fs.existsSync(dailyPath) ? (validDaily ? daily.date : null) : legacyDate;
  html = replaceElementText(html, 'dailyNewsDate', newsDate || '未確認');
  // The edition owns this notice. Remove it as soon as automatic news returns.
  html = html.replace(/<aside\b[^>]*\bid=["']editorial-publication-notice["'][^>]*>[\s\S]*?<\/aside>/g, '');
  if (report.quality && report.quality.mode === 'editorial_review') {
    const sourceDates = (report.headlines || []).map(item =>
      `<li><a href="${escapeHtml(item.url || '')}" target="_blank" rel="noopener">${escapeHtml(item.title || '')}</a> — 原文掲載日: ${escapeHtml(item.published_at || '未確認')}</li>`).join('');
    const notice = `<aside id="editorial-publication-notice" style="margin:1rem auto;padding:1rem;max-width:1200px;border:1px solid #e5ad54;background:#18212e;color:#f4e5c6;line-height:1.8"><strong>編集確認済み・3件の暫定版</strong><br>アシスタントが原文を読み、出典と掲載日を確認した暫定版です。発表元の主張を独立検証したものではありません。自動収集は未復旧です。重要度スコアは未評価です。<br>版の日付: ${escapeHtml(date || '')}<ul>${sourceDates}</ul></aside>`;
    html = html.replace(/(<body\b[^>]*>)/i, '$1' + notice);
  }
  fs.writeFileSync(INDEX_HTML, html, 'utf8');
}

function main() {
  if (process.argv.includes('--strict')) {
    const validDate = date => typeof date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(date) &&
      Number.isFinite(Date.parse(date)) && new Date(date).toISOString().slice(0, 10) === date;
    const report = readJson(AUTO_DAILY_JSON, null);
    const daily = readJson(path.join(ROOT, 'daily-news/data.json'), null);
    if (!report || !validDate(report.date) || !Array.isArray(report.headlines)) throw new Error('Published report metadata is missing or invalid');
    if (dataAgeDays(report.date) > MAX_DATA_AGE_DAYS_HARD) throw new Error('Published report metadata is too old; previous TOP is preserved');
    if (!daily || !validDate(daily.date) || !Array.isArray(daily.items) || !daily.items.length || daily.total !== daily.items.length) throw new Error('Published daily news metadata is missing or invalid');
    const slide = newestSlide();
    if (!slide || !validDate(slide.date)) throw new Error('Published slide metadata is missing or invalid');
  }
  updateSearchCoverage();
  updateDailyBriefing();
  const slide = newestSlide();
  if (!slide) {
    console.warn(`[build-homepage-latest] no day slides found in ${SLIDES_DIR}; preserving news JSON and writing honest homepage empty state`);
    preserveHomepageWithoutSlides();
    return;
  }

  const html = fs.readFileSync(slide.filePath, 'utf8');
  const title = extractTitle(html, slide.date);
  const summary = extractSummary(html, title);
  const slideUrl = `presentations/day_slides/${slide.name}`;
  const latestNews = buildSections();
  // A slide refresh must not replace a complete same-day news publication with
  // the smaller report preview. The news pipeline owns these sections.
  const publishedNews = readJson(LATEST_JSON);
  // build_news.py emits generated_at without news_date. Keep its calendar date
  // in the producer's timezone; an explicit news_date always takes precedence.
  const generatedAt = publishedNews && publishedNews.generated_at;
  const publishedDate = publishedNews && (publishedNews.news_date ??
    (typeof generatedAt === 'string' && Number.isFinite(Date.parse(generatedAt))
      ? generatedAt.slice(0, 10) : null));
  const daily = readJson(path.join(ROOT, 'daily-news/data.json'), {});
  if (daily.date && (!latestNews.dailyDate || daily.date > latestNews.dailyDate) &&
      Array.isArray(daily.items) && daily.items.length && daily.total === daily.items.length &&
      publishedDate === daily.date) latestNews.dailyDate = daily.date;
  if (publishedNews && latestNews.dailyDate &&
      publishedDate === latestNews.dailyDate &&
      dataAgeDays(latestNews.dailyDate) <= MAX_DATA_AGE_DAYS_HARD &&
      publishedNews.sections && !Array.isArray(publishedNews.sections) &&
      Object.values(publishedNews.sections).every(Array.isArray) &&
      Object.values(publishedNews.sections).some((items) => items.length > 0)) {
    latestNews.sections = Object.fromEntries(Object.entries(publishedNews.sections).map(([key, items]) => [key,
      items.map(item => {
        const reviewed = reviewedSummary(item);
        return reviewed === item ? item : { ...reviewed, blurb: reviewed.tldr };
      })]));
  }

  const data = {
    generated_at: dailyGenerationTime(latestNews.dailyDate, slide.date),
    news_date: latestNews.dailyDate,
    slide_date: slide.date,
    highlight: {
      category: '最新のスライド',
      title,
      summary,
      sources: [
        {
          name: 'AI Intelligence Hub',
          url: slideUrl,
        },
      ],
    },
    sections: Object.fromEntries(Object.entries(latestNews.sections).map(([key, items]) =>
      [key, items.filter(isHomepageNews)])),
  };

  fs.mkdirSync(NEWS_DIR, { recursive: true });
  fs.writeFileSync(LATEST_JSON, JSON.stringify(data, null, 2), 'utf8');
  console.log(`Updated ${path.relative(ROOT, LATEST_JSON)} from ${slide.name}`);
  updateHomepage(data, slide, slideUrl);
}

function syncResourcesAndClock() {
  let html = fs.readFileSync(INDEX_HTML, 'utf8');
  function resource(relative, description, alt) {
    const pattern = new RegExp('(<a\\b(?=[^>]*\\bres-card\\b)[^>]*href=["\\\']/?' + relative.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '["\\\'][^>]*>[\\s\\S]*?</a>)');
    html = html.replace(pattern, block => {
      block = block.replace(/(<div class="res-desc">)[\s\S]*?(<\/div>)/, '$1' + escapeHtml(description) + '$2');
      return alt ? block.replace(/(<img\b[^>]*\balt=)["'][^"']*["']/, '$1"' + escapeHtml(alt) + '"') : block;
    });
  }
  const toolsPath = path.join(ROOT, 'presentations/recommended_tools/index.html');
  if (fs.existsSync(toolsPath)) {
    const tools = fs.readFileSync(toolsPath, 'utf8');
    const candidates = (tools.match(/data-evidence="official-info"/g) || []).length;
    const recorded = (tools.match(/data-evidence="(?:usage-log|notes)"/g) || []).length;
    resource('presentations/recommended_tools/', `公式情報からの注目候補${candidates}件と利用記録${recorded}件を上部に紹介。以前の掲載分も一覧・検索で探せます。掲載時点と最新情報の確認状況を表示。`);
  }
  const guidePath = path.join(ROOT, 'presentations/ai_tool_optimization_2026_04.html');
  if (fs.existsSync(guidePath)) {
    const edition = /<title>[^<]*?(20\d{2}年\d{1,2}月版)/.exec(fs.readFileSync(guidePath, 'utf8'));
    if (!edition) throw new Error('Optimization guide edition is missing');
    resource('presentations/ai_tool_optimization_2026_04.html', `AIツールの役割分担とコスト構成を整理した${edition[1]}の保存ガイド。現在の料金・条件は公式情報を確認。`, `AIツール選択最適化ガイド${edition[1]}のカバー画像`);
  }
  html = html.replace(/var foot = document\.getElementById\('footerUpdated'\);\s*if \(foot && entries\[0\]\) foot\.textContent = 'UPDATED ' \+ entries\[0\]\.date;/,
    '// The archive edition is not the homepage update date.');
  html = html.replace(/<span class="archive-stat-label">最終更新 \(JST\)<\/span>/, '<span class="archive-stat-label">ニュース生成時刻 (JST)</span>');
  html = html.replace(/(<span class="sitrep-key">)更新は(<\/span>)/, '$1テーマ$2')
    .replace(/(<span class="sitrep-key">)判断は(<\/span>)/, '$1概要$2')
    .replace(/(<span class="sitrep-key">)動きは(<\/span>)/, '$1読むときは$2');
  html = html.replace(/(<aside\b[^>]*class="sitrep"[^>]*aria-label=)["'][^"']*["']/, '$1"最新スライドの要点"');
  fs.writeFileSync(INDEX_HTML, html, 'utf8');
  const data = readJson(LATEST_JSON, {});
  const date = [data.slide_date, data.news_date].filter(v => /^\d{4}-\d{2}-\d{2}$/.test(v || '')).sort().pop();
  if (date) {
    html = replaceElementText(html, 'footerUpdated', 'UPDATED ' + date);
    const knownClock = /(?:Z|[+-]\d{2}:\d{2})$/.test(data.generated_at || '');
    html = replaceElementText(html, 'heroUpdatedAt', knownClock ? jstTimeFromIso(data.generated_at) : `${data.news_date || date}（生成時刻未記録）`);
    fs.writeFileSync(INDEX_HTML, html, 'utf8');
  }
}

// Roll back all generated outputs if any input or required template fails.
// A failed build must not commit/publish a partly updated homepage.
const outputPaths = [INDEX_HTML, LATEST_JSON, path.join(ROOT, 'presentations/news_archive.html')];
const saved = new Map(outputPaths.map(file => [file, fs.existsSync(file) ? fs.readFileSync(file) : null]));
try {
  main();
  syncResourcesAndClock();
  if (process.argv.includes('--check')) {
    const changed = outputPaths.filter(file => {
      const before = saved.get(file);
      return before ? !before.equals(fs.readFileSync(file)) : fs.existsSync(file);
    });
    if (changed.length) throw new Error('Homepage is out of sync: ' + changed.map(file => path.relative(ROOT, file)).join(', '));
  }
} catch (error) {
  for (const [file, content] of saved) {
    if (content === null) { if (fs.existsSync(file)) fs.unlinkSync(file); }
    else if (!fs.existsSync(file) || !content.equals(fs.readFileSync(file))) fs.writeFileSync(file, content);
  }
  console.error('[build-homepage-latest] failed; previous generated data preserved: ' + error.message);
  process.exitCode = 1;
}

