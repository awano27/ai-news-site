"""
ソース管理システム v2.0
Tier制による情報源の階層的管理
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

import yaml
import feedparser
import requests
from bs4 import BeautifulSoup

from ..config.settings import settings
from ..models.schemas import SourceTier

logger = logging.getLogger(__name__)


class SourceManager:
    """情報源管理クラス"""
    
    def __init__(self):
        self.sources_config = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    async def collect_all_sources(self) -> List[Dict[str, Any]]:
        """全ソースから情報収集"""
        await self._load_sources_config()
        
        all_articles = []
        
        # Tier 1ソース（必須）
        logger.info("🔴 Collecting from Tier 1 sources")
        tier1_articles = await self._collect_tier1_sources()
        all_articles.extend(tier1_articles)
        
        # Tier 2ソース（重要）
        logger.info("🟡 Collecting from Tier 2 sources")
        tier2_articles = await self._collect_tier2_sources()
        all_articles.extend(tier2_articles)
        
        # X/Twitter投稿（CSVから）
        if settings.data_sources.x_posts_csv:
            logger.info("🐦 Collecting from X/Twitter CSV")
            x_articles = await self._collect_x_posts()
            all_articles.extend(x_articles)
        
        # GitHub Trending（技術系）
        logger.info("💻 Collecting from GitHub Trending")
        github_articles = await self._collect_github_trending()
        all_articles.extend(github_articles)
        
        # 重複除去
        unique_articles = self._deduplicate_articles(all_articles)
        
        logger.info(f"Collected {len(unique_articles)} unique articles from {len(all_articles)} total")
        
        return unique_articles
    
    async def _load_sources_config(self):
        """sources.yamlの読み込み"""
        try:
            with open(settings.sources_yaml, 'r', encoding='utf-8') as f:
                self.sources_config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load sources config: {e}")
            self.sources_config = {'feeds': [], 'x_accounts': []}
    
    async def _collect_tier1_sources(self) -> List[Dict[str, Any]]:
        """Tier 1ソースからの収集"""
        articles = []
        
        # 定義済みのTier 1ソース
        tier1_feeds = [
            'https://openai.com/blog/rss.xml',
            'https://www.anthropic.com/news/rss.xml',
            'https://deepmind.google/atom.xml',
            'https://ai.googleblog.com/atom.xml',
            'https://huggingface.co/blog/feed.xml',
            'https://export.arxiv.org/rss/cs.CL',
            'https://export.arxiv.org/rss/cs.LG',
            'https://export.arxiv.org/rss/stat.ML'
        ]
        
        # 設定ファイルからの追加
        if self.sources_config and 'feeds' in self.sources_config:
            tier1_feeds.extend(self.sources_config['feeds'][:10])  # 上位10件をTier 1扱い
        
        # 並列処理でフィード収集
        tasks = [self._fetch_feed(url, SourceTier.TIER_1) for url in tier1_feeds]
        feed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in feed_results:
            if isinstance(result, list):
                articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Tier 1 feed error: {result}")
        
        return articles
    
    async def _collect_tier2_sources(self) -> List[Dict[str, Any]]:
        """Tier 2ソースからの収集"""
        articles = []
        
        tier2_feeds = [
            'https://techcrunch.com/category/artificial-intelligence/feed/',
            'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml',
            'https://www.reuters.com/technology/artificial-intelligence/rss',
            'https://aws.amazon.com/blogs/machine-learning/feed/',
            'https://cloud.google.com/blog/topics/ai-ml/rss/',
            'https://blog.langchain.dev/rss/',
        ]
        
        # 設定ファイルからの追加
        if self.sources_config and 'feeds' in self.sources_config:
            tier2_feeds.extend(self.sources_config['feeds'][10:])  # 11件目以降をTier 2扱い
        
        # 重要度に基づくフィルタリング付きで収集
        tasks = [self._fetch_feed(url, SourceTier.TIER_2) for url in tier2_feeds]
        feed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in feed_results:
            if isinstance(result, list):
                # Tier 2は品質フィルタを適用
                filtered = self._filter_tier2_articles(result)
                articles.extend(filtered)
            elif isinstance(result, Exception):
                logger.error(f"Tier 2 feed error: {result}")
        
        return articles
    
    async def _fetch_feed(self, feed_url: str, tier: SourceTier) -> List[Dict[str, Any]]:
        """RSSフィードの取得と解析"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.session.get(feed_url, timeout=15)
            )
            response.raise_for_status()
            
            # feedparserでパース
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                logger.warning(f"No entries found in feed: {feed_url}")
                return []
            
            articles = []
            cutoff_date = datetime.now() - timedelta(hours=settings.temporal.max_age_hours)
            
            for entry in feed.entries[:20]:  # 最新20件まで
                try:
                    # 公開日の解析
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    
                    # 古い記事をスキップ
                    if pub_date and pub_date < cutoff_date:
                        continue
                    
                    # 記事情報を抽出
                    article = {
                        'title': entry.get('title', ''),
                        'url': entry.get('link', ''),
                        'source': self._extract_source_name(feed_url),
                        'source_tier': tier.value,
                        'published_date': pub_date or datetime.now(),
                        'summary': entry.get('summary', ''),
                        'tags': [tag.term for tag in entry.get('tags', [])]
                    }
                    
                    if article['url'] and article['title']:
                        articles.append(article)
                
                except Exception as e:
                    logger.warning(f"Error processing entry from {feed_url}: {e}")
                    continue
            
            logger.debug(f"Fetched {len(articles)} articles from {feed_url}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {e}")
            return []
    
    def _filter_tier2_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Tier 2記事の品質フィルタ"""
        filtered = []
        
        # AIキーワードによるフィルタ
        ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'deep learning',
            'neural network', 'transformer', 'gpt', 'llm', 'nlp', 'computer vision',
            'automation', 'algorithm', 'model', 'training', 'dataset', 'ml'
        ]
        
        for article in articles:
            title_lower = article['title'].lower()
            summary_lower = article.get('summary', '').lower()
            text = f"{title_lower} {summary_lower}"
            
            # AIキーワードチェック
            has_ai_content = any(keyword in text for keyword in ai_keywords)
            
            # 長さチェック（短すぎる記事を除外）
            has_sufficient_content = len(article['title']) >= 20
            
            if has_ai_content and has_sufficient_content:
                filtered.append(article)
        
        return filtered
    
    async def _collect_x_posts(self) -> List[Dict[str, Any]]:
        """X/Twitter投稿の収集（CSV形式）"""
        if not settings.data_sources.x_posts_csv:
            return []
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.session.get(settings.data_sources.x_posts_csv, timeout=10)
            )
            response.raise_for_status()
            
            # CSV解析（簡易版）
            lines = response.text.split('\n')
            if len(lines) < 2:
                return []
            
            articles = []
            cutoff_date = datetime.now() - timedelta(hours=settings.temporal.max_age_hours)
            
            for line in lines[1:]:  # ヘッダーをスキップ
                parts = line.strip().split(',')
                if len(parts) >= 4:
                    try:
                        date_str, handle, _, text = parts[:4]
                        url = parts[5] if len(parts) > 5 else f"https://twitter.com/{handle}"
                        
                        # 日付解析
                        pub_date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        # 古い投稿をスキップ
                        if pub_date < cutoff_date:
                            continue
                        
                        article = {
                            'title': text[:100] + '...' if len(text) > 100 else text,
                            'url': url,
                            'source': f"@{handle}",
                            'source_tier': SourceTier.TIER_2.value,
                            'published_date': pub_date,
                            'summary': text,
                            'category': 'sns'
                        }
                        
                        articles.append(article)
                    
                    except Exception as e:
                        logger.warning(f"Error parsing X post line: {line[:50]}... - {e}")
                        continue
            
            logger.info(f"Collected {len(articles)} X/Twitter posts")
            return articles
            
        except Exception as e:
            logger.error(f"Error collecting X posts: {e}")
            return []
    
    async def _collect_github_trending(self) -> List[Dict[str, Any]]:
        """GitHub Trendingからの収集"""
        if not settings.api.github_token:
            logger.info("GitHub token not available, skipping trending collection")
            return []
        
        try:
            # GitHub Search API
            headers = {'Authorization': f'token {settings.api.github_token}'}
            
            # AI/ML関連のトレンドリポジトリを検索
            queries = [
                'language:python topic:machine-learning',
                'language:python topic:artificial-intelligence',
                'language:python topic:deep-learning',
                'topic:llm OR topic:transformer'
            ]
            
            articles = []
            
            for query in queries:
                url = f"https://api.github.com/search/repositories"
                params = {
                    'q': f"{query} created:>={datetime.now().strftime('%Y-%m-%d')}",
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 10
                }
                
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.session.get(url, headers=headers, params=params, timeout=10)
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for repo in data.get('items', []):
                        article = {
                            'title': f"{repo['name']}: {repo.get('description', '')}",
                            'url': repo['html_url'],
                            'source': 'GitHub',
                            'source_tier': SourceTier.TIER_2.value,
                            'published_date': datetime.fromisoformat(repo['created_at'].replace('Z', '+00:00')),
                            'summary': repo.get('description', ''),
                            'category': 'tools',
                            'github_stars': repo.get('stargazers_count', 0)
                        }
                        
                        articles.append(article)
            
            logger.info(f"Collected {len(articles)} GitHub trending repositories")
            return articles
            
        except Exception as e:
            logger.error(f"Error collecting GitHub trending: {e}")
            return []
    
    def _extract_source_name(self, url: str) -> str:
        """URLからソース名を抽出"""
        try:
            domain = urlparse(url).netloc
            parts = domain.split('.')
            if len(parts) >= 2:
                return parts[-2].title()  # example.com -> Example
            return domain
        except:
            return "Unknown"
    
    def _deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """記事の重複除去"""
        seen_urls = set()
        unique_articles = []
        
        for article in articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        return unique_articles