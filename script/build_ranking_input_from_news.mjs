#!/usr/bin/env node
// Build a draft ranking input text (Top30) from news JSON files
// Output: presentations/ai_ranking_input_latest.txt

import { readFileSync, writeFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';

const ROOT = process.cwd();
const NEWS_DIR = join(ROOT, 'news');
const OUT_FILE = join(ROOT, 'presentations', 'ai_ranking_input_latest.txt');

function loadJSON(p) {
  try { return JSON.parse(readFileSync(p, 'utf-8')); } catch { return null; }
}

function ymd(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth()+1).padStart(2,'0');
  const dd = String(d.getDate()).padStart(2,'0');
  return `${y}-${m}-${dd}`;
}

function jaDate(s) {
  const [y,m,d] = s.split('-').map(x=>parseInt(x,10));
  return `${y}年${m}月${d}日`;
}

function clamp(n, a, b){ return Math.max(a, Math.min(b, n)); }

function scoreFor(category, stars){
  const s = Number(stars||0);
  let eng=2, biz=2;
  switch((category||'').toLowerCase()){
    case 'tools':
      eng = clamp(3 + Math.round(s/2), 1, 5);
      biz = clamp(2 + Math.round(s/3), 1, 5);
      break;
    case 'business':
      eng = clamp(2 + Math.round(s/3), 1, 5);
      biz = clamp(3 + Math.round(s/2), 1, 5);
      break;
    case 'company':
      eng = clamp(2 + Math.round(s/3), 1, 5);
      biz = clamp(2 + Math.round(s/3), 1, 5);
      break;
    case 'sns':
      eng = clamp(1 + Math.round(s/4), 1, 5);
      biz = clamp(1 + Math.round(s/4), 1, 5);
      break;
    default:
      eng = clamp(2 + Math.round(s/3), 1, 5);
      biz = clamp(2 + Math.round(s/3), 1, 5);
  }
  return { eng, biz, total: eng + biz };
}

function main(){
  if (!existsSync(NEWS_DIR)) {
    console.error('news directory not found');
    process.exit(1);
  }
  const latest = loadJSON(join(NEWS_DIR, 'latest.json')) || {};
  const base = latest.generated_at ? new Date(latest.generated_at) : new Date();

  // collect up to 31 daily files
  const days = [];
  for(let i=0;i<31;i++){
    const d = ymd(new Date(base.getTime() - i*24*3600*1000));
    const p = join(NEWS_DIR, `${d}.json`);
    if (existsSync(p)) days.push([d, loadJSON(p)]);
  }
  // if no per-day files, fallback to latest
  if (days.length === 0) days.push([ymd(base), latest]);

  const items = [];
  for (const [d, dj] of days){
    const sections = (dj && dj.sections) || {};
    for (const k of ['business','tools','company','sns']){
      for (const it of (sections[k]||[])){
        items.push({
          date: it.date || d,
          title: it.title || '',
          blurb: (it.blurb || '').replace(/\s+/g,' ').trim(),
          category: it.category || k,
          stars: it.stars || 0,
          source: (it.source && it.source.name) || 'unknown'
        });
      }
    }
  }

  // aggregate: pick top 30 by total score (from stars & category)
  const ranked = items.map(it => ({...it, ...scoreFor(it.category, it.stars)}))
    .sort((a,b)=> (b.total - a.total) || (b.stars - a.stars) || (b.date||'').localeCompare(a.date||''))
    .slice(0, 30);

  // prepare header period
  const dates = ranked.map(x=>x.date).filter(Boolean).sort();
  const start = dates[0] || ymd(new Date(base.getTime()-30*24*3600*1000));
  const end = dates[dates.length-1] || ymd(base);

  // key points
  const catCount = ranked.reduce((m,it)=>{ m[it.category]=(m[it.category]||0)+1; return m; }, {});
  const topCat = Object.entries(catCount).sort((a,b)=>b[1]-a[1]).slice(0,2).map(([k,v])=>`${k}: ${v}件`).join(', ');
  const avgTotal = (ranked.reduce((s,it)=>s+it.total,0) / (ranked.length||1)).toFixed(1);
  const keyPoints = [
    `トップカテゴリ: ${topCat||'N/A'}`,
    `平均スコア(Eng+Biz): ${avgTotal}`,
    `期間内件数: ${items.length}（候補から上位30件を抽出）`
  ];

  // sector table from categories
  const sectorRows = [
    ['モデル・LLM','LLM/生成モデル', String(Math.round((catCount['company']||0)+(catCount['sns']||0)/2)), '7.0', '生成/要約/対話'],
    ['ツール・SDK','開発・運用', String(catCount['tools']||0), '7.5', '開発効率/自動化'],
    ['ビジネス活用','業務適用', String(catCount['business']||0), '7.0', '業務効率/導入効果']
  ];

  // build lines according to parser pattern
  const lines = [];
  lines.push(`直近1ヶ月（${jaDate(start)}から${jaDate(end)}）`);
  lines.push('');
  lines.push('**キー points:**');
  for (const k of keyPoints) lines.push(`- ${k}`);
  lines.push('');
  lines.push('**ランキング概要**');
  let rank = 1;
  for (const it of ranked){
    const desc = (it.blurb || it.title || '').replace(/[\r\n]+/g,' ').replace(/\.+$/,'') + '.';
    const benefits = `活用領域: ${it.category}。出典: ${it.source}。`;
    lines.push(`${rank}. **${it.title}**: ${desc} Eng Tool: ${it.eng}, Biz Eff: ${it.biz}, 合計: ${it.total}. ${benefits}.`);
    rank++;
  }
  lines.push('');
  lines.push('| セクター | 代表技術 | 件数 | 平均スコア | 活用例 |');
  lines.push('|---|---|---:|---:|---|');
  for (const r of sectorRows){
    lines.push(`| ${r[0]} | ${r[1]} | ${r[2]} | ${r[3]} | ${r[4]} |`);
  }

  writeFileSync(OUT_FILE, lines.join('\n'), 'utf-8');
  console.log('wrote', OUT_FILE, `${ranked.length} items`);
}

main();

