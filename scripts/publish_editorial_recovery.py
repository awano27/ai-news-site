#!/usr/bin/env python3
"""Publish an explicit three-article source-reviewed provisional edition offline.

This is never called by the automatic collector. It requires a dated editorial
manifest and records assistant document review, not provider/model success or
independent verification of the publishers' claims. All rendering is staged and
strictly validated before selected output files replace current local files.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.build_search_index import canonical_url, atomic_write, json_bytes
from src.auto_collect.quality import is_japanese_summary

MODE='editorial_review'
STATUS='editorial_reviewed'
NOTICE='編集確認済み・3件の暫定版'
EXPLANATION='アシスタントが原文を読み、出典と掲載日を確認した暫定版です。発表元の主張を独立検証したものではありません。自動収集は未復旧です。重要度スコアは未評価です。'
CONTENT_FIELDS=('title','summary','impact','url','source','published_at')
REVIEW_FIELDS=('source_url','source_date','reviewed_at','review_method','reviewer','scope')


def _require(ok,message):
    if not ok: raise ValueError('editorial recovery: '+message)


def fingerprint(article):
    payload={key:article[key] for key in CONTENT_FIELDS}
    return hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def prepare_editorial(manifest,edition):
    day=date.fromisoformat(edition)
    _require(isinstance(manifest,dict) and manifest.get('version')==1,'manifest version must be 1')
    _require(manifest.get('edition_date')==edition,'edition date mismatch')
    rows=manifest.get('articles')
    _require(isinstance(rows,list) and len(rows)==3,'exactly three reviewed articles required')
    articles=[];seen=set()
    for row in rows:
        _require(isinstance(row,dict),'article must be an object')
        _require(all(isinstance(row.get(k),str) and row[k].strip() for k in CONTENT_FIELDS),'copy and source metadata must be nonempty text')
        _require(is_japanese_summary(row['summary']) and re.search(r'[ぁ-ゖァ-ヺ一-鿿]',row['title']),'Japanese title and substantive summary required')
        _require(is_japanese_summary(row['impact']),'reviewed Japanese audience text required')
        key=canonical_url(row['url'])
        _require(key and key not in seen,'unsafe or duplicate article URL');seen.add(key)
        published=date.fromisoformat(row['published_at'])
        _require(row['published_at']==published.isoformat() and day-timedelta(days=1)<=published<=day,'source publication date must be today or yesterday')
        review=row.get('review')
        _require(isinstance(review,dict) and all(isinstance(review.get(k),str) and review[k].strip() for k in REVIEW_FIELDS),'complete source review metadata required')
        _require(canonical_url(review['source_url'])==key,'review source URL does not match article')
        _require(review['source_date']==row['published_at'],'source date mismatch')
        _require(review['review_method']=='ai_document_review' and review['reviewer']=='assistant','only explicit assistant document review is supported')
        reviewed=date.fromisoformat(review['reviewed_at'])
        _require(reviewed.isoformat()==review['reviewed_at'] and published<=reviewed<=day,'invalid review date')
        article={k:row[k] for k in CONTENT_FIELDS}
        article.update(evidence={'impact_ja':row['impact']},type='news',category='記事',score=0,score_status='unscored',processing_status=STATUS,
                       editorial_review={k:review[k] for k in REVIEW_FIELDS})
        article['editorial_review']['content_sha256']=fingerprint(article)
        articles.append(article)
    sources=sorted({a['source'] for a in articles})
    _require(len(sources)>=2,'at least two publishers required')
    quality={'mode':MODE,'status':STATUS,'date':edition,'article_count':3,'japanese_count':3,
             'sources':sources,'notice':NOTICE,'review_method':'ai_document_review','reviewer':'assistant',
             'automatic_collection_status':'not_recovered','independent_claim_verification':False,
             'input_count':3,'excluded_count':0,'excluded':[]}
    return articles,quality


def validate_editorial_quality(daily):
    quality=daily.get('quality') or {}
    _require(quality.get('mode')==MODE and quality.get('status')==STATUS,'distinct editorial status required')
    _require(not quality.get('provider') and not quality.get('model'),'editorial mode must not claim provider/model provenance')
    _require(quality.get('automatic_collection_status')=='not_recovered','automatic collection recovery must not be claimed')
    items=daily.get('items');_require(isinstance(items,list),'items required')
    rows=[]
    for item in items:
        _require(isinstance(item,dict) and item.get('type')=='news' and item.get('processing_status')==STATUS,'editorial processing_status required for every item')
        _require(item.get('score')==0 and item.get('score_status')=='unscored','automatic ranking must not be claimed')
        _require(not item.get('claim_evidence') and not item.get('evidence_label') and not (item.get('evidence') or {}).get('evidence_label'),'editorial review does not confer a verification badge')
        review=item.get('editorial_review')
        _require(isinstance(review,dict),'review record required')
        _require(review.get('content_sha256')==fingerprint(item),'reviewed copy fingerprint mismatch')
        rows.append({**{k:item.get(k) for k in CONTENT_FIELDS},'review':review})
    _,expected=prepare_editorial({'version':1,'edition_date':daily.get('date'),'articles':rows},daily.get('date'))
    _require(daily.get('total')==3,'edition total mismatch')
    _require(quality==expected,'quality metadata does not match reviewed edition')


def _write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(json_bytes(value))


def _decorate(text,*,kind,edition,articles,generated_iso):
    description=f'{edition} {NOTICE}。{EXPLANATION}'
    generated_jst=datetime.fromisoformat(generated_iso).astimezone(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M JST')
    text=re.sub(r'Generated:?\s+[^<]*',f'Generated: {generated_jst}',text)
    sources=''.join(f'<li><a href="{html.escape(a["url"],quote=True)}" target="_blank" rel="noopener">{html.escape(a["title"])}</a> — 原文掲載日: {a["published_at"]}<br>対象: {html.escape(a["impact"])}</li>' for a in articles)
    notice=f'<aside id="editorial-publication-notice" style="margin:1rem auto;padding:1rem;max-width:1200px;border:1px solid #e5ad54;background:#18212e;color:#f4e5c6;line-height:1.8"><strong>{NOTICE}</strong><br>{EXPLANATION}<br>版の日付: {edition}<ul>{sources}</ul></aside>'
    if kind=='homepage':
        # Homepage identity and styling are independent of the daily edition.
        return re.sub(r'(<body\b[^>]*>)',lambda m:m[1]+notice,text,count=1)
    text=re.sub(r'(<meta name="description" content=")[^"]*(">)',lambda m:m[1]+html.escape(description,quote=True)+m[2],text)
    text=text.replace('</title>',f' | {NOTICE}</title>',1)
    style='<style>.score,.row-score,.top3-score,.score-legend,#sort-score{display:none!important}</style>'
    text=text.replace('</head>',f'<meta name="publication:mode" content="{MODE}">\n'+style+'</head>',1)
    text=re.sub(r'(<body\b[^>]*>)',lambda m:m[1]+notice,text,count=1)
    if kind=='daily':
        text=re.sub(r'<p class="hero-lead">.*?</p>',f'<p class="hero-lead">{NOTICE}。{EXPLANATION}</p>',text,count=1,flags=re.S)
        # Do not present an uncomputed importance metric as a measured result.
        text=text.replace('<div class="metric-num">0</div><div class="metric-label">見逃せない</div>','<div class="metric-num">—</div><div class="metric-label">重要度未評価</div>')
    elif kind=='report':
        text=re.sub(r'<p class="hero-sub">.*?</p>',f'<p class="hero-sub">{NOTICE}。{EXPLANATION}</p>',text,count=1,flags=re.S)
        text=text.replace('自動収集レポート',NOTICE).replace('情報源: RSS / Hacker News / GitHub / HuggingFace &mdash; ローカルLLM: Ollama gemma3:4b','情報源: 記載した原文。処理: アシスタントによる原文確認・日本語編集')
        text=text.replace('Top 3 of the day','今回確認した3件')
        text=text.replace('<div class="kpi-n">0</div><div class="kpi-l">重要記事</div>','<div class="kpi-n">—</div><div class="kpi-l">重要度未評価</div>')
        # Scores and historical automatic/full-feed counts are not comparable.
        text=text.replace('</head>','<style>#charts .chart-cell:nth-child(2),#charts .chart-cell:nth-child(3){display:none}</style></head>',1)
    return text


def _merge_archive(stage,edition,report):
    filename=f'auto_daily_report_{edition.replace("-","_")}.html'
    for name in ('index','searchable'):
        path=stage/f'presentations/daily_reports/{name}.json'
        data=json.loads(path.read_text()) if path.exists() else {'reports':[]}
        _require(isinstance(data,dict) and isinstance(data.get('reports'),list),'invalid existing report archive index')
        _require(not any(row.get('date')==edition for row in data['reports']),'dated report archive already exists')
        row={'date':edition,'file':filename}
        if name=='searchable':row.update(total=3,high=0,titles=[a['title'] for a in report['headlines']],publication_mode=MODE)
        data['reports'].append(row);data['reports'].sort(key=lambda r:r['date'],reverse=True)
        data.update(generated=edition,count=len(data['reports']))
        _write_json(path,data)


def _copy_inputs(root,stage):
    files=['index.html','scripts/build-homepage-latest.js','public-pages/news/search_index.json','public-pages/news/archive_index.json',
           'presentations/daily_reports/index.json','presentations/daily_reports/searchable.json','presentations/news_archive.html',
           'config/reviewed_news_summaries.json','news/latest.json','presentations/day_slides/list.json','presentations/day_slides/meta_index.json']
    # Only HTML and metadata are needed; do not copy images or unrelated assets.
    files += [str(p.relative_to(root)) for p in (root/'presentations/day_slides').glob('day_slide_*.html')]
    for relative in files:
        source=root/relative
        if source.exists():
            target=stage/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)


def publish_editorial(root,manifest,edition):
    root=Path(root).resolve();articles,quality=prepare_editorial(manifest,edition)
    generated_iso=datetime.now(timezone.utc).isoformat()
    current=root/'daily-news/data.json'
    if current.exists():
        existing=json.loads(current.read_text())
        _require(date.fromisoformat(existing['date'])<date.fromisoformat(edition),'refusing to replace same or newer current edition')
    for relative in (f'daily-news/archive/{edition}.html',f'public-pages/news/daily/{edition}.json',f'presentations/daily_reports/auto_daily_report_{edition.replace("-","_")}.html'):
        _require(not (root/relative).exists(),'refusing to replace existing dated archive')
    _require((root/'index.html').exists() and (root/'scripts/build-homepage-latest.js').exists(),'homepage and builder inputs required')
    from src.auto_collect import daily_news_page
    from src.auto_collect.formatter import DayFileFormatter
    from src.auto_collect.html_report_parser import parse_daily_txt
    from src.auto_collect.html_report_renderer import generate_html
    from scripts.sync_daily_search import sync_daily_search
    from scripts.check_daily_publication import Source,verify
    with tempfile.TemporaryDirectory(prefix='editorial-stage-') as temporary:
        stage=Path(temporary);_copy_inputs(root,stage)
        prior_search=json.loads((stage/'public-pages/news/search_index.json').read_text()) if (stage/'public-pages/news/search_index.json').exists() else []
        day=date.fromisoformat(edition);transport=stage/f'input/day/{day:%m%d}.txt'
        DayFileFormatter().write(articles,transport,day)
        parsed=parse_daily_txt(transport)
        byurl={a['url']:a for a in articles}
        for item in parsed['headlines']:
            original=byurl[item['url']]
            item.update({k:original[k] for k in ('type','published_at','processing_status','score_status','editorial_review')})
        report_html,report=generate_html(parsed,stage/'presentations/daily_reports','https://visionhub.jp/presentations/daily_reports/og/default.png')
        report['quality']=quality
        report['generated_iso']=generated_iso
        report_html=_decorate(report_html,kind='report',edition=edition,articles=articles,generated_iso=generated_iso)
        report_dir=stage/'presentations';report_dir.mkdir(exist_ok=True)
        (report_dir/'auto_daily_report.html').write_text(report_html)
        _write_json(report_dir/'auto_daily_report.json',report)
        _write_json(stage/'public-pages/api/auto_daily_report/latest.json',report)
        archive=stage/f'presentations/daily_reports/auto_daily_report_{edition.replace("-","_")}.html';archive.parent.mkdir(parents=True,exist_ok=True)
        archive.write_text(report_html.replace('https://visionhub.jp/presentations/auto_daily_report.html',f'https://visionhub.jp/{archive.relative_to(stage)}'))
        _merge_archive(stage,edition,report)
        saved=(daily_news_page.DAILY_NEWS_DIR,daily_news_page.ARCHIVE_DIR)
        try:
            daily_news_page.DAILY_NEWS_DIR=stage/'daily-news';daily_news_page.ARCHIVE_DIR=stage/'daily-news/archive'
            daily_news_page.generate_daily_news(day,articles,quality=quality)
        finally:daily_news_page.DAILY_NEWS_DIR,daily_news_page.ARCHIVE_DIR=saved
        daily_path=stage/'daily-news/data.json';daily=json.loads(daily_path.read_text());daily['generated_iso']=generated_iso
        for item in daily['items']:
            original=byurl[item['url']];item.update(impact=original['impact'],score_status='unscored',editorial_review=original['editorial_review'])
        _write_json(daily_path,daily)
        daily_html=(stage/'daily-news/index.html').read_text()
        daily_html=re.sub(r'(<script id="report-data" type="application/json">).*?(</script>)',lambda m:m[1]+json.dumps(daily,ensure_ascii=False).replace('<','\\u003c')+m[2],daily_html,flags=re.S)
        daily_html=_decorate(daily_html,kind='daily',edition=edition,articles=articles,generated_iso=generated_iso)
        (stage/'daily-news/index.html').write_text(daily_html);(stage/f'daily-news/archive/{edition}.html').write_text(daily_html)
        sync_daily_search(stage)
        search=json.loads((stage/'public-pages/news/search_index.json').read_text())
        _require(all(row in search for row in prior_search),'historical search content changed')
        subprocess.run(['node',str(stage/'scripts/build-homepage-latest.js')],check=True,capture_output=True,text=True)
        verify(Source(stage),edition,require_quality=True)
        paths=[f'input/day/{day:%m%d}.txt','daily-news/data.json','daily-news/index.html',f'daily-news/archive/{edition}.html',
               'presentations/auto_daily_report.html','presentations/auto_daily_report.json',str(archive.relative_to(stage)),
               'presentations/daily_reports/index.json','presentations/daily_reports/searchable.json','public-pages/api/auto_daily_report/latest.json',
               f'public-pages/news/daily/{edition}.json','public-pages/news/search_index.json','index.html','news/latest.json','presentations/news_archive.html']
        paths=[p for p in paths if (stage/p).exists()]
        for relative in paths:atomic_write(root/relative,(stage/relative).read_bytes())
    return {'date':edition,'total':3,'mode':MODE,'files':paths}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--date',required=True)
    args=parser.parse_args(argv)
    try:print(json.dumps(publish_editorial(args.root,json.loads(args.manifest.read_text()),args.date),ensure_ascii=False));return 0
    except (ValueError,OSError,KeyError,TypeError,subprocess.CalledProcessError) as error:print(str(error),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
