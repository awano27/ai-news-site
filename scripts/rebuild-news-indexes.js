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

function effectiveDailyDate(data, fallbackDate) {
  const sourceDate = data?.metadata?.source_date;
  if (/^\d{4}-\d{2}-\d{2}$/.test(sourceDate || '')) return sourceDate;

  const articles = Array.isArray(data?.articles) ? data.articles : [];
  const publishedDates = articles
    .map((article) => String(article?.published_at || '').slice(0, 10))
    .filter((date) => /^\d{4}-\d{2}-\d{2}$/.test(date))
    .sort((a, b) => b.localeCompare(a));

  return publishedDates[0] || fallbackDate;
}

function buildIndexes() {
  const files = fs.readdirSync(NEWS_DIR)
    .filter((name) => name.endsWith('.json'))
    .filter((name) => !['archive_index.json', 'daily_index.json', 'daily_latest.json', 'version.json'].includes(name));

  const archiveEntriesByDate = new Map();
  const dailyEntriesByDate = new Map();
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
    const entryDate = isDaily ? effectiveDailyDate(data, date) : date;
    const entry = { date: entryDate, file: name, count };
    if (isDaily && entryDate !== date) {
      entry.snapshot_date = date;
    }

    const existingArchiveEntry = archiveEntriesByDate.get(entryDate);
    if (
      !existingArchiveEntry ||
      (isDaily && !existingArchiveEntry.file.endsWith('_daily.json')) ||
      (isDaily === existingArchiveEntry.file.endsWith('_daily.json') && name.localeCompare(existingArchiveEntry.file) < 0)
    ) {
      archiveEntriesByDate.set(entryDate, entry);
    }

    // Date-named snapshots (YYYY-MM-DD.json) also feed the daily index so
    // downstream consumers keep getting current data after the *_daily.json
    // extraction pipeline stopped (last file: 2026-03-20). A *_daily.json
    // file still wins over a date-named file for the same date because it
    // carries the richer multi-article payload.
    const dailyEntry = {
      date: entryDate,
      file: name,
      count,
      snapshot_date: entryDate !== date ? date : undefined,
      extracted_at: data?.metadata?.extracted_at || data?.extracted_at || '',
      source_date: data?.metadata?.source_date || '',
      source: data?.metadata?.source || data?.source || '',
    };
    const existingDailyEntry = dailyEntriesByDate.get(entryDate);
    const existingIsDaily = existingDailyEntry ? existingDailyEntry.file.endsWith('_daily.json') : false;
    if (
      !existingDailyEntry ||
      (isDaily && !existingIsDaily) ||
      (isDaily === existingIsDaily && name.localeCompare(existingDailyEntry.file) < 0)
    ) {
      dailyEntriesByDate.set(entryDate, dailyEntry);
    }

    if (
      !newestDaily ||
      entryDate > newestDaily.date ||
      (entryDate === newestDaily.date && isDaily && !newestDaily.isDaily)
    ) {
      newestDaily = { date: entryDate, data, isDaily };
    }
  }

  const archiveEntries = Array.from(archiveEntriesByDate.values()).sort((a, b) => {
    if (a.date !== b.date) return b.date.localeCompare(a.date);
    return a.file.localeCompare(b.file);
  });
  const dailyEntries = Array.from(dailyEntriesByDate.values()).sort((a, b) => b.date.localeCompare(a.date));

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
