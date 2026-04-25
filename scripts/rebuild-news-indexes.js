#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const NEWS_DIR = path.join(__dirname, '../public-pages/news');
const ARCHIVE_INDEX = path.join(NEWS_DIR, 'archive_index.json');
const DAILY_INDEX = path.join(NEWS_DIR, 'daily_index.json');
const VERSION_FILE = path.join(NEWS_DIR, 'version.json');
const DAILY_LATEST_FILE = path.join(NEWS_DIR, 'daily_latest.json');

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function getCount(data) {
  if (typeof data.count === 'number') return data.count;
  if (Array.isArray(data.items)) return data.items.length;
  if (Array.isArray(data.articles)) return data.articles.length;
  if (typeof data?.metadata?.total_articles === 'number') return data.metadata.total_articles;
  return 0;
}

function getDateFromName(name) {
  const match = name.match(/^(\d{4}-\d{2}-\d{2})(?:_daily)?\.json$/);
  return match ? match[1] : null;
}

function buildIndexes() {
  const files = fs.readdirSync(NEWS_DIR)
    .filter((name) => name.endsWith('.json'))
    .filter((name) => !['archive_index.json', 'daily_index.json', 'daily_latest.json', 'version.json'].includes(name));

  const archiveEntriesByDate = new Map();
  const dailyEntries = [];
  let newestDaily = null;

  for (const name of files) {
    const date = getDateFromName(name);
    if (!date) continue;

    const filePath = path.join(NEWS_DIR, name);
    let data;
    try {
      data = readJson(filePath);
    } catch (error) {
      console.error(`Failed to read ${name}: ${error.message}`);
      continue;
    }

    const count = getCount(data);
    const isDaily = name.endsWith('_daily.json');
    const entry = { date, file: name, count };

    const existingArchiveEntry = archiveEntriesByDate.get(date);
    if (
      !existingArchiveEntry ||
      (isDaily && !existingArchiveEntry.file.endsWith('_daily.json')) ||
      (isDaily === existingArchiveEntry.file.endsWith('_daily.json') && name.localeCompare(existingArchiveEntry.file) < 0)
    ) {
      archiveEntriesByDate.set(date, entry);
    }

    if (isDaily) {
      const dailyEntry = {
        date,
        file: name,
        count,
        extracted_at: data?.metadata?.extracted_at || data?.extracted_at || '',
        source: data?.metadata?.source || data?.source || '',
      };
      dailyEntries.push(dailyEntry);

      if (!newestDaily || date > newestDaily.date) {
        newestDaily = { date, data };
      }
    }
  }

  const archiveEntries = Array.from(archiveEntriesByDate.values()).sort((a, b) => {
    if (a.date !== b.date) return b.date.localeCompare(a.date);
    return a.file.localeCompare(b.file);
  });
  dailyEntries.sort((a, b) => b.date.localeCompare(a.date));

  fs.writeFileSync(ARCHIVE_INDEX, JSON.stringify(archiveEntries, null, 2), 'utf8');
  fs.writeFileSync(DAILY_INDEX, JSON.stringify(dailyEntries, null, 2), 'utf8');

  if (newestDaily) {
    fs.writeFileSync(DAILY_LATEST_FILE, JSON.stringify(newestDaily.data, null, 2), 'utf8');
  }

  const now = new Date();
  const iso = now.toISOString();
  const version = {
    version: iso,
    sha: crypto.createHash('md5').update(iso).digest('hex').slice(0, 8),
    updated: iso,
    total_entries: archiveEntries.length,
    daily_entries: dailyEntries.length,
  };
  fs.writeFileSync(VERSION_FILE, JSON.stringify(version, null, 2), 'utf8');

  console.log(`Rebuilt archive_index.json (${archiveEntries.length} entries)`);
  console.log(`Rebuilt daily_index.json (${dailyEntries.length} entries)`);
  if (newestDaily) {
    console.log(`Updated daily_latest.json (${newestDaily.date})`);
  }
}

buildIndexes();
