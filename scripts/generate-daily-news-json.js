#!/usr/bin/env node

/**
 * Daily AI News JSON Generator
 *
 * input/day/配下のテキストファイルを読み込み、JSON形式で出力します。
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
const INPUT_DIR = path.join(__dirname, '../input/day');
const OUTPUT_DIR = path.join(__dirname, '../presentations/api');
const OUTPUT_FILE = path.join(OUTPUT_DIR, 'daily-news.json');
const OUTPUT_LATEST_FILE = path.join(OUTPUT_DIR, 'daily-news-latest.json');

/**
 * テキストファイルを解析してニュースオブジェクトに変換
 */
function parseNewsFile(filePath, filename) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');

    // ファイル名から日付を抽出 (例: 1115.txt -> 2025-11-15)
    const dateMatch = filename.match(/(\d{2})(\d{2})\.txt$/);
    if (!dateMatch) return null;

    const month = dateMatch[1];
    const day = dateMatch[2];
    const date = `2025-${month}-${day}`;

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
      title: sections.title || 'タイトル不明',
      summary: sections.summary || '',
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

  // input/day/ 配下のファイルを取得
  const files = fs.readdirSync(INPUT_DIR)
    .filter(file => file.endsWith('.txt'))
    .sort(); // ファイル名でソート

  console.log(`📁 Found ${files.length} text files in ${INPUT_DIR}\n`);

  // 各ファイルを解析
  const newsItems = [];
  for (const file of files) {
    const filePath = path.join(INPUT_DIR, file);
    const newsItem = parseNewsFile(filePath, file);

    if (newsItem) {
      newsItems.push(newsItem);
      console.log(`✅ Parsed: ${file} - ${newsItem.title}`);
    } else {
      console.log(`⚠️  Skipped: ${file} (empty or invalid)`);
    }
  }

  // 日付降順にソート（新しい順）
  newsItems.sort((a, b) => b.date.localeCompare(a.date));

  // 完全版JSON出力
  const fullData = {
    generatedAt: new Date().toISOString(),
    totalCount: newsItems.length,
    items: newsItems
  };

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(fullData, null, 2), 'utf-8');
  console.log(`\n✅ Generated full JSON: ${OUTPUT_FILE}`);
  console.log(`   Total items: ${newsItems.length}`);

  // 最新10件版JSON出力
  const latestData = {
    generatedAt: new Date().toISOString(),
    totalCount: newsItems.length,
    latestCount: Math.min(10, newsItems.length),
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

module.exports = { parseNewsFile, extractSection, extractLinks };
