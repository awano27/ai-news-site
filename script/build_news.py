# scripts/build_news.py
import os, re, json, time, math, hashlib, html
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import requests
import feedparser
import tldextract
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
import trafilatura
import csv

JST = timezone(timedelta(hours=9))
FAST_MODE = os.getenv('NEWS_FAST_MODE') == '1'
try:
    GLOBAL_TIMEOUT_SEC = int(os.getenv('NEWS_GLOBAL_TIMEOUT_SEC', '60'))
except Exception:
    GLOBAL_TIMEOUT_SEC = 60
ROOT = os.path.dirname(os.path.dirname(__file__))
NEWS_DIR = os.path.join(ROOT, 'news')
SOURCES_YAML = os.path.join(ROOT, 'sources.yaml')

# --- utils -------------------------------------------------

def log(*a):
    print('[build]', *a, flush=True)

def canon_url(u: str) -> str:
    try:
        p = urlparse(u)
        # パラメータのutm等を削除
        q = [(k,v) for k,v in parse_qsl(p.query) if not k.lower().startswith('utm_')]
        # 末尾スラッシュと #frag を除去
        p = p._replace(query=urlencode(q), fragment='')
        s = urlunparse(p)
        if s.endswith('/'):
            s = s[:-1]
        return s
    except Exception:
        return u

SIM_THRESHOLD = 0.95  # 類似判定を厳しめにして間引き過多を抑制

from difflib import SequenceMatcher

def very_similar(a,b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= SIM_THRESHOLD

UA = {
    'User-Agent': 'Mozilla/5.0 (NewsBot; +https://github.com)'
}

# --- sources ----------------------------------------------

def load_sources():
    import yaml
    with open(SOURCES_YAML, 'r', encoding='utf-8') as f:
        y = yaml.safe_load(f)
    return (
        y.get('feeds', []),
        y.get('x_accounts', []),
        y.get('x_rss_base'),
        y.get('x_rss_accounts', []),
        y.get('sheets', [])
    )

# --- fetch -------------------------------------------------

def head_ok(url: str) -> bool:
    try:
        # 一部SNS/大手はHEAD拒否が多い→許可ドメインは常にTrue
        host = urlparse(url).netloc.lower()
        allow_hosts = ['x.com', 'twitter.com', 'nitter.net']
        if any(h == host or host.endswith('.'+h) for h in allow_hosts):
            return True
        if FAST_MODE:
            return True
        r = requests.head(url, headers=UA, timeout=8, allow_redirects=True)
        if r.status_code >= 400:
            # 一部サイトはHEAD拒否 → GETで再確認
            r = requests.get(url, headers=UA, timeout=10, allow_redirects=True)
        return 200 <= r.status_code < 400
    except Exception:
        return False


def fetch_feed(url: str):
    log('feed:', url)
    d = None
    try:
        if FAST_MODE:
            rr = requests.get(url, headers=UA, timeout=8)
            rr.raise_for_status()
            d = feedparser.parse(rr.text)
        else:
            rr = requests.get(url, headers=UA, timeout=15)
            rr.raise_for_status()
            d = feedparser.parse(rr.text)
    except Exception:
        # フォールバック: feedparserにURLを直接渡す（内部で取得）
        try:
            d = feedparser.parse(url)
        except Exception:
            d = {'entries': []}
    if not d:
        d = {'entries': []}
    items = []
    for e in d.entries:
        title = e.get('title', '').strip()
        link = e.get('link') or e.get('id')
        if not title or not link:
            continue
        link = canon_url(link)
        # pubdate
        dt = None
        for key in ['published', 'updated', 'created']:
            if e.get(key):
                try:
                    dt = dateparser.parse(e.get(key))
                    break
                except Exception:
                    pass
        if not dt:
            dt = datetime.now(timezone.utc)
        # summary
        summary = BeautifulSoup(e.get('summary', ''), 'html.parser').get_text(' ', strip=True)
        items.append({
            'title': title,
            'url': link,
            'summary': summary,
            'published': dt.astimezone(JST).isoformat(),
            'source_name': tldextract.extract(link).registered_domain or urlparse(link).netloc,
        })
    return items


def fetch_x_api(usernames):
    token = os.getenv('X_BEARER_TOKEN')
    if not token or not usernames:
        return []
    log('x api: users', usernames)
    headers = {
        'Authorization': f'Bearer {token}',
        'User-Agent': UA['User-Agent']
    }
    out = []
    for name in usernames:
        try:
            u = requests.get(f'https://api.x.com/2/users/by/username/{name}', headers=headers, timeout=10).json()
            uid = u.get('data',{}).get('id')
            display = u.get('data',{}).get('name')
            if not uid:
                continue
            t = requests.get(
                f'https://api.x.com/2/users/{uid}/tweets',
                params={'max_results': 10, 'tweet.fields': 'created_at'},
                headers=headers, timeout=10
            ).json()
            for tw in t.get('data', []):
                url = f'https://x.com/{name}/status/{tw.get("id")}'
                out.append({
                    'title': (tw.get('text') or '').split('\n')[0][:90],
                    'url': url,
                    'summary': tw.get('text') or '',
                    'published': dateparser.parse(tw.get('created_at')).astimezone(JST).isoformat(),
                    'source_name': 'x.com',
                    'author_handle': name,
                    'author_display': display
                })
        except Exception as ex:
            log('x api error', name, ex)
    return out


def fetch_x_rss(base, accounts):
    if not base or not accounts:
        return []
    out = []
    for name in accounts:
        url = f"{base.rstrip('/')}/{name}/rss"
        try:
            for e in fetch_feed(url):
                # NitterのリンクをX公式に正規化
                e['url'] = re.sub(r'^https?://[^/]+/([^/]+)/status/(\d+).*', r'https://x.com/\1/status/\2', e['url'])
                e['source_name'] = 'x.com'
                e['author_handle'] = name
                out.append(e)
        except Exception as ex:
            log('x rss error', name, ex)
    return out

# --- google sheets -----------------------------------------

def fetch_google_sheet_csv(sheet_id: str, gid: str|int = 0, timeout_sec: int = 20):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    log('sheet:', url)
    try:
        r = requests.get(url, headers=UA, timeout=timeout_sec)
        r.raise_for_status()
        r.encoding = 'utf-8'
        text = r.text
    except Exception as ex:
        log('sheet err', ex)
        return []

    rows = []
    for row in csv.reader(text.splitlines()):
        rows.append(row)
    return rows


def rows_to_items_from_sheet(rows, mapping=None):
    # mapping: dict with keys: date, handle, text, url. Values are column indices (0-based)
    # default assumes: A=date(0) B=handle(1) D=text(3) F=url(5)
    m = mapping or {'date': 0, 'handle': 1, 'text': 3, 'url': 5}
    out = []
    for r in rows:
        try:
            dt_raw = (r[m['date']] if len(r) > m['date'] else '').strip()
            handle = (r[m['handle']] if len(r) > m['handle'] else '').strip()
            text = (r[m['text']] if len(r) > m['text'] else '').strip()
            url = canon_url((r[m['url']] if len(r) > m['url'] else '').strip())
            if not text or not url:
                continue
            # parse date
            dt = None
            if dt_raw:
                try:
                    dt = dateparser.parse(dt_raw)
                except Exception:
                    dt = None
            if not dt:
                dt = datetime.now(timezone.utc)
            src_name = 'x.com' if 'x.com/' in url or 'twitter.com/' in url else tldextract.extract(url).registered_domain
            out.append({
                'title': text.split('\n')[0][:90],
                'url': url,
                'summary': text,
                'published': dt.astimezone(JST).isoformat(),
                'source_name': src_name or 'sheet',
                'author_handle': handle.lstrip() if handle else ''
            })
        except Exception:
            continue
    return out

# --- extraction -------------------------------------------

def extract_text(url: str) -> str:
    try:
        if FAST_MODE:
            return ''
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return ''
        txt = trafilatura.extract(downloaded, include_comments=False, include_images=False, include_tables=False) or ''
        return txt.strip()
    except Exception:
        return ''

# --- heuristics & scoring --------------------------------
KEYWORDS_ENGINEER = r"\b(API|SDK|CLI|ライブラリ|GitHub|オープンソース|weights|モデル|fine-tune|benchmark|データセット|リリース|v\d(?:\.\d)?)\b"
KEYWORDS_BIZ = r"\b(Copilot|Notion|Slack|Google\s?Workspace|Microsoft\s?365|Salesforce|HubSpot|自動化|ワークフロー|生産性|アシスタント)\b"
KEYWORDS_POLICY = r"\b(EU\s?AI\s?Act|規制|法案|大統領令|省令|罰金|当局|安全性評価|監査)\b"
BIG_NAMES = [
    'OpenAI','Anthropic','Google','DeepMind','Microsoft','Meta','NVIDIA','Amazon','Apple','xAI','Mistral','Hugging Face'
]


def classify(item):
    title = (item.get('title') or '')
    s = (item.get('summary') or '')
    text = f"{title} {s}"
    cat = []
    if re.search(KEYWORDS_ENGINEER, text, re.I):
        cat.append('tools')
    if re.search(KEYWORDS_BIZ, text, re.I):
        cat.append('business')
    if any(n.lower() in text.lower() for n in BIG_NAMES) or re.search(KEYWORDS_POLICY, text, re.I):
        cat.append('company')
    if 'x.com' in (item.get('source_name') or '') or 'twitter' in (item.get('source_name') or ''):
        cat.append('sns')
    if not cat:
        # デフォルトは company
        cat = ['company']
    return cat


def score(item):
    now = datetime.now(JST)
    try:
        dt = dateparser.parse(item.get('published')).astimezone(JST)
    except Exception:
        dt = now
    age_h = (now - dt).total_seconds()/3600
    # 情報量拡充のため新しさウィンドウを可変に（デフォルト96h）
    try:
        rec_hours = float(os.getenv('NEWS_RECENCY_WINDOW_HOURS', '96'))
    except Exception:
        rec_hours = 96.0
    recency = max(0.0, 1.0 - min(age_h/rec_hours, 1.0))

    t = (item.get('title') or '') + ' ' + (item.get('summary') or '')
    engineer = 1.0 if re.search(KEYWORDS_ENGINEER, t, re.I) else 0.0
    biz = 1.0 if re.search(KEYWORDS_BIZ, t, re.I) else 0.0
    policy = 1.0 if re.search(KEYWORDS_POLICY, t, re.I) else 0.0
    big = 1.0 if any(n.lower() in t.lower() for n in BIG_NAMES) else 0.0

    # サプライズ（脆弱性/大型発表/劇的比較などの単語）
    surprise = 1.0 if re.search(r"(突破|leak|爆|倍|破る|破竹|unprecedented|重大|障害|停止|重大脆弱性|過去最大)", t, re.I) else 0.0

    base = 0.4*recency + 0.25*surprise + 0.2*big + 0.1*engineer + 0.05*(biz or policy)
    # 星（1〜5）
    stars = 1 + int(round(base*4))
    return base, min(max(stars,1),5)

# --- LLM summarization (optional) -------------------------

def llm_summarize(title, text, url):
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        return None
    model = os.getenv('OPENAI_MODEL') or 'gpt-4o-mini'
    base = os.getenv('OPENAI_API_BASE') or 'https://api.openai.com/v1'
    try:
        prompt = f"""
以下の記事を日本語で80文字以内に要約し、カテゴリ（business/tools/company/snsのいずれか）と、重要度を1〜5で出してください。出力はJSONのみ。

タイトル: {title}
URL: {url}
本文: {text[:4000]}
"""
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': 'You are a concise Japanese news assistant.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.2
        }
        r = requests.post(f'{base}/chat/completions', headers={'Authorization': f'Bearer {key}'}, json=payload, timeout=45)
        r.raise_for_status()
        ans = r.json()['choices'][0]['message']['content']
        j = json.loads(ans)
        return {
            'blurb': j.get('summary') or j.get('要約') or j.get('blurb'),
            'category': j.get('category') or j.get('カテゴリ'),
            'stars': int(j.get('stars') or j.get('重要度') or 3)
        }
    except Exception as ex:
        log('llm fail', ex)
        return None

# --- main -------------------------------------------------

def main():
    os.makedirs(NEWS_DIR, exist_ok=True)
    feeds, x_users, x_rss_base, x_rss_users, sheets = load_sources()
    start_time = time.time()

    items = []
    only_sheets = os.getenv('NEWS_ONLY_SHEETS') == '1'
    if not only_sheets:
        for f in feeds:
            try:
                items.extend(fetch_feed(f))
            except Exception as ex:
                log('feed err', f, ex)
            if time.time() - start_time > GLOBAL_TIMEOUT_SEC:
                break

    # SNS
    if not only_sheets:
        if time.time() - start_time <= GLOBAL_TIMEOUT_SEC:
            items.extend(fetch_x_api(x_users))
        if time.time() - start_time <= GLOBAL_TIMEOUT_SEC:
            items.extend(fetch_x_rss(x_rss_base, x_rss_users))

    # Google Sheets
    for s in (sheets or []):
        try:
            sid = s.get('id')
            gid = s.get('gid', 0)
            mapping = s.get('mapping')
            rows = fetch_google_sheet_csv(sid, gid)
            items.extend(rows_to_items_from_sheet(rows, mapping))
        except Exception as ex:
            log('sheet fetch fail', ex)

    # dedup by URL & title
    uniq = []
    seen = set()
    for it in items:
        url = canon_url(it['url'])
        key = (url, it['title'].strip().lower())
        if key in seen:
            continue
        seen.add(key)
        uniq.append(it)
        if FAST_MODE and len(uniq) >= 120:
            break

    # title-similarity prune
    pruned = []
    if FAST_MODE:
        # 類似判定はスキップして速度優先
        pruned = uniq[:]
    else:
        for it in uniq:
            if any(very_similar(it['title'], p['title']) for p in pruned):
                continue
            pruned.append(it)
            if time.time() - start_time > GLOBAL_TIMEOUT_SEC:
                break

    # verify links quickly
    verified = pruned if FAST_MODE else [it for it in pruned if head_ok(it['url'])]

    # enrich with text, llm/fallback summary, score, category
    enriched = []
    for it in verified:
        body = extract_text(it['url'])
        llm = llm_summarize(it['title'], body or it['summary'], it['url'])
        cats = classify(it)
        base, stars = score(it)
        category = (llm and llm.get('category')) or cats[0]
        item_out = {
            'title': it['title'],
            'blurb': (llm and llm.get('blurb')) or (body[:120] + '…' if body else it['summary'][:120]),
            'category': category,
            'date': it['published'][:10],
            'stars': int((llm and llm.get('stars')) or stars),
            'source': {'name': it['source_name'], 'url': it['url']}
        }
        # SNS向けの明示的な著者情報
        if category == 'sns' or (it.get('source_name') == 'x.com'):
            handle = it.get('author_handle') or re.sub(r'^https?://x\.com/([^/]+)/.*', r'\1', it['url'])
            if handle and not handle.startswith('@'):
                handle = '@' + handle
            item_out['sns'] = {
                'handle': handle,
                'display_name': it.get('author_display') or '',
                'posted_at': it.get('published')
            }
            # 出典の表示名はハンドルに
            item_out['source'] = {'name': handle or 'X', 'url': it['url']}
            item_out['category'] = 'sns'
        enriched.append(item_out)
        if FAST_MODE and len(enriched) >= 80:
            break
        if time.time() - start_time > GLOBAL_TIMEOUT_SEC:
            break

    # score again using produced blurb/title
    for it in enriched:
        base, stars = score({'title': it['title'], 'summary': it['blurb'], 'published': it['date'], 'source_name': it['source']['name']})
        it['stars'] = max(it['stars'], stars)

    # age-based filter for freshness (default 24h, widen to 48h if empty)
    def hours_since(datestr: str) -> float:
        try:
            dt = dateparser.parse(datestr).astimezone(JST)
        except Exception:
            dt = datetime.now(JST)
        return max(0.0, (datetime.now(JST) - dt).total_seconds()/3600)

    try:
        max_age_h = float(os.getenv('NEWS_MAX_AGE_HOURS', '24'))
    except Exception:
        max_age_h = 24.0

    fresh = [it for it in enriched if hours_since(it['date']) <= max_age_h]
    if not fresh and enriched:
        # widen once to 48h if nothing fresh
        fresh = [it for it in enriched if hours_since(it['date']) <= 48.0]

    # split into sections and pick上位
    sections = {'business': [], 'tools': [], 'company': [], 'sns': []}
    for it in (fresh or enriched):
        sections.setdefault(it['category'], sections['company']).append(it)

    # 並べ替え（stars→新しさ）
    def sortkey(x):
        try:
            dt = dateparser.parse(x['date'])
        except Exception:
            dt = datetime.now(JST)
        return (-x['stars'], dt)

    try:
        max_per = int(os.getenv('NEWS_MAX_PER_SECTION', '30'))
    except Exception:
        max_per = 30
    for k in sections:
        sections[k] = sorted(sections[k], key=sortkey)[:max_per]

    # highlight = SNSを除く全体から最高スコア（鮮度フィルタ後）
    non_sns_items = [x for x in (fresh or enriched) if x.get('category') != 'sns']
    all_items = sorted(non_sns_items, key=lambda x: (-x['stars']))
    hl = all_items[0] if all_items else None
    highlight = None
    if hl:
        highlight = {
            'category': '重要トピック',
            'stars': hl['stars'],
            'title': hl['title'],
            'summary': hl['blurb'],
            'sources': [hl['source']]
        }

    out = {
        'generated_at': datetime.now(JST).isoformat(),
        'highlight': highlight,
        'sections': sections
    }

    today = datetime.now(JST).strftime('%Y-%m-%d')
    with open(os.path.join(NEWS_DIR, 'latest.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open(os.path.join(NEWS_DIR, f'{today}.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    log('DONE', len(enriched), 'items')

if __name__ == '__main__':
    main()