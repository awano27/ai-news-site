#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const SLIDES_DIR = path.join(ROOT, 'presentations', 'day_slides');
const NEWS_DIR = path.join(ROOT, 'news');
const LATEST_JSON = path.join(NEWS_DIR, 'latest.json');
const DAILY_LATEST_JSON = path.join(ROOT, 'public-pages', 'news', 'daily_latest.json');

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

function normalizeSource(article) {
  const sourceName = article.source || article.source_name || 'source';
  return {
    name: sourceName,
    url: article.url || '#',
  };
}

function starsFor(article) {
  if (article.importance === 'high') return 4;
  if (article.importance === 'medium') return 3;
  return 2;
}

function buildSections() {
  if (!fs.existsSync(DAILY_LATEST_JSON)) return {};

  let data;
  try {
    data = JSON.parse(fs.readFileSync(DAILY_LATEST_JSON, 'utf8'));
  } catch {
    return {};
  }

  const sections = {};
  const articles = Array.isArray(data.articles) ? data.articles : [];
  for (const article of articles) {
    const category = article.category || 'posts';
    if (!sections[category]) sections[category] = [];
    if (sections[category].length >= 6) continue;

    sections[category].push({
      title: article.title || 'Untitled',
      blurb: article.summary || '',
      category,
      date: (article.published_at || '').slice(0, 10) || '',
      stars: starsFor(article),
      source: normalizeSource(article),
    });
  }

  return sections;
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

  const data = {
    generated_at: toJstIso(slide.date),
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
    sections: buildSections(),
  };

  fs.mkdirSync(NEWS_DIR, { recursive: true });
  fs.writeFileSync(LATEST_JSON, JSON.stringify(data, null, 2), 'utf8');
  console.log(`Updated ${path.relative(ROOT, LATEST_JSON)} from ${slide.name}`);
}

main();
