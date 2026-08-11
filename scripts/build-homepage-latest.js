#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const SLIDES_DIR = path.join(ROOT, 'presentations', 'day_slides');
const NEWS_DIR = path.join(ROOT, 'news');
const LATEST_JSON = path.join(NEWS_DIR, 'latest.json');
const INDEX_HTML = path.join(ROOT, 'index.html');
const ARCHIVE_INDEX_JSON = path.join(ROOT, 'public-pages', 'news', 'archive_index.json');
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

function toJstIso(date) {
  return `${date}T09:00:00.000000+09:00`;
}

function readJson(filePath, fallback = null) {
  if (!fs.existsSync(filePath)) return fallback;
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (err) {
    console.warn(`[build-homepage-latest] failed to parse ${path.relative(ROOT, filePath)}: ${err.message}`);
    return fallback;
  }
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
  if (data && data.highlight && data.highlight.title) {
    pool.push({
      title: data.highlight.title,
      category: data.highlight.category || '本日のスライド',
      stars: data.highlight.stars || 5,
      source: sourceName(data.highlight),
      url: sourceUrl(data.highlight, slideUrl),
    });
  }

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
  const score = scoreOf(item);
  const pct = Math.round((score / 5) * 100);
  const href = escapeHtml(item.url || '#');
  const rel = href.startsWith('http') ? ' target="_blank" rel="noopener noreferrer"' : '';
  const category = escapeHtml(item.category || 'NEWS');
  const title = escapeHtml(item.title || '最新ランキングを開く');
  const source = escapeHtml(item.source || 'AI Intelligence Hub');
  return [
    `          <a class="ranking-card" href="${href}"${rel} aria-label="${escapeHtml(index + 1)}位: ${title}">`,
    `            <div class="rc-rank">${String(index + 1).padStart(2, '0')}</div>`,
    '            <div class="rc-body">',
    `              <span class="rc-tag">${category}</span>`,
    `              <h3 class="rc-title">${title}</h3>`,
    `              <span class="rc-source">${source}</span>`,
    '              <div class="rc-foot">',
    `                <div class="rc-bar"><div class="rc-fill" style="width:${pct}%"></div></div>`,
    `                <span class="rc-score">${score.toFixed(1)} / 5</span>`,
    '              </div>',
    '            </div>',
    '          </a>',
  ].join('\n');
}

function collectCategoryItems(data) {
  const sections = data && data.sections ? data.sections : {};
  const preferred = ['tech', 'research', 'tools', 'business', 'company', 'sns', 'posts'];
  const keys = preferred.concat(Object.keys(sections).filter((k) => !preferred.includes(k)));
  const seen = new Set();
  const items = [];
  for (const key of keys) {
    if (seen.has(key)) continue;
    seen.add(key);
    const list = sections[key];
    if (!Array.isArray(list) || !list.length) continue;
    const item = list.find((x) => x && x.title);
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

function replaceGrid(html, id, replacement) {
  const start = html.indexOf(`<div id="${id}"`);
  if (start === -1) throw new Error(`Missing #${id} in index.html`);
  const lineStart = html.lastIndexOf('\n', start) + 1;
  const endMarker = '\n      </div>\n    </section>';
  const end = html.indexOf(endMarker, start);
  if (end === -1) throw new Error(`Could not find closing section after #${id}`);
  return html.slice(0, lineStart) + replacement + html.slice(end);
}

function updateHomepage(data, slide, slideUrl) {
  if (!fs.existsSync(INDEX_HTML)) {
    console.warn(`[build-homepage-latest] index.html not found at ${INDEX_HTML}`);
    return;
  }

  const archiveEntries = readJson(ARCHIVE_INDEX_JSON, []);
  const totalSlides = Array.isArray(archiveEntries) ? archiveEntries.length : 0;
  const totalItems = Array.isArray(archiveEntries)
    ? archiveEntries.reduce((sum, entry) => sum + (Number(entry.count) || 0), 0)
    : 0;
  const generatedAt = jstTimeFromIso(data.generated_at);
  const slideDate = slide.date;
  const fallbackDate = data.news_date || slideDate;
  const updateTime = generatedAt ? generatedAt.replace(/^\d{4}-\d{2}-\d{2}\s+/, '').replace(' JST', '') : '09:00';
  const rankingItems = collectRankingItems(data, slideUrl);
  const categoryItems = collectCategoryItems(data);
  const rawHeroTitle = data.highlight && data.highlight.title ? data.highlight.title : '最新スライドを公開しました';
  const heroTitle = String(rawHeroTitle)
    .replace(/\s*\|\s*Day Slide\s*\d{4}-\d{2}-\d{2}\s*$/i, '')
    .replace(/\s*\|\s*\d{4}-\d{2}-\d{2}\s*$/i, '')
    .trim() || rawHeroTitle;
  const heroMeta = [
    data.highlight && data.highlight.category,
    data.highlight && sourceName(data.highlight),
    data.highlight && data.highlight.stars ? '★'.repeat(Math.min(data.highlight.stars, 5)) : '',
  ].filter(Boolean).join(' · ');

  let html = fs.readFileSync(INDEX_HTML, 'utf8');

  html = html.replace(/<meta http-equiv="Content-Security-Policy"[\s\S]*?\/>\n\s*/i, '');
  html = replaceFirst(
    html,
    /(<meta name="referrer" content="strict-origin-when-cross-origin" \/>\n)/,
    `$1  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; base-uri 'self'; object-src 'none'; img-src 'self' data: https:; font-src https://fonts.gstatic.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com; connect-src 'self' https://www.google-analytics.com https://*.google-analytics.com; form-action 'self'; upgrade-insecure-requests" />\n`,
    'CSP meta'
  );

  html = replaceFirst(
    html,
    /<a class="cta" id="latestSlideHeroBtn" href="[^"]*">/,
    `<a class="cta" id="latestSlideHeroBtn" href="${slideUrl}">`,
    'header latest slide CTA'
  );
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
  html = replaceFirst(
    html,
    /\s*<p class="hero-summary">[\s\S]*?<\/p>/,
    `\n          <p class="hero-summary">\n            毎日更新。最新データ: <span id="heroUpdatedAt">${escapeHtml(generatedAt || `${fallbackDate} 09:00 JST`)}</span>。<br/>\n            モデル・論文・プロダクトリリースをビジネス／研究／ツールに整理してお届けします。\n          </p>`,
    'hero summary'
  );
  html = replaceFirst(
    html,
    /(?:<!-- fallback:latest-slide -->)?<span id="heroNewsTitle"[\s\S]*?<\/span>(?:<!-- fallback:end -->)?\s*<span class="hero-news-meta" id="heroNewsMeta">[\s\S]*?<\/span>/,
    `<!-- fallback:latest-slide --><span id="heroNewsTitle">${escapeHtml(heroTitle)}</span><!-- fallback:end -->\n              <span class="hero-news-meta" id="heroNewsMeta">${escapeHtml(heroMeta)}</span>`,
    'hero news title and meta'
  );
  html = replaceFirst(
    html,
    /<noscript>\s*(?:<!-- fallback:latest-slide -->)?<span>[\s\S]*?<\/span>(?:<!-- fallback:end -->)?\s*<\/noscript>/,
    `<noscript>\n                <!-- fallback:latest-slide --><span>最新トピック: ${escapeHtml(heroTitle)}。<a href="${slideUrl}">今日のスライド</a>または<a href="presentations/news_archive.html">アーカイブ</a>からご覧ください。</span><!-- fallback:end -->\n              </noscript>`,
    'hero noscript fallback'
  );
  html = replaceFirst(
    html,
    /<a id="heroSlideBtn" class="btn btn-primary" href="[^"]*">/,
    `<a id="heroSlideBtn" class="btn btn-primary" href="${slideUrl}">`,
    'hero slide button'
  );
  html = replaceFirst(
    html,
    /<a id="todaySlideCard" class="main-card is-primary" href="[^"]*">/,
    `<a id="todaySlideCard" class="main-card is-primary" href="${slideUrl}">`,
    'today slide card'
  );
  html = replaceFirst(
    html,
    /<span id="todaySlideDate" class="main-card-date">[\s\S]*?<\/span>/,
    `<span id="todaySlideDate" class="main-card-date">${escapeHtml(slideDate)}</span>`,
    'today slide date'
  );

  const rankingFallback = rankingItems.length
    ? rankingItems.map(rankingCardHtml).join('\n')
    : `          <a class="ranking-card" href="presentations/ai_ranking_report_latest.html">\n            <div class="rc-rank">--</div>\n            <div class="rc-body"><h3 class="rc-title">最新ランキングを開く</h3><span class="rc-source">AI Intelligence Hub</span></div>\n          </a>`;
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
    `        <div id="catGrid" class="cat-grid">\n${catFallback}\n          <noscript>\n            <div class="cat-card"><div class="cat-label">LATEST</div><div class="cat-title">${escapeHtml(heroTitle)}</div><div class="cat-source"><a href="${slideUrl}">今日のスライドを見る →</a></div></div>\n          </noscript>\n        </div>`
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
    /<div class="archive-stat"><span class="archive-stat-num"><em(?: id="statUpdated")?>[\s\S]*?<\/em><\/span><span class="archive-stat-label">(?:Daily Update|Latest Update) \(JST\)<\/span><\/div>/,
    `<div class="archive-stat"><span class="archive-stat-num"><em id="statUpdated">${escapeHtml(updateTime)}</em></span><span class="archive-stat-label">Latest Update (JST)</span></div>`,
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

  const headlines = Array.isArray(data.headlines) ? data.headlines.slice() : [];
  headlines.sort((a, b) => (Number(b.score) || 0) - (Number(a.score) || 0));
  for (const h of headlines) {
    const bucket = CATEGORY_MAP[h.category] || 'tech';
    pushItem(sections, bucket, {
      title: h.title || 'Untitled',
      blurb: blurbFor(h),
      category: bucket,
      date: reportDate || '',
      stars: starsForScore(h.score, h.importance),
      source: normalizeSource(h, h.source),
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

function main() {
  const slide = newestSlide();
  if (!slide) {
    throw new Error(`No day slides found in ${SLIDES_DIR}`);
  }

  const html = fs.readFileSync(slide.filePath, 'utf8');
  const title = extractTitle(html, slide.date);
  const summary = extractSummary(html, title);
  const slideUrl = `presentations/day_slides/${slide.name}`;
  const latestNews = buildSections();

  const data = {
    generated_at: toJstIso(slide.date),
    news_date: latestNews.dailyDate,
    highlight: {
      category: '本日のスライド',
      stars: 5,
      title,
      summary,
      sources: [
        {
          name: 'AI Intelligence Hub',
          url: slideUrl,
        },
      ],
    },
    sections: latestNews.sections,
  };

  fs.mkdirSync(NEWS_DIR, { recursive: true });
  fs.writeFileSync(LATEST_JSON, JSON.stringify(data, null, 2), 'utf8');
  console.log(`Updated ${path.relative(ROOT, LATEST_JSON)} from ${slide.name}`);
  updateHomepage(data, slide, slideUrl);
}

main();
