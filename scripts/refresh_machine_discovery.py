#!/usr/bin/env python3
"""Refresh public machine-readable discovery from retained, published editions.

Run during Pages packaging, after sync_daily_search and homepage generation.
Does not invent missing editions or enable analytics. Private config stays private.
"""
import argparse
import html
import json
import re
from pathlib import Path

EVIDENCE_KEYS = ('correction_note','integrity_status','integrity_warning','claim_evidence')

def evidence(item):
    return {k:item[k] for k in EVIDENCE_KEYS if k in item}

DATE = re.compile(r'^\d{4}-\d{2}-\d{2}\.json$')

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def refresh(root):
    root=Path(root)
    entries={}
    public=root/'public-pages/news'
    # Preserve the legacy selector's reviewed records, counts and precedence.
    # Legacy producers maintain these rows; nested daily editions only add dates.
    index=public/'archive_index.json'
    if index.exists():
        entries={e['date']:e for e in read(index) if not e.get('file','').startswith('daily/')}
    for p in sorted((public/'daily').glob('*.json')):
        if not DATE.fullmatch(p.name): continue
        data=read(p)
        if data.get('date')!=p.stem or not isinstance(data.get('items'),list):
            raise ValueError('Invalid retained edition: '+str(p))
        items=data['items'];sections={}
        for item in items:
            category=item.get('category','other')
            sections.setdefault(category,[]).append({'title':item.get('title',''),'blurb':item.get('summary',''), 'category':category,'date':p.stem,'source':{'name':item.get('source',''),'url':item.get('url','')},**evidence(item)})
        first=items[0] if items else {}
        destination=root/'news'/p.name
        existing=read(destination) if destination.exists() else {}
        if not existing or existing.get('source_url')=='https://visionhub.jp/public-pages/news/daily/'+p.name:
            write(destination,{'generated_at':p.stem,'news_date':p.stem,'source_url':'https://visionhub.jp/public-pages/news/daily/'+p.name,'highlight':{**evidence(first),'title':first.get('title',''),'summary':first.get('summary',''),'sources':[{'name':first.get('source',''),'url':first.get('url','')}] if first else []},'sections':sections})
        if p.stem not in entries:
            entries[p.stem]={'date':p.stem,'file':'daily/'+p.name,'count':len(items)}
    write(public/'archive_index.json',[entries[k] for k in sorted(entries,reverse=True)])
    slides=sorted((root/'presentations/day_slides').glob('day_slide_????_??_??.html'),reverse=True)
    if slides:
        p=slides[0];match=re.search(r'<title[^>]*>(.*?)</title>',p.read_text(encoding='utf-8'),re.S|re.I)
        title=html.unescape(match.group(1)) if match else p.stem
        llms=root/'llms.txt';text=llms.read_text(encoding='utf-8')
        text=re.sub(r"^- \[Today's day slide\].*$",lambda _:f"- [Today's day slide](https://visionhub.jp/presentations/day_slides/{p.name}): {title}",text,flags=re.M)
        llms.write_text(text,encoding='utf-8')
    cfg=read(root/'config/analytics.json');mid=str(cfg.get('measurement_id',''))
    valid=bool(re.fullmatch(r'G-[A-Z0-9]{6,}',mid)) and not re.search('REPLACE|XXXX',mid,re.I)
    write(root/'assets/analytics-config.json',{'measurement_id':mid if valid else None,'status':'configured' if valid else 'not_configured'})
    print('machine discovery:',len(entries),'editions; analytics:', 'configured' if valid else 'not configured (unchanged)')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);refresh(p.parse_args().root)
