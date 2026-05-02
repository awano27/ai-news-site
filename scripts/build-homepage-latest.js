#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const SLIDES_DIR = path.join(ROOT, 'presentations', 'day_slides');
const NEWS_DIR = path.join(ROOT, 'news');
const LATEST_JSON = path.join(NEWS_DIR, 'latest.json');
const AUTO_DAILY_JSON = path.join(ROOT, 'public-pages', 'api', 'auto_daily_report', 'latest.json');
const DAILY_LATEST_JSON = path.join(ROOT, 'public-pages', 'news', 'daily_latest.json'); // legacy fallback only

function decodeEntities(value) {
  return String(value || '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
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
}

main();
