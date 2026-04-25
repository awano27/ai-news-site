#!/usr/bin/env node

/**
 * Daily AI News JSON Generator
 *
 * public-pages/news/配下の日次ニューススナップショットを読み込み、
 * 旧 presentations/api 互換のJSON形式で出力します。
 *
 * 使い方:
 *   node scripts/generate-daily-news-json.js
 *
 * 出力:
 *   presentations/api/daily-news.json - 全ニュースのJSON
 *   presentations/api/daily-news-latest.json - 最新10件のJSON
 */

const fs = require('fs');
const path = require('path');

// パス設定
const NEWS_DIR = path.join(__dirname, '../public-pages/news');
const OUTPUT_DIR = path.join(__dirname, '../presentations/api');
const OUTPUT_FILE = path.join(OUTPUT_DIR, 'daily-news.json');
const OUTPUT_LATEST_FILE = path.join(OUTPUT_DIR, 'daily-news-latest.json');

function pad2(value) {
  return String(value).padStart(2, '0');
}

function inferDateFromFilename(filename, now = new Date()) {
  const dateMatch = filename.match(/^(\d{2})(\d{2})(?:-\d+)?\.txt$/);
  if (!dateMatch) return null;

  const month = Number(dateMatch[1]);
  const day = Number(dateMatch[2]);
  let year = now.getFullYear();

  let candidate = new Date(Date.UTC(year, month - 1, day));
  if (Number.isNaN(candidate.getTime())) return null;

  const today = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()));
  if (candidate > today) {
    year -= 1;
    candidate = new Date(Date.UTC(year, month - 1, day));
  }

  return `${candidate.getUTCFullYear()}-${pad2(candidate.getUTCMonth() + 1)}-${pad2(candidate.getUTCDate())}`;
}

function extractFallbackTitle(content) {
  const lines = content
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean);
  return lines[0] || 'タイトル不明';
}

function extractFallbackSummary(content, title) {
  const lines = content
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean)
    .filter(line => line !== title);

  return lines.slice(0, 4).join(' ').slice(0, 280);
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

function articleToNewsItem(article, snapshotDate, filename) {
  const sourceName = article.source || 'source';
  const sourceUrl = article.url || '';
  return {
    date: snapshotDate,
    filename,
    title: article.title || 'タイトル不明',
    summary: article.summary || '',
    surprise: '',
    sources: sourceUrl ? [{ text: sourceName, url: sourceUrl }] : [],
    engineerPoints: '',
    businessPoints: '',
    comparison: '',
    category: article.category || '',
    importance: article.importance || '',
    score: article.score || 0,
    rank: article.rank || 0,
    publishedAt: article.published_at || '',
    source: sourceName,
    url: sourceUrl,
  };
}

function effectiveDailyDate(data, fallbackDate) {
  const sourceDate = data?.metadata?.source_date;
  if (/^\d{4}-\d{2}-\d{2}$/.test(sourceDate || '')) return sourceDate;

  const articles = Array.isArray(data?.articles) ? data.articles : [];
  const publishedDates = articles
    .map(article => String(article.published_at || '').slice(0, 10))
    .filter(date => /^\d{4}-\d{2}-\d{2}$/.test(date))
    .sort((a, b) => b.localeCompare(a));

  return publishedDates[0] || fallbackDate;
}

function loadDailySnapshots() {
  const indexPath = path.join(NEWS_DIR, 'daily_index.json');
  let entries;

  if (fs.existsSync(indexPath)) {
    entries = readJson(indexPath);
  } else {
    entries = fs.readdirSync(NEWS_DIR)
      .filter(name => /^\d{4}-\d{2}-\d{2}_daily\.json$/.test(name))
      .map(file => ({ date: file.replace('_daily.json', ''), file }));
  }

  const seenDates = new Set();

  return entries
    .filter(entry => entry && entry.date && entry.file)
    .sort((a, b) => b.date.localeCompare(a.date))
    .map(entry => {
      const filePath = path.join(NEWS_DIR, entry.file);
      if (!fs.existsSync(filePath)) {
        return {
          date: entry.date,
          filename: entry.file,
          file: entry.file,
          title: `Daily AI News ${entry.date}`,
          summary: '',
          count: entry.count || 0,
          items: [],
        };
      }

      let data;
      try {
        data = readJson(filePath);
      } catch (error) {
        console.error(`Error reading ${entry.file}:`, error.message);
        return {
          date: entry.date,
          filename: entry.file,
          file: entry.file,
          title: `Daily AI News ${entry.date}`,
          summary: '',
          count: entry.count || 0,
          items: [],
        };
      }

      const articles = Array.isArray(data.articles) ? data.articles : [];
      const effectiveDate = effectiveDailyDate(data, entry.date);
      if (seenDates.has(effectiveDate)) return null;
      seenDates.add(effectiveDate);

      const first = articles[0] ? articleToNewsItem(articles[0], effectiveDate, entry.file) : null;
      return {
        date: effectiveDate,
        snapshotDate: entry.date,
        filename: entry.file,
        file: entry.file,
        title: first ? first.title : `Daily AI News ${effectiveDate}`,
        summary: first ? first.summary : '',
        count: entry.count || articles.length,
        items: articles.slice(0, 3).map(article => articleToNewsItem(article, effectiveDate, entry.file)),
      };
    })
    .filter(Boolean)
    .sort((a, b) => b.date.localeCompare(a.date));
}

/**
 * テキストファイルを解析してニュースオブジェクトに変換
 */
function parseNewsFile(filePath, filename) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');

    const date = inferDateFromFilename(filename);
    if (!date) return null;

    // 空ファイルチェック
    if (content.trim().length === 0) return null;

    // セクションを抽出
    const sections = {
      title: extractSection(content, 'タイトル'),
      summary: extractSection(content, '概要'),
      surprise: extractSection(content, 'なぜサプライズか'),
      sources: extractSection(content, '一次情報リンク'),
      engineerPoints: extractSection(content, 'エンジニア視点'),
      businessPoints: extractSection(content, 'ビジネス視点'),
      comparison: extractSection(content, '他の有力候補との比較')
    };

    return {
      date,
      filename,
      title: sections.title || extractFallbackTitle(content),
      summary: sections.summary || extractFallbackSummary(content, sections.title || extractFallbackTitle(content)),
      surprise: sections.surprise || '',
      sources: extractLinks(sections.sources),
      engineerPoints: sections.engineerPoints || '',
      businessPoints: sections.businessPoints || '',
      comparison: sections.comparison || '',
      rawContent: content
    };
  } catch (error) {
    console.error(`Error parsing ${filename}:`, error.message);
    return null;
  }
}

/**
 * テキストから指定セクションを抽出
 */
function extractSection(content, sectionName) {
  // セクション見出しのパターン (例: "1. **タイトル**" または "2. **概要（3〜5行）**")
  const patterns = [
    new RegExp(`\\d+\\.\\s*\\*\\*${sectionName}[^*]*\\*\\*\\s*\\n([\\s\\S]*?)(?=\\n---\\n|\\n\\d+\\.\\s*\\*\\*|$)`, 'i'),
    new RegExp(`#+\\s*${sectionName}[^\\n]*\\n([\\s\\S]*?)(?=\\n---\\n|\\n#+\\s|$)`, 'i'),
    new RegExp(`${sectionName}[\\s\\S]*?\\n([\\s\\S]*?)(?=\\n---\\n|\\n\\d+\\.|$)`, 'i')
  ];

  for (const pattern of patterns) {
    const match = content.match(pattern);
    if (match && match[1]) {
      return match[1].trim();
    }
  }

  return '';
}

/**
 * テキストからリンクを抽出
 */
function extractLinks(text) {
  if (!text) return [];

  const links = [];

  // Markdown形式のリンク [text](url)
  const mdLinkPattern = /\[([^\]]+)\]\(([^)]+)\)/g;
  let match;
  while ((match = mdLinkPattern.exec(text)) !== null) {
    links.push({
      text: match[1],
      url: match[2]
    });
  }

  // プレーンURLも抽出
  const urlPattern = /https?:\/\/[^\s\)]+/g;
  const urls = text.match(urlPattern) || [];
  urls.forEach(url => {
    if (!links.some(link => link.url === url)) {
      links.push({
        text: url,
        url: url
      });
    }
  });

  return links;
}

/**
 * メイン処理
 */
function main() {
  console.log('🚀 Daily AI News JSON Generator');
  console.log('================================\n');

  // 出力ディレクトリ作成
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    console.log(`✅ Created output directory: ${OUTPUT_DIR}`);
  }

  const newsItems = loadDailySnapshots();
  const totalArticles = newsItems.reduce((total, entry) => total + (entry.count || 0), 0);
  console.log(`📁 Loaded ${newsItems.length} daily snapshots from ${NEWS_DIR}\n`);

  // 日付降順にソート（新しい順）
  newsItems.sort((a, b) => b.date.localeCompare(a.date));

  // 完全版JSON出力
  const fullData = {
    generatedAt: new Date().toISOString(),
    totalCount: newsItems.length,
    totalArticles,
    entries: newsItems,
    items: newsItems
  };

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(fullData, null, 2), 'utf-8');
  console.log(`\n✅ Generated full JSON: ${OUTPUT_FILE}`);
  console.log(`   Total days: ${newsItems.length}`);
  console.log(`   Total articles: ${totalArticles}`);

  // 最新10件版JSON出力
  const latestData = {
    generatedAt: new Date().toISOString(),
    totalCount: newsItems.length,
    totalArticles,
    latestCount: Math.min(10, newsItems.length),
    entries: newsItems.slice(0, 10),
    items: newsItems.slice(0, 10)
  };

  fs.writeFileSync(OUTPUT_LATEST_FILE, JSON.stringify(latestData, null, 2), 'utf-8');
  console.log(`✅ Generated latest JSON: ${OUTPUT_LATEST_FILE}`);
  console.log(`   Latest items: ${latestData.latestCount}`);

  console.log('\n🎉 JSON generation completed!\n');

  // 統計情報
  console.log('📊 Statistics:');
  console.log(`   Date range: ${newsItems[newsItems.length - 1]?.date} ~ ${newsItems[0]?.date}`);
  console.log(`   Output files:`);
  console.log(`     - ${OUTPUT_FILE}`);
  console.log(`     - ${OUTPUT_LATEST_FILE}`);
}

// 実行
if (require.main === module) {
  main();
}

module.exports = { parseNewsFile, extractSection, extractLinks, inferDateFromFilename };
